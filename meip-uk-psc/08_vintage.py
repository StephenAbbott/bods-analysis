"""Step 8 — split subjects by whether the company existed at MEIP's vintage date.
live_now: in Basic Company Data 2026-09-01. Otherwise the public CH page (step 6) gives
status + cessation date: 'dissolved_after_vintage' if ceased > 2024-12-31,
'dissolved_before_vintage' if on/before, 'not_found' if the page carried no status.
Then the outcome table is recomputed for subjects that existed at the vintage date."""
import json, collections, datetime
D = {r['number']: r for r in (json.loads(l) for l in open('dissolution.jsonl'))}
R = [json.loads(l) for l in open('results.jsonl')]
VINTAGE = datetime.date(2024, 12, 31)
def when(r):
    if not r['number']: return 'no_uk_number'
    if r['ch_status']: return 'live_now'
    d = D.get(r['number'])
    if not d or not d['status']: return 'not_found'
    if not d['ceased']: return 'closed_no_date'
    dt = datetime.datetime.strptime(d['ceased'], '%d %B %Y').date()
    return 'dissolved_after_vintage' if dt > VINTAGE else 'dissolved_before_vintage'
years = collections.Counter()
for r in R:
    r['vintage_status'] = when(r)
    if r['vintage_status'] == 'dissolved_before_vintage':
        years[D[r['number']]['ceased'][-4:]] += 1
print('vintage status (all 15,678):', collections.Counter(r['vintage_status'] for r in R).most_common())
print('by hierarchy:', {h: dict(collections.Counter(r['vintage_status'] for r in R if r['hierarchy'] == h)) for h in ['Unknown', 'Known', 'Partial']})
print('dissolved before vintage, by year of dissolution:', sorted(years.items()))
print('status words:', collections.Counter(D[r['number']]['status'] for r in R if r['vintage_status'] in ('dissolved_before_vintage', 'dissolved_after_vintage')))
alive = [r for r in R if r['vintage_status'] in ('live_now', 'dissolved_after_vintage')]
for h in ['Unknown', 'Known', 'Partial', 'ALL']:
    rs = [r for r in alive if h == 'ALL' or r['hierarchy'] == h]
    c = collections.Counter(r['outcome'] for r in rs); n = len(rs)
    rg = [r for r in rs if r['outcome'] == 'reaches_group']; hd = sum(bool(r.get('reaches_head')) for r in rg)
    print(f"\nexisting at vintage, {h}: {n:,}")
    for k, v in c.most_common(): print(f"  {k:22s} {v:,} ({100*v/n:.1f}%)")
    print(f"  reaches head: {hd:,} ({100*hd/n:.1f}% of all, {100*hd/len(rg):.1f}% of reaches_group)")
with open('results_with_vintage.jsonl', 'w') as f:
    for r in R: f.write(json.dumps(r) + '\n')
