"""Step 11 — the tables behind the UK post's charts, all on the base the post uses:
UK subsidiaries that existed on 31 Dec 2024 (results_with_vintage.jsonl).
Writes results/uk_*.csv and results/uk_summary.json."""
import json, collections, csv, datetime
R = [json.loads(l) for l in open('results_with_vintage.jsonl')]
D = {json.loads(l)['number']: json.loads(l) for l in open('dissolution.jsonl')}
alive = lambda r: r['vintage_status'] in ('live_now', 'dissolved_after_vintage')
S = {}
def w(fn, hdr, rows):
    with open('results/' + fn, 'w', newline='') as f:
        x = csv.writer(f); x.writerow(hdr); x.writerows(rows)
unk = [r for r in R if r['hierarchy'] == 'Unknown']
ua = [r for r in unk if alive(r)]
rg = [r for r in ua if r['outcome'] == 'reaches_group']; hd = [r for r in rg if r.get('reaches_head')]
funnel = [('UK subsidiaries in MEIP', len(R)), ('marked "Unknown" by MEIP', len(unk)),
          ('...that existed on 31 Dec 2024', len(ua)), ('PSC chain reaches the MEIP group', len(rg)),
          ('PSC chain reaches the head MEIP records', len(hd))]
w('uk_funnel.csv', ['stage', 'subsidiaries'], funnel); S['funnel'] = funnel
hdep = collections.Counter(min(x['depth'] for x in r['own_hits'] if x['is_head']) for r in hd)
w('uk_head_depth.csv', ['layers_to_head', 'subsidiaries'], sorted(hdep.items())); S['head_depth'] = dict(sorted(hdep.items()))
S['head_depth_4plus'] = sum(v for k, v in hdep.items() if k >= 4)
oc = collections.Counter(r['outcome'] for r in ua)
w('uk_outcomes.csv', ['outcome', 'subsidiaries'], oc.most_common()); S['outcomes_unknown_alive'] = dict(oc)
def trail(r):
    e = r.get('ends', {})
    if e.get('foreign_or_unnumbered_corporate'): return 'leaves the UK at a foreign parent that is not the head'
    if e.get('uk_corporate_without_psc'): return 'stops at a UK company with no active PSC'
    if e.get('individual') or e.get('super_secure'): return 'ends at individuals'
    return 'other'
tr = collections.Counter(trail(r) for r in rg if not r.get('reaches_head'))
w('uk_trail_end.csv', ['where the trail stops', 'subsidiaries'], tr.most_common()); S['trail_end'] = dict(tr)
yrs = collections.Counter()
for r in R:
    if r['vintage_status'] == 'dissolved_before_vintage': yrs[int(D[r['number']]['ceased'][-4:])] += 1
w('uk_dissolved_before_vintage_by_year.csv', ['year_dissolved', 'subsidiaries'], sorted(yrs.items()))
S['dissolved_before_vintage'] = sum(yrs.values()); S['dissolved_by_year'] = dict(sorted(yrs.items()))
S['vintage_status_all'] = dict(collections.Counter(r['vintage_status'] for r in R))
json.dump(S, open('results/uk_summary.json', 'w'), indent=1)
for k, v in S.items(): print(k, v)
