"""Step 4 — headline tables from results.jsonl."""
import json, collections
from common import norm_name, stem_name
R = [json.loads(l) for l in open('results.jsonl')]
def pct(a, b): return f"{a:,} ({100*a/b:.1f}%)" if b else '0'
out = {}
for h in ['Unknown', 'Partial', 'Known', 'ALL']:
    rs = [r for r in R if h == 'ALL' or r['hierarchy'] == h]
    n = len(rs); c = collections.Counter(r['outcome'] for r in rs)
    rg = [r for r in rs if r['outcome'] == 'reaches_group']
    head = [r for r in rg if r.get('reaches_head')]
    hd = collections.Counter(min(x['depth'] for x in r['own_hits'] if x['is_head']) for r in head)
    live = collections.Counter(bool(r['ch_status']) for r in rg)
    print(f"\n== {h}: {n:,} rows")
    for k, v in c.most_common(): print(f"  {k:22s} {pct(v, n)}")
    print(f"  reaches head (of reaches_group): {pct(len(head), len(rg))}; head depth {sorted(hd.items())}")
    print(f"  reaches_group live/dissolved now: {dict(live)}")
    print(f"  best method: {dict(collections.Counter(r['best_method'] for r in rg))}")
# Known rows: does the PSC immediate corporate parent agree with MEIP 'Parent of Subsidiary'?
agree = collections.Counter()
for r in R:
    if r['hierarchy'] != 'Known' or not r.get('meip_parent') or not r.get('chain'): continue
    firsts = [s for s in r['chain'] if s['depth'] == 1 and s['kind'] in 'cl']
    if not firsts: agree['no corporate PSC'] += 1; continue
    mp = r['meip_parent']
    if any(norm_name(s['name']) == norm_name(mp) for s in firsts): agree['strict name agrees'] += 1
    elif any(stem_name(s['name']) == stem_name(mp) for s in firsts): agree['loose name agrees'] += 1
    else: agree['differs'] += 1
print('\nKnown rows, MEIP Parent of Subsidiary vs PSC immediate corporate parent:', dict(agree))

# no_psc_live split by whether the entity type is inside the UK PSC regime.
# Out of scope: English/Welsh/NI limited partnerships (prefix LP/NL — Scottish LPs, SL, are in scope since 2017),
# overseas companies' UK establishments ('Other company type', FC/BR numbers).
def scope(r):
    n = r['number'] or ''; cat = r.get('ch_category') or ''
    if n.startswith(('LP', 'NL')): return 'out_of_regime: English/NI limited partnership'
    if n.startswith(('FC', 'BR', 'NF', 'SF')) or cat == 'Other company type': return 'out_of_regime: overseas company / other type'
    return 'in_regime: ' + (cat or '?')
np = [r for r in R if r['outcome'] == 'no_psc_live']
print('\nno_psc_live by PSC-regime scope:', collections.Counter(scope(r) for r in np).most_common())
print('no_psc_live Unknown only:', collections.Counter(scope(r).split(':')[0] for r in np if r['hierarchy'] == 'Unknown'))

# Where the UK trail ends, for rows that reach the group but not the head.
def trail_end(r):
    e = r.get('ends', {})
    if e.get('foreign_or_unnumbered_corporate'): return 'leaves the UK at a non-UK corporate PSC that is not the head'
    if e.get('uk_corporate_without_psc'): return 'stops at a UK company with no active PSC'
    if e.get('individual') or e.get('super_secure'): return 'ends at individuals'
    return 'other'
nh = [r for r in R if r['outcome'] == 'reaches_group' and not r.get('reaches_head')]
print('\nreaches_group but not head (%d): %s' % (len(nh), collections.Counter(trail_end(r) for r in nh).most_common()))
nhu = [r for r in nh if r['hierarchy'] == 'Unknown']
print('  Unknown only (%d): %s' % (len(nhu), collections.Counter(trail_end(r) for r in nhu).most_common()))
