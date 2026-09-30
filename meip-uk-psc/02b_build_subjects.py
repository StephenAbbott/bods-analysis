"""Step 2b — the UK subjects and the per-group name/number index.
Subjects = MEIP Group Register rows with ISO3 == GBR and Hierarchy != 'MNE Head'.
CH numbers come from the OpenCorporates id ('gb/<n>') and every 'GBBR:<n>' in
Business ID, normalised with OpenCheck's normaliser. When a row carries more than
one distinct GB number, the number that is live in Basic Company Data is
preferred (first such, in OC-then-Business-ID order); the row is flagged.
Group index = for every Parent MNE: the strict and loose name keys of every row
(head + subsidiaries, 'Subsidiary Name (Clean)' plus each 'Alternative Names'
entry plus the 'Parent MNE' label itself) and every GB number of every row."""
import gzip, json, sqlite3, re, collections
from common import normalise_ch_company_number, norm_name, stem_name, strict_keys, loose_keys
rows = [json.loads(l) for l in gzip.open('meip_rows.jsonl.gz', 'rt')]
bcd = sqlite3.connect('file:basic_company_data.sqlite?mode=ro', uri=True)
def live(n): return bcd.execute('select name,status,category,prev_names from co where number=?', (n,)).fetchone()

def gb_numbers(r):
    out = []
    oc = r.get('OpenCorporates') or ''
    if oc.startswith('gb/'): out.append(oc[3:])
    for p in re.split(r'[,;|]\s*', str(r.get('Business ID') or '')):
        if p.startswith('GBBR:'): out.append(p[5:])
    seen = []
    for x in out:
        n = normalise_ch_company_number(x)
        if n and n not in seen: seen.append(n)
    return seen

def alt_names(r):
    a = r.get('Alternative Names') or ''
    return [x.strip() for x in re.split(r'[;|]', str(a)) if x.strip()]

groups = collections.defaultdict(lambda: {'strict': set(), 'loose': set(), 'numbers': set(), 'head_strict': set(), 'head_loose': set(), 'head_numbers': set()})
for r in rows:
    g = groups[r['Parent MNE']]
    names = [r['Subsidiary Name (Clean)']] + alt_names(r)
    nums = gb_numbers(r)
    for nm in names:
        g['strict'].update(strict_keys(nm)); g['loose'].update(loose_keys(nm))
    g['numbers'].update(nums)
    if r['Hierarchy'] == 'MNE Head':
        for nm in names + [r['Parent MNE']]:
            g['head_strict'].update(strict_keys(nm)); g['head_loose'].update(loose_keys(nm))
        g['head_numbers'].update(nums)
for k, g in groups.items():  # the Parent MNE label names the group too
    g['strict'].update(strict_keys(k)); g['loose'].update(loose_keys(k))
import os
ALIASES = os.environ.get('MEIP_ALIASES')  # sensitivity run only (step 9)
if ALIASES:
    for a in json.load(open(ALIASES))['aliases']:
        g = groups[a['group']]
        for fld_s, fld_l in (('strict', 'loose'), ('head_strict', 'head_loose')):
            g[fld_s].update(strict_keys(a['alias'])); g[fld_l].update(loose_keys(a['alias']))
json.dump({k: {kk: sorted(v) for kk, v in g.items()} for k, g in groups.items()}, open(os.environ.get('MEIP_GROUP_INDEX', 'group_index.json'), 'w'))

subs = []; stats = collections.Counter()
for r in rows:
    if r['ISO3'] != 'GBR' or r['Hierarchy'] == 'MNE Head': continue
    nums = gb_numbers(r)
    chosen = None; live_row = None
    for n in nums:
        lr = live(n)
        if lr: chosen, live_row = n, lr; break
    if chosen is None and nums: chosen = nums[0]
    stats['multi_gb_numbers' if len(nums) > 1 else ('one_gb_number' if nums else 'no_gb_number')] += 1
    stats['live_in_bcd' if live_row else ('not_in_bcd' if chosen else 'n/a')] += 1
    subs.append({'row': r['_row'], 'group': r['Parent MNE'], 'hierarchy': r['Hierarchy'],
                 'name': r['Subsidiary Name (Clean)'], 'meip_parent': r.get('Parent of Subsidiary'),
                 'gb_numbers': nums, 'number': chosen,
                 'ch_name': live_row[0] if live_row else None, 'ch_status': live_row[1] if live_row else None,
                 'ch_category': live_row[2] if live_row else None})
with open(os.environ.get('MEIP_SUBJECTS', 'subjects.jsonl'), 'w') as f:
    for s in subs: f.write(json.dumps(s) + '\n')
print('subjects', len(subs), dict(stats))
print('groups', len(groups))
