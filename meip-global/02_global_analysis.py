"""Global picture of the OECD-UNSD MEIP Global Register (vintage 31 Dec 2024).

Input : meip_rows.jsonl.gz, produced from globalregister2024.xlsx by 01_export_meip_rows.py
Output: results/*.csv (one table per figure) and results/summary.json (every number the
        global post quotes). Run: python3 02_global_analysis.py

Definitions
- A *subsidiary* is a Group Register row whose Hierarchy is not "MNE Head" (126,157 rows).
  The spreadsheet has 501 head rows for 500 groups (one group lists two heads).
- *Host* = the row's ISO3 column. Rows with no ISO3 are counted as "not given".
- *Identifier* = any of OpenCorporates, LEI, PermID or DUNL on the row.
- Heads are used exactly as MEIP publishes them. About 4% of groups have a head row that
  is not the listed parent (e.g. Munich Re's head is a UK pension trustee); see the post.
- Offshore lists: corpnet.py (Garcia-Bernardo et al. 2017), verbatim.
- Chain depth: rebuilt from 'Parent of Subsidiary' by matching the parent name to another
  row of the same group (exact, case-insensitive). Only rows with a parent can be placed."""
import gzip, json, collections, statistics, csv, os
from corpnet import SINKS, CONDUITS
from countries import name
os.makedirs('results', exist_ok=True)
rows = [json.loads(l) for l in gzip.open('meip_rows.jsonl.gz', 'rt')]
subs = [r for r in rows if r['Hierarchy'] != 'MNE Head']
heads = [r for r in rows if r['Hierarchy'] == 'MNE Head']
S = {}
def pct(a, b): return round(100 * a / b, 1)
def write(fn, header, data):
    with open(f'results/{fn}', 'w', newline='') as f:
        w = csv.writer(f); w.writerow(header); w.writerows(data)

# 1. Hierarchy
h = collections.Counter(r['Hierarchy'] for r in rows)
S['rows'] = len(rows); S['subsidiaries'] = len(subs); S['head_rows'] = len(heads)
S['groups'] = len({r['Parent MNE'] for r in rows})
S['hierarchy_all_rows'] = dict(h)
S['unknown_share_all_rows_pct'] = pct(h['Unknown'], len(rows))
S['unknown_share_subsidiaries_pct'] = pct(h['Unknown'], len(subs))
byg = collections.defaultdict(list)
for r in rows: byg[r['Parent MNE']].append(r)
gun = []
for g, v in byg.items():
    sv = [r for r in v if r['Hierarchy'] != 'MNE Head']
    if sv: gun.append((g, len(sv), pct(sum(r['Hierarchy'] == 'Unknown' for r in sv), len(sv))))
S['groups_over_95pct_unknown'] = sum(u > 95 for _, _, u in gun)
S['groups_fully_known'] = sum(u == 0 for _, _, u in gun)
S['groups_median_unknown_pct'] = statistics.median(u for _, _, u in gun)
write('group_unknown_share.csv', ['group', 'subsidiaries', 'unknown_pct'], sorted(gun, key=lambda x: x[2]))
S['best_known_groups_100plus'] = [(g, n, u) for g, n, u in sorted(gun, key=lambda x: x[2]) if n >= 100][:8]

# 2. Hosts: share, hierarchy, identifiers
host = collections.defaultdict(list)
for r in subs: host[r['ISO3'] or ''].append(r)
S['host_jurisdictions'] = len([k for k in host if k])
def has_id(r): return any(r.get(k) for k in ('OpenCorporates', 'LEI', 'PermID', 'DUNL'))
tab = []
for c, v in host.items():
    n = len(v)
    tab.append((c, name(c), n, pct(n, len(subs)),
                pct(sum(r['Hierarchy'] == 'Unknown' for r in v), n),
                pct(sum(not has_id(r) for r in v), n),
                pct(sum(bool(r.get('OpenCorporates')) for r in v), n),
                pct(sum(bool(r.get('LEI')) for r in v), n)))
tab.sort(key=lambda x: -x[2])
write('hosts.csv', ['iso3', 'name', 'subsidiaries', 'share_pct', 'unknown_pct', 'no_identifier_pct', 'opencorporates_pct', 'lei_pct'], tab)
hb = {'All 126,157 subsidiaries': [pct(sum(r['Hierarchy'] == k for r in subs), len(subs)) for k in ('Known', 'Partial', 'Unknown')]}
for c, v in host.items():
    if c: hb[name(c)] = [pct(sum(r['Hierarchy'] == k for r in v), len(v)) for k in ('Known', 'Partial', 'Unknown')]
json.dump(hb, open('results/hierarchy_by_host.json', 'w'), indent=1)
S['top_hosts'] = [(t[1], t[2], t[3]) for t in tab[:10]]
S['subsidiaries_no_identifier_pct'] = pct(sum(not has_id(r) for r in subs), len(subs))
big = [t for t in tab if t[2] >= 500 and t[0]]
S['hosts_500plus'] = len(big)

