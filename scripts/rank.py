#!/usr/bin/env python3
"""Merge every sweep's candidates, score them, and write the daily queue.

    python3 scripts/rank.py            # writes state/queue_ranked.csv and state/queue_ranked.md
    python3 scripts/rank.py --selftest

Score (0-100) = 60% fit + 30% timing + 10% company.
  fit     : % of the posting's design skills your master CV covers, weighted by role type (intern first),
            minus a penalty when the posting asks for more years than you have.
  timing  : fresh postings first (applicants in the first 72h get read), plus internship season and deadlines.
  company : visa/relocation signals, global-remote hiring, priority companies.
Only postings with fit >= targets.min_fit_percent (default 60) enter the queue.
Your skills come from targets.my_skills in config/settings.json, which must only hold things the master CV proves.
"""
import csv, datetime, json, os, re, sys

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R, 'scripts'))
import design_targets as DT

UTC = datetime.timezone.utc
SW = os.path.join(R, 'state', 'sweep')

# Design-skill vocabulary used to read what a posting asks for. Lower case; regex allowed.
VOCAB = {
    'figma': r'figma', 'prototyping': r'prototyp', 'wireframing': r'wirefram', 'user research': r'user research|ux research',
    'usability testing': r'usability test|user test', 'user interviews': r'user interview|customer interview',
    'interaction design': r'interaction design', 'visual design': r'visual design', 'design systems': r'design system',
    'component library': r'component librar|components', 'design tokens': r'design token', 'accessibility': r'accessib|wcag|a11y',
    'information architecture': r'information architecture', 'user flows': r'user flow|journey', 'personas': r'persona',
    'a/b testing': r'a/b test|experiment', 'analytics': r'analytics|ga4|mixpanel|amplitude|hotjar|heatmap',
    'html/css': r'\bhtml\b|\bcss\b', 'javascript': r'javascript|\bjs\b', 'react': r'\breact\b', 'front-end': r'front.?end',
    'framer': r'framer', 'webflow': r'webflow', 'motion': r'motion|animation|micro.?interaction|rive|after effects|lottie',
    'ux writing': r'ux writing|content design|microcopy', 'branding': r'brand', 'typography': r'typograph',
    'mobile': r'mobile|ios|android', 'responsive web': r'responsive|web app', 'developer handoff': r'hand.?off|dev mode',
    'agile': r'agile|scrum|sprint', 'cross-functional': r'cross.?functional|engineers and product|pm and eng',
    'product thinking': r'product thinking|product strategy|business goals', 'data-informed': r'data.?(?:driven|informed)|metrics',
    'ai tools': r'\bai\b|cursor|claude|v0|figma make|vibe.?cod', 'sql': r'\bsql\b', 'storybook': r'storybook',
    'sketch': r'\bsketch\b', 'adobe': r'adobe|photoshop|illustrator|\bxd\b', 'protopie': r'protopie|principle',
    'service design': r'service design|journey map', 'design critique': r'critique|feedback session', 'workshops': r'workshop|facilitat',
    'fintech': r'fintech|payments|banking|financial', 'logistics': r'logistics|shipping|supply chain', 'b2b saas': r'b2b|saas|enterprise',
    'e-commerce': r'e-?commerce|checkout', 'dashboards': r'dashboard|data visuali',
}
VOCAB_RE = {k: re.compile(v, re.I) for k, v in VOCAB.items()}
YEARS = re.compile(r'(?<!\d)(\d{1,2})\s*\+?\s*(?:-|to)?\s*\d{0,2}\s*\+?\s*years?[^.]{0,50}?(?:experience|exp\.)', re.I)
VISA = re.compile(r'visa sponsorship (?:is )?(?:available|provided)|we (?:can |will )?sponsor|relocation (?:support|package|assistance)|we hire (?:globally|anywhere)|deel|remote\.com|oyster', re.I)
DEADLINE = re.compile(r'(?:deadline|apply by|closing date|applications close)[^.\d]{0,20}(\d{1,2} \w+ \d{4}|\w+ \d{1,2},? \d{4}|\d{4}-\d{2}-\d{2})', re.I)

