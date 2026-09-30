# bods-analysis

Reproducible analysis of beneficial ownership and corporate group data published in the
[Beneficial Ownership Data Standard (BODS)](https://standard.openownership.org).

By Stephen Abbott Pugh. The code is MIT-licensed; each dataset keeps its own licence (below).

## Analyses

| Folder | What it does | Post |
|---|---|---|
| [`meip-global/`](meip-global) | The OECD-UNSD Multinational Enterprise Information Platform (MEIP) Global Register of the 500 largest multinational groups, vintage 31 Dec 2024: hierarchy status, where subsidiaries sit, offshore and conduit jurisdictions, headquarters, chain depth | *Post 1 (link when published)* |
| [`meip-uk-psc/`](meip-uk-psc) | MEIP's 15,678 UK subsidiaries tested against the UK register of people with significant control (PSC): how many the register links to their group and to its head | *Post 2 (link when published)* |
| [`charts/`](charts) | Draws every chart in both posts from the CSVs in `*/results/` | |

Every number quoted in the posts is in a `results/` file produced by a script here.

## Inputs (not committed — download them)

| Input | Where from | Licence |
|---|---|---|
| `globalregister2024.xlsx` (MEIP Global Register) and the BODS zip | [OECD MEIP page](https://www.oecd.org/en/data/dashboards/oecd-unsd-multinational-enterprise-information-platform.html) | OECD terms |
| `psc_graph.sqlite.gz` — the Companies House PSC snapshot as a SQLite graph (active PSCs only) | [OpenCheck release asset `psc-graph-latest`](https://github.com/StephenAbbott/opencheck/releases/tag/psc-graph-latest) (rebuilt daily; the posts used the 23 Sep 2026 snapshot) | OGL v3.0 |
| `BasicCompanyDataAsOneFile-2026-09-01.zip` | [Companies House bulk data](https://download.companieshouse.gov.uk/en_output.html) | OGL v3.0 |
| Dissolution dates | public Companies House company pages (step 6 of `meip-uk-psc`) | OGL v3.0 |

The SHA-256 hashes of the files used are in `meip-uk-psc/results/inputs.sha256`.

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
# charts
cd .. && python3 charts/make_charts.py
```

## Offshore classification

`meip-global/corpnet.py` holds the sink and conduit offshore financial centres from
Garcia-Bernardo, J., Fichtner, J., Takes, F. W. & Heemskerk, E. M. (2017), *Uncovering Offshore
Financial Centers: Conduits and Sinks in the Global Corporate Ownership Network*, Scientific
Reports 7, 6246, [doi:10.1038/s41598-017-06322-9](https://doi.org/10.1038/s41598-017-06322-9), copied verbatim.