# 3. HQ geography (heads as published; one row per group, first head row)
hq = {}
for r in heads: hq.setdefault(r['Parent MNE'], r['ISO3'])
hqc = collections.Counter(hq.values())
write('hq_countries.csv', ['iso3', 'name', 'groups'], [(c, name(c), n) for c, n in hqc.most_common()])
S['hq_top'] = [(name(c), n) for c, n in hqc.most_common(12)]
S['uk_hq_groups'] = hqc['GBR']
off_hq = sorted((g, c) for g, c in hq.items() if c in SINKS or c in CONDUITS and c != 'GBR')
S['heads_in_sinks'] = sorted(g for g, c in hq.items() if c in SINKS)
S['heads_in_conduits_excl_uk'] = sorted(g for g, c in hq.items() if c in CONDUITS and c != 'GBR')
nj = [(g, len({r['ISO3'] for r in v if r['Hierarchy'] != 'MNE Head' and r['ISO3']})) for g, v in byg.items()]
S['jurisdictions_per_group_median'] = statistics.median(n for _, n in nj)
S['jurisdictions_per_group_top'] = sorted(nj, key=lambda x: -x[1])[:8]
home = []
for g, v in byg.items():
    sv = [r for r in v if r['Hierarchy'] != 'MNE Head']
    if sv and hq.get(g): home.append((g, name(hq[g]), len(sv), pct(sum(r['ISO3'] == hq[g] for r in sv), len(sv))))
write('home_share.csv', ['group', 'hq_as_published', 'subsidiaries', 'home_share_pct'], sorted(home, key=lambda x: x[3]))
S['home_share_median_pct'] = statistics.median(x[3] for x in home)

# 4. Offshore (CORPNET)
ns = sum(r['ISO3'] in SINKS for r in subs); nc = sum(r['ISO3'] in CONDUITS for r in subs)
ncx = sum(r['ISO3'] in CONDUITS and r['ISO3'] != 'GBR' for r in subs)
S['sink_subsidiaries'] = ns; S['sink_share_pct'] = pct(ns, len(subs))
S['conduit_subsidiaries'] = nc; S['conduit_share_pct'] = pct(nc, len(subs))
S['conduit_excl_uk_subsidiaries'] = ncx; S['conduit_excl_uk_share_pct'] = pct(ncx, len(subs))
sinkc = collections.Counter(r['ISO3'] for r in subs if r['ISO3'] in SINKS)
write('sinks_by_jurisdiction.csv', ['iso3', 'name', 'subsidiaries'], [(c, name(c), sinkc[c]) for c in SINKS])
S['sinks_by_jurisdiction_top'] = [(name(c), n) for c, n in sinkc.most_common(10)]
S['sink_jurisdictions_present'] = sum(1 for c in SINKS if sinkc[c])
gs = []
for g, v in byg.items():
    sv = [r for r in v if r['Hierarchy'] != 'MNE Head']
    if not sv: continue
    k = sum(r['ISO3'] in SINKS for r in sv)
    gs.append((g, len(sv), k, pct(k, len(sv))))
write('group_sink_share.csv', ['group', 'subsidiaries', 'sink_subsidiaries', 'sink_pct'], sorted(gs, key=lambda x: -x[2]))
S['groups_with_any_sink'] = sum(1 for x in gs if x[2])
S['groups_with_any_sink_pct'] = pct(S['groups_with_any_sink'], len(gs))
S['top_groups_by_sink_count'] = sorted(gs, key=lambda x: -x[2])[:10]
S['top_groups_by_sink_share_50plus'] = sorted([x for x in gs if x[1] >= 50], key=lambda x: -x[3])[:10]
# comparison: Cayman vs Italy etc.
S['cayman_vs_italy'] = (len(host['CYM']), len(host['ITA']))

# 5. Chain depth from Parent of Subsidiary
depth = collections.Counter(); per_group_max = {}; mid = collections.Counter(); withp = resolved = 0
for g, v in byg.items():
    idx = {}
    for r in v: idx.setdefault((r['Subsidiary Name (Clean)'] or '').strip().upper(), r)
    par = {}
    for r in v:
        p = (r.get('Parent of Subsidiary') or '').strip().upper()
        if p:
            withp += 1
            if p in idx and idx[p] is not r: par[r['_row']] = idx[p]; resolved += 1
    mx = 0
    for r in v:
        if r['_row'] not in par: continue
        d, cur, seen = 0, r, set()
        while cur['_row'] in par and cur['_row'] not in seen:
            seen.add(cur['_row']); cur = par[cur['_row']]; d += 1
        if cur['Hierarchy'] == 'MNE Head':
            depth[d] += 1; mx = max(mx, d)
    per_group_max[g] = mx
    for r in v:
        if r['_row'] in par and par[r['_row']]['Hierarchy'] != 'MNE Head':
            pass
    for p in {id(x): x for x in par.values()}.values():
        if p['Hierarchy'] != 'MNE Head': mid[p['ISO3']] += 1
S['rows_with_parent'] = withp; S['rows_parent_resolved'] = resolved
S['rows_with_parent_pct_of_subs'] = pct(withp, len(subs))
S['depth_to_head'] = dict(sorted(depth.items()))
S['placed_under_head'] = sum(depth.values())
S['deepest_groups'] = sorted(per_group_max.items(), key=lambda x: -x[1])[:8]
S['intermediate_holding_jurisdictions'] = [(name(c), n) for c, n in mid.most_common(10)]
write('depth_to_head.csv', ['layers_below_head', 'subsidiaries'], sorted(depth.items()))
json.dump(S, open('results/summary.json', 'w'), indent=1, ensure_ascii=False)
for k, v in S.items(): print(k, ':', v)
