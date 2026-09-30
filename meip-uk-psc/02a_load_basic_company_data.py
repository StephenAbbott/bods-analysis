"""Step 2a — load Companies House Basic Company Data (live companies only; the
free monthly bulk product) into SQLite so every step can read a company's
current name, status, category and previous names by number.
Source: https://download.companieshouse.gov.uk/BasicCompanyDataAsOneFile-2026-09-01.zip
(OGL v3.0). Dissolved companies are NOT in this product: a number absent from
it has been dissolved/removed (or was never a CH number)."""
import csv, io, sqlite3, zipfile, sys
Z = 'BasicCompanyDataAsOneFile-2026-09-01.zip'
db = sqlite3.connect('basic_company_data.sqlite')
db.execute('drop table if exists co')
db.execute('create table co (number text primary key, name text, category text, status text, country_of_origin text, incorporated text, prev_names text) without rowid')
zf = zipfile.ZipFile(Z); member = zf.namelist()[0]
rdr = csv.reader(io.TextIOWrapper(zf.open(member), encoding='utf-8', newline=''))
hdr = [h.strip() for h in next(rdr)]
ix = {h: i for i, h in enumerate(hdr)}
prev_cols = [ix[f'PreviousName_{k}.CompanyName'] for k in range(1, 11)]
batch = []; n = 0
short = 0
for r in rdr:
    if len(r) < len(hdr):
        short += 1; r = r + [''] * (len(hdr) - len(r))
    prev = '|'.join(r[c].strip() for c in prev_cols if r[c].strip())
    batch.append((r[ix['CompanyNumber']].strip(), r[ix['CompanyName']].strip(), r[ix['CompanyCategory']], r[ix['CompanyStatus']], r[ix['CountryOfOrigin']], r[ix['IncorporationDate']], prev))
    if len(batch) == 100000:
        db.executemany('insert or replace into co values (?,?,?,?,?,?,?)', batch); batch = []; n += 100000
db.executemany('insert or replace into co values (?,?,?,?,?,?,?)', batch); n += len(batch)
db.commit()
print('rows', n, 'short rows padded', short, db.execute('select status,count(*) from co group by status order by 2 desc').fetchall())
