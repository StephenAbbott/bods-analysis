"""Step 7 — per-group table for groups with >= 50 UK subsidiaries in MEIP:
MEIP's Unknown share vs the share the PSC chain places in the group / at the head."""
import json, collections, csv
R = [json.loads(l) for l in open('results.jsonl')]
g = collections.defaultdict(list)
for r in R: g[r['group']].append(r)
rows = []
for k, v in g.items():
    n = len(v)
    if n < 50: continue
    unk = sum(r['hierarchy'] == 'Unknown' for r in v)
    rg = sum(r['outcome'] == 'reaches_group' for r in v)
    hd = sum(bool(r.get('reaches_head')) for r in v)
    rows.append((k, n, round(100*unk/n), round(100*rg/n), round(100*hd/n)))
rows.sort(key=lambda x: -x[1])
with open('per_group.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['group', 'uk_subsidiaries', 'meip_unknown_pct', 'psc_reaches_group_pct', 'psc_reaches_head_pct']); w.writerows(rows)
print(len(rows), 'groups'); [print(r) for r in rows[:25]]
print('lowest head share:'); [print(r) for r in sorted(rows, key=lambda x: x[4])[:10]]
