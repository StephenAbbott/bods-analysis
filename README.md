# bods-analysis

Reproducible analysis of beneficial ownership and corporate group data published in line with the
[Beneficial Ownership Data Standard (BODS)](https://standard.openownership.org). The code is MIT-licensed; each dataset keeps its own licence (below).

## Analyses

| Folder | What it does | Post |
|---|---|---|
| [`meip-global/`](meip-global) | The OECD-UNSD Multinational Enterprise Information Platform (MEIP) Global Register of the 500 largest multinational groups, vintage 31 Dec 2024: hierarchy status, where subsidiaries sit, offshore and conduit jurisdictions, headquarters, chain depth | *[What the OECD’s register of the world’s 500 largest corporate groups tells us about who owns what](https://stephenabbottpugh.medium.com/what-the-oecds-register-of-the-world-s-500-largest-corporate-groups-tells-us-about-who-owns-what-659397545db5?postPublishedType=initial)* |
| [`meip-uk-psc/`](meip-uk-psc) | MEIP's 15,678 UK subsidiaries tested against the UK register of people with significant control (PSC): how many the register links to their group and to its head | *[What an open ownership register adds: testing the UK’s PSC register against the OECD’s map of the world’s largest groups](https://stephenabbottpugh.medium.com/what-an-open-ownership-register-adds-testing-the-uk-psc-register-against-the-oecds-global-register-b3e7374e3bbe)* |
| [`estonia-register-comparison/`](estonia-register-comparison) | Estonia's declared beneficial owners tested against the same companies' shareholder lists (an open version of T-rank's Norway register comparison), for the 22,563 Estonian LEI holders in OpenCheck's Estonia dataset | *link to follow* |
| [`charts/`](charts) | Draws every chart in the posts from the CSVs in `*/results/` (`make_charts.py` for MEIP, `make_estonia_charts.py` for Estonia; shared style in `house.py`) | |

Every number quoted in the posts is in a `results/` file produced by a script here.

## Inputs (not committed — download them)

| Input | Where from | Licence |
|---|---|---|
| `globalregister2024.xlsx` (MEIP Global Register) and the BODS zip | [OECD MEIP page](https://www.oecd.org/en/data/dashboards/oecd-unsd-multinational-enterprise-information-platform.html) | OECD terms |
| `psc_graph.sqlite.gz` — the Companies House PSC snapshot as a SQLite graph (active PSCs only) | [OpenCheck release asset `psc-graph-latest`](https://github.com/StephenAbbott/opencheck/releases/tag/psc-graph-latest) (rebuilt daily; the posts used the 23 Sep 2026 snapshot) | OGL v3.0 |
| `BasicCompanyDataAsOneFile-2026-09-01.zip` | [Companies House bulk data](https://download.companieshouse.gov.uk/en_output.html) | OGL v3.0 |
| Dissolution dates | public Companies House company pages (step 6 of `meip-uk-psc`) | OGL v3.0 |
| `estonia-2026-07-04.jsonl.gz` — OpenCheck's Estonia BODS dataset: 209,529 BODS v0.4 statements covering every Estonian LEI holder, joined on the registry code to the e-Business Register's open data of 4 July 2026 (shareholders with percentages, officers, declared beneficial owners) | [OpenCheck release `dataset-estonia-2026-07-04`](https://github.com/StephenAbbott/opencheck/releases/tag/dataset-estonia-2026-07-04) | CC BY 4.0 (e-Business Register layer CC BY 4.0, GLEIF layer CC0) |

The SHA-256 hashes of the files used are in `meip-uk-psc/results/inputs.sha256` and `estonia-register-comparison/results/inputs.json`.

## Running

```
pip install openpyxl matplotlib
# global
cd meip-global
python3 01_export_meip_rows.py /path/to/globalregister2024.xlsx
python3 00_bods_profile.py /path/to/meip_bods.jsonl > results/bods_profile.json
python3 02_global_analysis.py
# UK (see meip-uk-psc/README.md for the full run order)
cd ../meip-uk-psc && cp ../meip-global/meip_rows.jsonl.gz . && ...
# Estonia (see estonia-register-comparison/README.md)
cd ../estonia-register-comparison
python3 01_load.py /path/to/estonia-2026-07-04.jsonl.gz
python3 02_compare.py && python3 03_summarise.py && python3 04_family_surnames.py
# charts
cd .. && python3 charts/make_charts.py && python3 charts/make_estonia_charts.py
```

## Offshore classification

`meip-global/corpnet.py` holds the sink and conduit offshore financial centres from
Garcia-Bernardo, J., Fichtner, J., Takes, F. W. & Heemskerk, E. M. (2017), *Uncovering Offshore
Financial Centers: Conduits and Sinks in the Global Corporate Ownership Network*, Scientific
Reports 7, 6246, [doi:10.1038/s41598-017-06322-9](https://doi.org/10.1038/s41598-017-06322-9), copied verbatim.
