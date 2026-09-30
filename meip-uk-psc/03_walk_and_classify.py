"""Step 3 — walk each UK subject's corporate-PSC chain in the Companies House
PSC graph (snapshot 2026-09-23, active PSCs only) and classify it against the
MEIP group the subject is listed in.

Walk: breadth-first from the subject's company number. At each company read
its active PSC rows. Corporate ('c') and legal-person ('l') PSCs that carry a
UK registration number are followed to that company (OpenCheck's own rule:
only UK-registered corporate PSCs are walkable). Depth cap 12; cycles walked once.

Matching a PSC (or a company reached on the chain) to a MEIP group, strongest first:
  number   – the UK company number is a GB number of a row in the group
  strict   – strict name key (legal forms folded) equals a group name key
  loose    – loose key (legal-form words dropped) equals a group loose key,
             only when the loose key is >= 5 characters and >= 1 non-generic token
For companies reached on the chain, the name tried is the filed PSC name plus the
company's current and previous names from Basic Company Data.

Subject outcome (first that applies):
  no_uk_number        MEIP gives no GB company number
  no_psc_dissolved    no active PSC rows and number not live in Basic Company Data
  no_psc_live         no active PSC rows although the company is live
  reaches_group       some PSC on the chain matches the subject's own MEIP group
  reaches_other_group chain matches a different MEIP group (and not its own)
  individuals_only    every chain end is an individual / super-secure PSC
  unmatched_corporate chain ends at a corporate/legal PSC that matches no group
"""
import json, sqlite3, collections
from common import norm_name, stem_name, normalise_ch_company_number, strict_keys, loose_keys
psc = sqlite3.connect('file:psc_graph.sqlite?mode=ro', uri=True)
bcd = sqlite3.connect('file:basic_company_data.sqlite?mode=ro', uri=True)
import os
G = json.load(open(os.environ.get('MEIP_GROUP_INDEX', 'group_index.json')))
GENERIC = {"HOLDING","HOLDINGS","GROUP","INTERNATIONAL","UK","EUROPE","INVESTMENTS","INVESTMENT","SERVICES","FINANCE","CAPITAL","TRUSTEES","NOMINEES","MANAGEMENT","PROPERTIES","LIMITED"}
def loose_ok(k): return len(k) >= 5 and any(t not in GENERIC for t in k.split())
# inverted indexes, to find OTHER groups
inv_num = collections.defaultdict(set); inv_strict = collections.defaultdict(set); inv_loose = collections.defaultdict(set)
for gname, g in G.items():
    for n in g['numbers']: inv_num[n].add(gname)
    for k in g['strict']: inv_strict[k].add(gname)
    for k in g['loose']:
        if loose_ok(k): inv_loose[k].add(gname)
def match_groups(names, number):
    """{group: best_method} for a party identified by names and (optional) UK number."""
    out = {}
    if number:
        for g in inv_num.get(number, ()): out[g] = 'number'
    for nm in names:
        for k in strict_keys(nm):
            for g in inv_strict.get(k, ()): out.setdefault(g, 'strict')
    for nm in names:
        for k in loose_keys(nm):
            if loose_ok(k):
                for g in inv_loose.get(k, ()): out.setdefault(g, 'loose')
    return out
def co_names(number):
    r = bcd.execute('select name, prev_names from co where number=?', (number,)).fetchone()
    if not r: return [], False
    return [r[0]] + [x for x in (r[1] or '').split('|') if x], True
def pscs(number):
    return psc.execute('select psc_id, kind, name, reg_number, notified_on from psc where company_number=? and ceased_on is null', (number,)).fetchall()
RANK = {'number': 0, 'strict': 1, 'loose': 2}
def is_head(group, names, number):
    g = G[group]
    if number and number in g['head_numbers']: return True
    hs, hl = set(g['head_strict']), set(g['head_loose'])
    return any(strict_keys(n) & hs for n in names) or any(k in hl for n in names for k in loose_keys(n) if loose_ok(k))

def walk(subject):
    own = subject['group']; start = subject['number']
    seen = {start}; frontier = [(start, 0)]; steps = []
    ends = collections.Counter(); own_hits = []; other_hits = collections.Counter()
    first_level = None
    while frontier:
        nxt = []
        for num, depth in frontier:
            rows = pscs(num)
            if depth == 0: first_level = rows
            if not rows:
                if depth > 0: ends['uk_corporate_without_psc'] += 1
                continue
            for psc_id, kind, name, reg, notified in rows:
                step = {'from': num, 'depth': depth + 1, 'kind': kind, 'name': name, 'reg_number': reg}
                if kind in ('i', 's'):
                    ends['individual' if kind == 'i' else 'super_secure'] += 1
                    steps.append(step); continue
                names = [name] if name else []
                if reg:
                    cn, _ = co_names(reg); names += cn
                m = match_groups(names, reg)
                step['match'] = m.get(own); step['other_groups'] = sorted(g for g in m if g != own)
                if own in m:
                    own_hits.append({'depth': depth + 1, 'method': m[own], 'name': name, 'reg_number': reg, 'is_head': is_head(own, names, reg)})
                for g in m:
                    if g != own: other_hits[g] += 1
                steps.append(step)
                if reg and reg not in seen and depth + 1 < 12:
                    seen.add(reg); nxt.append((reg, depth + 1))
                elif not reg:
                    ends['foreign_or_unnumbered_corporate'] += 1
        frontier = nxt
    return first_level, steps, ends, own_hits, other_hits

out = open(os.environ.get('MEIP_RESULTS', 'results.jsonl'), 'w'); summary = collections.Counter(); by_h = collections.defaultdict(collections.Counter)
for line in open('subjects.jsonl'):
    s = json.loads(line)
    res = dict(s)
    if not s['number']:
        res['outcome'] = 'no_uk_number'
    else:
        first, steps, ends, own_hits, other_hits = walk(s)
        res.update({'psc_count': len(first), 'psc_kinds': dict(collections.Counter(r[1] for r in first)),
                    'chain': steps, 'ends': dict(ends), 'own_hits': own_hits, 'other_groups': dict(other_hits)})
        if not first:
            res['outcome'] = 'no_psc_live' if s['ch_status'] else 'no_psc_dissolved'
        elif own_hits:
            best = min(own_hits, key=lambda h: (RANK[h['method']], h['depth']))
            res['outcome'] = 'reaches_group'; res['best_method'] = best['method']
            res['reaches_head'] = any(h['is_head'] for h in own_hits)
            res['min_depth_to_group'] = min(h['depth'] for h in own_hits)
        elif other_hits:
            res['outcome'] = 'reaches_other_group'
        elif ends.get('foreign_or_unnumbered_corporate') or ends.get('uk_corporate_without_psc'):
            res['outcome'] = 'unmatched_corporate'
        else:
            res['outcome'] = 'individuals_only'
    summary[res['outcome']] += 1; by_h[s['hierarchy']][res['outcome']] += 1
    out.write(json.dumps(res) + '\n')
out.close()
print('ALL', dict(summary))
for h, c in by_h.items(): print(h, sum(c.values()), dict(c))
