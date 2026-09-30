"""Step 10 — what kind of control does the UK register record at the first link?
For every subject that existed at the vintage date and reaches its MEIP group, take the
depth-1 corporate PSC(s) that match the subject's own group, read their natures of control
from the PSC store, and band them:
  majority      shares or votes 50-75% or 75-100% (MEIP's own test is >50% of votes)
  25-50         shares or votes 25-50% only
  appoint       right to appoint/remove directors (or members/person), no share/vote band
  influence     significant influence or control only
Also report subjects whose first group-member PSC reaches the chain at depth >1 (the first
link is a non-group company) separately."""
import json, sqlite3, collections
psc = sqlite3.connect('file:psc_graph.sqlite?mode=ro', uri=True)
codes = dict(psc.execute('select code_byte, code from nature_codes').fetchall())
R = [json.loads(l) for l in open('results_with_vintage.jsonl')]
def band(natures):
    txt = [codes[b] for b in natures]
    if any(('ownership-of-shares' in t or 'voting-rights' in t or 'surplus-assets' in t) and ('75-to-100' in t or '50-to-75' in t) for t in txt): return 'majority'
    if any('25-to-50' in t for t in txt): return '25-50'
    if any('right-to-appoint' in t for t in txt): return 'appoint'
    if any('significant-influence' in t for t in txt): return 'influence'
    return 'other'
per_subject = collections.Counter(); all_links = collections.Counter(); first_link_nongroup = 0
by_h = collections.defaultdict(collections.Counter)
for r in R:
    if r['vintage_status'] not in ('live_now', 'dissolved_after_vintage') or r['outcome'] != 'reaches_group': continue
    firsts = [s for s in r['chain'] if s['depth'] == 1 and s['kind'] in 'cl' and s.get('match')]
    if not firsts: first_link_nongroup += 1; continue
    bands = []
    for s in firsts:
        rows = psc.execute('select natures from psc where company_number=? and kind=? and name is ? and ceased_on is null', (r['number'], s['kind'], s['name'])).fetchall()
        for (nat,) in rows:
            b = band(nat or b''); bands.append(b); all_links[b] += 1
    order = ['majority', '25-50', 'appoint', 'influence', 'other']
    best = min(bands, key=order.index) if bands else 'not_found'
    per_subject[best] += 1; by_h[r['hierarchy']][best] += 1
n = sum(per_subject.values())
print('subjects (existing at vintage, reaches_group) with a group-member PSC at depth 1:', n, '| first link is a non-group company:', first_link_nongroup)
for k, v in per_subject.most_common(): print(f'  {k:10s} {v:,} ({100*v/n:.1f}%)')
print('by hierarchy:', {h: dict(c) for h, c in by_h.items()})
print('all depth-1 group-member PSC links:', dict(all_links))
