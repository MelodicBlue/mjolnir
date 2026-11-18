#!/usr/bin/env python3
"""Shared title and location rules for a Nigeria-based product/UX design candidate.

Every sweep imports this module so the rules live in one place:
  title_ok(title)            -> True for product/UX/UI design roles at intern, junior or mid level
  title_tier(title)          -> 'intern' | 'junior' | 'core' | 'adjacent'  (used by rank.py)
  loc_ok(location, text='')  -> True when a candidate in Lagos could actually take the job
  loc_kind(location, text='')-> 'remote-global' | 'remote-region' | 'nigeria' | 'relocate' | None

Run `python3 scripts/design_targets.py --selftest` after any edit.
"""
import re, sys

# ---------------------------------------------------------------- titles
DESIGN = re.compile(
    r'product design|ux|ui\b|ui/|user experience|user interface|interaction design|experience design'
    r'|product designer|digital designer|web designer|design engineer|design technologist'
    r'|visual designer|brand designer|design intern|designer intern|design internship|design (?:apprentice|trainee)', re.I)
# Senior and management roles, and design jobs that are not digital product work.
TOO_SENIOR = re.compile(r'senior|\bsr\b\.?|staff|principal|\blead\b|manager|director|head of|\bvp\b|\bchief\b|\biii\b|\biv\b', re.I)
NOT_PRODUCT = re.compile(
    r'industrial design|mechanical|hardware|interior|fashion|apparel|textile|furniture|packaging|print|instructional'
    r'|game designer|level designer|narrative|sound designer|landscape|architectur|civil|electrical|circuit|pcb|asic'
    r'|cad\b|drafter|recruit|sales|account exec|researcher only', re.I)
INTERN = re.compile(r'intern\b|internship|placement|working student|trainee|apprentice|co-?op\b|siwes|industrial training', re.I)
JUNIOR = re.compile(r'junior|\bjr\b|associate|entry.?level|graduate|new grad|early career|\bi\b$|\b1\b$', re.I)
ADJACENT = re.compile(r'visual designer|brand designer|web designer|digital designer|design engineer|design technologist', re.I)

def title_ok(t):
    t = t or ''
    return bool(DESIGN.search(t)) and not TOO_SENIOR.search(t) and not NOT_PRODUCT.search(t)

def title_tier(t):
    t = t or ''
    if INTERN.search(t): return 'intern'
    if JUNIOR.search(t): return 'junior'
    if ADJACENT.search(t): return 'adjacent'
    return 'core'

# ---------------------------------------------------------------- locations
REMOTE = re.compile(r'remote|anywhere|distributed|work from home|wfh|telecommut', re.I)
GLOBAL = re.compile(r'worldwide|anywhere|global|any location|all locations|international|no location restriction', re.I)
REGION = re.compile(r'emea|europe|\beu\b|africa|nigeria|lagos|\bwat\b|\bcet\b|\bgmt\b|utc ?[+-]? ?[0-3]\b|gmt ?[+-] ?[0-3]\b'
                    r'|middle east|time ?zones? (?:overlap|within)', re.I)
NIGERIA = re.compile(r'nigeria|lagos|abuja|port harcourt|ibadan', re.I)
# Countries where internships commonly come with visa support, matching the Visa routes tab of the sheet.
RELOCATE = re.compile(r'united kingdom|\buk\b|london|manchester|edinburgh|ireland|dublin|netherlands|amsterdam|rotterdam|eindhoven'
                      r'|germany|berlin|munich|hamburg|portugal|lisbon|porto|spain|madrid|barcelona|poland|krak[oó]w|warsaw'
                      r'|france|paris|italy|milan|sweden|stockholm|denmark|copenhagen|finland|helsinki|estonia|tallinn'
                      r'|switzerland|zurich|belgium|brussels|austria|vienna|czech|prague|luxembourg|united arab emirates|uae|dubai|abu dhabi', re.I)
