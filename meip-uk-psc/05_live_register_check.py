"""Step 5 — verify the PSC store against the live Companies House register for a
random sample of subjects: fetch each company's public PSC page and compare the
active PSC names with the store's. Polite: 1 request / 1.5 s."""
import json, random, re, time, html, subprocess
from common import norm_name
random.seed(7)
R = [json.loads(l) for l in open('results.jsonl')]
pool = [r for r in R if r.get('psc_count')]
sample = random.sample(pool, 40)
ok = diff = 0; lines = []
for r in sample:
    n = r['number']
    page = subprocess.run(['curl', '-s', f'https://find-and-update.company-information.service.gov.uk/company/{n}/persons-with-significant-control'], capture_output=True, text=True).stdout
    # active PSCs only: split blocks, drop those marked Ceased
    blocks = re.split(r'id="psc-name-\d+"', page)[1:]
    live = set()
    for b in blocks:
        m = re.search(r'<b>(.*?)</b>', b, re.S)
        if not m: continue
        if re.search(r'Ceased on', b.split('psc-name')[0][:3000]): continue
        live.add(norm_name(html.unescape(m.group(1)).strip()))
    store = {norm_name(s['name']) for s in r['chain'] if s['depth'] == 1}
    same = live == store
    ok += same; diff += (not same)
    lines.append(f"{'OK ' if same else 'DIFF'} {n} {r['name'][:40]} store={sorted(store)} live={sorted(live)}")
    time.sleep(1.5)
open('live_register_check.txt', 'w').write('\n'.join(lines) + f"\nOK {ok} DIFF {diff}\n")
print('\n'.join(lines)); print('OK', ok, 'DIFF', diff)
