"""Export every Group Register row of the OECD-UNSD MEIP Global Register spreadsheet to
gzipped JSON lines. HYPERLINK formulas are reduced to their display value (the identifier);
`_row` keeps the spreadsheet row number for audit.
Run: python3 01_export_meip_rows.py /path/to/globalregister2024.xlsx   -> meip_rows.jsonl.gz"""
import openpyxl, json, gzip, re, hashlib, sys
SRC = sys.argv[1] if len(sys.argv) > 1 else 'globalregister2024.xlsx'
OUT = 'meip_rows.jsonl.gz'
def disp(v):
    if isinstance(v, str):
        m = re.match(r'=HYPERLINK\("[^"]*",\s*"([^"]*)"\)', v)
        if m: return m.group(1)
    return v
h = hashlib.sha256(open(SRC, 'rb').read()).hexdigest()
ws = openpyxl.load_workbook(SRC, read_only=True)['Group Register']
n = 0
with gzip.open(OUT, 'wt') as f:
    for i, r in enumerate(ws.iter_rows(values_only=True)):
        if i == 0: hdr = list(r); continue
        rec = {k: disp(v) for k, v in zip(hdr, r)}; rec['_row'] = i + 1
        f.write(json.dumps(rec, ensure_ascii=False, default=str) + '\n'); n += 1
print('rows', n, 'xlsx sha256', h)