# Remote roles fenced to one country or region we are not in.
FENCED = re.compile(r'(?:remote|us|usa|u\.s\.)[^a-z]{0,6}(?:only|based)|(?:must|need to|required to) (?:be )?(?:located|based|reside|live)'
                    r'|united states|\busa?\b|\bu\.s\.|canada|latam|latin america|brazil|mexico|india|apac|australia|new zealand'
                    r'|philippines|(?-i:\b(?:AL|AK|AZ|AR|CA|CO|CT|DE|DC|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\b)', re.I)
FENCE_PHRASE = re.compile(r'(?:authori[sz]ed|eligible|legally able|right) to work in (?:the )?(?:us|united states|uk|united kingdom|canada|eu|european union)'
                          r'|(?:not|unable to|cannot|can\'t|won\'t|do not|does not) (?:offer |provide )?(?:visa )?sponsor'
                          r'|without (?:the need for )?(?:visa )?sponsorship|no visa sponsorship', re.I)

def loc_kind(loc, text=''):
    loc, text = loc or '', text or ''
    both = loc + ' | ' + text[:4000]
    if NIGERIA.search(loc): return 'nigeria'
    if REMOTE.search(loc) or (not loc.strip() and REMOTE.search(text[:1500])):
        if GLOBAL.search(both) and not FENCED.search(loc): return 'remote-global'
        if REGION.search(loc) or (REGION.search(text[:4000]) and not FENCED.search(loc)): return 'remote-region'
        if FENCED.search(loc): return None
        # Bare "Remote" with nothing else: keep it, rank.py marks it "check eligibility".
        return 'remote-region' if not FENCE_PHRASE.search(text) else None
    if RELOCATE.search(loc):
        return None if FENCE_PHRASE.search(text) else 'relocate'
    return None

def loc_ok(loc, text=''):
    return loc_kind(loc, text) is not None

class _LocMatcher:
    """Drop-in for the old compiled LOC regex: LOC.search(location) -> truthy when we can take the job."""
    def search(self, s): return loc_ok(s)
LOC = _LocMatcher()

def selftest():
    for t in ('Product Designer', 'Product Design Intern', 'UI/UX Designer', 'UX Design Intern, Summer 2027', 'Associate Product Designer',
              'Junior UI Designer', 'Product Designer (Internship)', 'Design Engineer', 'UX/UI Designer - Remote', 'Interaction Designer'):
        assert title_ok(t), t
    for t in ('Senior Product Designer', 'Lead UX Designer', 'Industrial Design Intern', 'Software Engineer', 'Staff Product Designer',
              'Design Manager', 'Fashion Designer', 'Instructional Designer', 'Mechanical Design Engineer', 'Game Designer'):
        assert not title_ok(t), t
    assert title_tier('Product Design Intern') == 'intern' and title_tier('Junior Product Designer') == 'junior'
    assert title_tier('Product Designer') == 'core' and title_tier('Visual Designer') == 'adjacent'
    assert loc_kind('Remote - Worldwide') == 'remote-global'
    assert loc_kind('Remote (EMEA)') == 'remote-region'
    assert loc_kind('Lagos, Nigeria') == 'nigeria'
    assert loc_kind('Remote - US') is None
    assert loc_kind('Remote, United States') is None
    assert loc_kind('San Francisco, CA') is None
    assert loc_kind('London, UK') == 'relocate'
    assert loc_kind('London, UK', 'You must have the right to work in the UK. We do not offer visa sponsorship.') is None
    assert loc_kind('Remote', 'We hire anywhere in the world.') == 'remote-global'
    assert loc_kind('Remote', 'Candidates must be authorized to work in the US.') is None
    assert loc_kind('Krakow, Poland | Lisbon') == 'relocate'
    assert LOC.search('Remote - Europe') and not LOC.search('New York, NY')
    print('design_targets selftest ok')

if __name__ == '__main__' and '--selftest' in sys.argv: selftest()