def load_settings():
    try: return json.load(open(os.path.join(R, 'config', 'settings.json')))
    except Exception: return {'targets': {}}

def read(name):
    p = os.path.join(SW, name)
    try: return json.load(open(p))
    except Exception: return []

def norm_all():
    rows = []
    for o in read('cands.json'):          # delta_sweep: [ats, slug, iso, title, loc, comp, url, desc]
        rows.append(dict(source=o[0], company=o[1], title=o[3], location=o[4], posted=o[2], url=o[6], desc=o[7] if len(o) > 7 else '', pay=o[5]))
    for o in read('list_cands.json'):     # list_sweep: [label, company, date, title, locs, terms, band, url]
        rows.append(dict(source=o[0], company=o[1], title=o[3], location=o[4], posted=o[2], url=o[7], desc='', pay=o[6]))
    for o in read('linkedin_cands.json'): # linkedin_sweep dicts
        rows.append(dict(source='linkedin/' + o.get('apply', ''), company=o.get('company', ''), title=o.get('title', ''), location=o.get('location', ''),
                         posted=o.get('posted', ''), url=o.get('url', ''), desc='', pay=o.get('pay', ''), years=o.get('years')))
    rows += read('remote_cands.json')
    return rows

def parse_date(s):
    for f in ('%Y-%m-%dT%H:%M', '%Y-%m-%d'):
        try: return datetime.datetime.strptime((s or '')[:len('2026-01-01T00:00') if 'T' in (s or '') else 10], f).replace(tzinfo=UTC)
        except Exception: pass
    return None

def score(r, mine, priority, now, min_fit):
    title, desc = r.get('title', ''), r.get('desc', '') or ''
    kind = r.get('kind') or DT.loc_kind(r.get('location', ''), desc)
    if not DT.title_ok(title) or not kind: return None
    tier = DT.title_tier(title)
    asked = [k for k, rx in VOCAB_RE.items() if rx.search(desc)]
    covered = [k for k in asked if k in mine]
    coverage = len(covered) / len(asked) if asked else 0.55  # no description: unverified, rank below postings we could read
    tier_w = {'intern': 1.0, 'junior': 0.95, 'core': 0.85, 'adjacent': 0.7}[tier]
    yrs = r.get('years')
    if yrs in (None, '?', ''):
        m = YEARS.search(desc); yrs = int(m.group(1)) if m else None
    penalty = 0 if yrs is None or yrs <= 1 else 10 if yrs == 2 else 25 if yrs == 3 else 45
    fit = max(0, round(100 * (0.4 * tier_w + 0.6 * coverage)) - penalty)
    if fit < min_fit: return None
    posted = parse_date(r.get('posted'))
    age = (now - posted).days if posted else 10
    timing = 30 if age <= 2 else 24 if age <= 4 else 16 if age <= 7 else 8 if age <= 14 else 2
    if tier == 'intern' and now.month in (9, 10, 11, 12, 1, 2): timing = min(30, timing + 5)
    if DEADLINE.search(desc): timing = min(30, timing + 4)
    comp = {'remote-global': 6, 'nigeria': 5, 'remote-region': 4, 'relocate': 3}[kind]
    if VISA.search(desc): comp += 4
    if any(p and p in (r.get('company', '') or '').lower() for p in priority): comp += 4
    comp = min(10, comp)
    total = round(0.6 * fit + timing + comp)
    flags = []
    if kind == 'relocate' and not VISA.search(desc): flags.append('check visa sponsorship')
    if kind == 'remote-region' and not re.search(r'emea|europe|africa|nigeria|worldwide|anywhere', r.get('location', '') + desc[:3000], re.I): flags.append('check remote eligibility')
    if 'easy-apply' in r.get('source', ''): flags.append('Easy Apply only: find company site')
    if yrs and yrs >= 2: flags.append(f'asks {yrs}+ yrs')
    return dict(score=total, fit=fit, tier=tier, kind=kind, age=age, company=r.get('company', ''), title=title,
                location=r.get('location', ''), posted=(r.get('posted') or '')[:10], source=r.get('source', ''), url=r.get('url', ''),
                matched=', '.join(covered), gaps=', '.join(k for k in asked if k not in mine), pay=r.get('pay', ''), flags='; '.join(flags))

