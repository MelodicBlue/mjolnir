#!/usr/bin/env python3
"""Remote job boards with public feeds, filtered for design roles a Lagos-based candidate can take.

    python3 scripts/remote_sweep.py              # postings newer than state/last_remote_sweep.txt (default 72h)
    python3 scripts/remote_sweep.py --hours 168  # fixed window, does not advance the cutoff

Sources (all public, no login):
  Himalayas      https://himalayas.app/jobs/api            (locationRestrictions, timezoneRestrictions)
  Remote OK      https://remoteok.com/api                  (terms: keep the Remote OK link and credit them; we only store their URL)
  We Work Remotely  https://weworkremotely.com/categories/remote-design-jobs.rss
  Remotive       https://remotive.com/api/remote-jobs?category=design

These are SOURCES. Apply on the company's own site whenever the posting links to one.
Output: state/sweep/remote_cands.json  (list of dicts: source, company, title, location, kind, posted, url, desc, pay)
"""
import datetime, html, json, os, re, sys, time, urllib.request
import xml.etree.ElementTree as ET

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R, 'scripts'))
import design_targets as DT

UTC = datetime.timezone.utc
CUT_FILE = os.path.join(R, 'state', 'last_remote_sweep.txt')
OUT = os.path.join(R, 'state', 'sweep', 'remote_cands.json')
UA = {'User-Agent': 'Mozilla/5.0 (job-search personal use; contact udedave06@gmail.com)'}

def get(url, timeout=30):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read().decode('utf-8', 'replace')

def text_of(h):
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', h or ''))).strip()

def keep(rows, source, company, title, loc, posted, url, desc, pay=''):
    if not DT.title_ok(title): return
    kind = DT.loc_kind(loc, desc)
    if not kind: return
    rows.append(dict(source=source, company=company, title=title, location=loc[:120], kind=kind,
                     posted=posted.isoformat()[:16], url=url, desc=desc[:6000], pay=pay))

def himalayas(since, rows):
    offset = 0
    for _ in range(60):  # up to ~1,200 newest postings
        d = json.loads(get(f'https://himalayas.app/jobs/api?limit=20&offset={offset}'))
        jobs = d.get('jobs') or []
        if not jobs: break
        older = 0
        for j in jobs:
            posted = datetime.datetime.fromtimestamp(int(j.get('pubDate') or 0), UTC)
            if posted < since: older += 1; continue
            locs = j.get('locationRestrictions') or []
            # A country list is a hiring restriction: keep it only if Nigeria or Africa/EMEA is on it.
            if locs and not any(re.search(r'nigeria|africa|emea|worldwide|anywhere', str(l), re.I) for l in locs): continue
            loc = 'Remote - ' + (', '.join(locs) if locs else 'Worldwide')
            if j.get('timezoneRestrictions'): loc += ' | UTC ' + ','.join(str(x) for x in j['timezoneRestrictions'][:6])
            pay = f"{j.get('minSalary') or ''}-{j.get('maxSalary') or ''} {j.get('currency') or ''}/{j.get('salaryPeriod') or ''}" if j.get('minSalary') else ''
            keep(rows, 'himalayas', j.get('companyName', ''), j.get('title', ''), loc, posted,
                 j.get('applicationLink', ''), text_of(j.get('description') or j.get('excerpt')), pay)
        if older == len(jobs): break  # whole page older than the window
        offset += 20; time.sleep(1)

def remoteok(since, rows):
    data = json.loads(get('https://remoteok.com/api'))
    for j in data[1:]:
        posted = datetime.datetime.fromtimestamp(int(j.get('epoch') or 0), UTC)
        if posted < since: continue
        loc = 'Remote' + (' - ' + j['location'] if j.get('location') else '')
        pay = f"{j.get('salary_min')}-{j.get('salary_max')} USD/yr" if j.get('salary_min') else ''
        keep(rows, 'remoteok', j.get('company', ''), j.get('position', ''), loc, posted, j.get('url', ''), text_of(j.get('description')), pay)

def wwr(since, rows):
    root = ET.fromstring(get('https://weworkremotely.com/categories/remote-design-jobs.rss'))
    for it in root.iter('item'):
        g = lambda t: (it.findtext(t) or '').strip()
        posted = datetime.datetime.strptime(g('pubDate'), '%a, %d %b %Y %H:%M:%S %z')
        if posted < since: continue
        company, _, title = g('title').partition(': ')
        loc = 'Remote - ' + (g('region') or 'Anywhere in the World') + (' ' + g('country') if g('country') else '')
        keep(rows, 'weworkremotely', company, title or company, loc, posted, g('link'), text_of(g('description')))

def remotive(since, rows):
    d = json.loads(get('https://remotive.com/api/remote-jobs?category=design'))
    for j in d.get('jobs', []):
        posted = datetime.datetime.fromisoformat(j['publication_date']).replace(tzinfo=UTC)
        if posted < since: continue
        loc = 'Remote - ' + (j.get('candidate_required_location') or 'Worldwide')
        keep(rows, 'remotive', j.get('company_name', ''), j.get('title', ''), loc, posted, j.get('url', ''), text_of(j.get('description')), j.get('salary') or '')

def main():
    args = sys.argv[1:]
    now = datetime.datetime.now(UTC)
    if '--hours' in args:
        since, advance = now - datetime.timedelta(hours=float(args[args.index('--hours') + 1])), False
    elif os.path.exists(CUT_FILE):
        since, advance = datetime.datetime.fromisoformat(open(CUT_FILE).read().strip()), True
    else:
        since, advance = now - datetime.timedelta(hours=72), True
    rows, ok = [], True
    for name, fn in (('himalayas', himalayas), ('remoteok', remoteok), ('weworkremotely', wwr), ('remotive', remotive)):
        n = len(rows)
        try: fn(since, rows)
        except Exception as e: print(f'{name}: error {e}'); ok = False
        print(f'{name}: {len(rows) - n} matching postings')
    seen, uniq = set(), []
    for r in rows:
        k = (r['company'].lower().strip(), r['title'].lower().strip())
        if k in seen: continue
        seen.add(k); uniq.append(r)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(uniq, open(OUT, 'w'), indent=1)
    if advance and ok: open(CUT_FILE, 'w').write(now.isoformat())
    print(f'remote sweep: {len(uniq)} candidates since {since.isoformat()[:16]}')
    for r in uniq: print('\t'.join([r['source'], r['company'], r['title'], r['kind'], r['posted'][:10], r['url']]))

if __name__ == '__main__': main()
