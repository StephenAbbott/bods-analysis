"""Step 9 — sensitivity check: rerun with aliases.json (renamed / differently written
group heads) and compare with the headline run, on the base of subjects that existed at
the 31 Dec 2024 vintage. Produce with:
  MEIP_ALIASES=aliases.json MEIP_GROUP_INDEX=group_index_alias.json MEIP_SUBJECTS=/tmp/s.jsonl python3 02b_build_subjects.py
  MEIP_GROUP_INDEX=group_index_alias.json MEIP_RESULTS=results_alias.jsonl python3 03_walk_and_classify.py
then run this script."""
import json, collections
V = {json.loads(l)['row']: json.loads(l)['vintage_status'] for l in open('results_with_vintage.jsonl')}
A = {json.loads(l)['row']: json.loads(l) for l in open('results.jsonl')}
B = {json.loads(l)['row']: json.loads(l) for l in open('results_alias.jsonl')}
alive = [k for k, v in V.items() if v in ('live_now', 'dissolved_after_vintage')]
for h in ['Unknown', 'ALL']:
    ks = [k for k in alive if h == 'ALL' or A[k]['hierarchy'] == h]
    for lab, R in (('headline', A), ('with aliases', B)):
        rg = sum(R[k]['outcome'] == 'reaches_group' for k in ks); hd = sum(bool(R[k].get('reaches_head')) for k in ks)
        print(f"{h:8s} {lab:13s} n={len(ks):,} reaches_group {rg:,} ({100*rg/len(ks):.1f}%)  reaches_head {hd:,} ({100*hd/len(ks):.1f}%)")
chg = collections.Counter(); ex = collections.defaultdict(list)
for k in alive:
    a, b = A[k], B[k]
    key = (a['group'], a['outcome'], b['outcome'], bool(a.get('reaches_head')), bool(b.get('reaches_head')))
    if key[1:3] != (key[2], key[2]) or key[3] != key[4]:
        if (a['outcome'], bool(a.get('reaches_head'))) != (b['outcome'], bool(b.get('reaches_head'))):
            chg[key] += 1; ex[key].append(a['name'])
print('\nchanged rows (group, outcome before->after, head before->after):')
for k, v in chg.most_common(): print(v, k, ex[k][:2])