def main():
    if '--selftest' in sys.argv: return selftest()
    S = load_settings(); T = S.get('targets', {})
    mine = set(T.get('my_skills', []))
    priority = [c.lower() for c in T.get('priority_companies', [])]
    skip = [c.lower() for c in T.get('skip_companies', [])]
    applied = set()
    ap = os.path.join(R, 'state', 'applied_companies.txt')
    if os.path.exists(ap): applied = {l.strip().lower() for l in open(ap) if l.strip()}
    now = datetime.datetime.now(UTC)
    out, seen = [], set()
    for r in norm_all():
        co = (r.get('company') or '').lower()
        if any(s in co for s in skip): continue
        k = (co, (r.get('title') or '').lower())
        if k in seen: continue
        seen.add(k)
        s = score(r, mine, priority, now, T.get('min_fit_percent', 60))
        if s:
            if co in applied: s['flags'] = (s['flags'] + '; ' if s['flags'] else '') + 'already applied here'
            out.append(s)
    out.sort(key=lambda s: -s['score'])
    cols = ['score', 'fit', 'tier', 'company', 'title', 'kind', 'location', 'posted', 'age', 'source', 'url', 'matched', 'gaps', 'pay', 'flags']
    with open(os.path.join(R, 'state', 'queue_ranked.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, restval=''); w.writeheader(); w.writerows(out)
    with open(os.path.join(R, 'state', 'queue_ranked.md'), 'w') as f:
        f.write(f'# Ranked queue {now.isoformat()[:10]}  ({len(out)} postings at fit >= {T.get("min_fit_percent", 60)}%)\n\n')
        for i, s in enumerate(out, 1):
            f.write(f"{i}. **{s['score']}** fit {s['fit']}% · {s['tier']} · {s['company']} · {s['title']} · {s['kind']} · {s['age']}d · {s['url']}"
                    + (f"  _{s['flags']}_" if s['flags'] else '') + '\n')
    print(f'ranked {len(out)} postings -> state/queue_ranked.csv')
    for s in out[:25]: print(f"{s['score']:>3} {s['fit']:>3}% {s['tier']:<8} {s['company'][:24]:<24} {s['title'][:50]:<50} {s['kind']:<13} {s['age']}d")

def selftest():
    now = datetime.datetime(2026, 11, 18, tzinfo=UTC)
    mine = {'figma', 'prototyping', 'design systems', 'user research', 'usability testing', 'html/css', 'a/b testing'}
    a = score(dict(title='Product Design Intern', location='Remote - Worldwide', posted='2026-11-17',
                   desc='Figma, prototyping, design systems, user research. Visa sponsorship available.'), mine, [], now, 65)
    b = score(dict(title='Product Designer', location='Remote - Worldwide', posted='2026-10-01',
                   desc='5+ years of experience. Figma, Storybook, Sketch, service design.'), mine, [], now, 0)
    c = score(dict(title='Product Designer', location='Remote - US only', posted='2026-11-17', desc='Figma'), mine, [], now, 0)
    assert a and a['fit'] == 100 and a['score'] > 80, a
    assert b and b['score'] < a['score'] and 'asks 5+ yrs' in b['flags'], b
    assert c is None
    print('rank selftest ok')

if __name__ == '__main__': main()
