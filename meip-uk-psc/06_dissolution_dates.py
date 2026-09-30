"""Step 6 — for every subject whose number is NOT in Basic Company Data (i.e. not
live on 2026-09-01), read the public Companies House company page and record the
status line and dissolution date. Resumable (skips numbers already in the output).
Polite: 3 workers, each sleeping 1 s after a request."""
import json, re, time, subprocess, os, threading
from concurrent.futures import ThreadPoolExecutor

OUT = 'dissolution.jsonl'
done = set()
if os.path.exists(OUT):
    done = {json.loads(l)['number'] for l in open(OUT)}
subs = [json.loads(l) for l in open('subjects.jsonl')]
todo = sorted({s['number'] for s in subs if s['number'] and not s['ch_status']} - done)
lock = threading.Lock()
f = open(OUT, 'a')


def one(n):
    page = subprocess.run(['curl', '-s', '-m', '20',
                           f'https://find-and-update.company-information.service.gov.uk/company/{n}'],
                          capture_output=True, text=True).stdout
    st = re.search(r'id="company-status"[^>]*>\s*([^<]+)', page)
    dd = re.search(r'id="cessation-date"[^>]*>\s*([^<]+)', page)
    rec = json.dumps({'number': n, 'status': st.group(1).strip() if st else None,
                      'ceased': dd.group(1).strip() if dd else None, 'http_ok': bool(page)})
    with lock:
        f.write(rec + '\n'); f.flush()
    time.sleep(1.0)


with ThreadPoolExecutor(3) as ex:
    list(ex.map(one, todo))
print('done', len(todo))
