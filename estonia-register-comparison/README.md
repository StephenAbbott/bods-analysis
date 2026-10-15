# Estonia: declared beneficial owners against the shareholder data

An open version of the register comparison T-rank has run on Norway's register of
beneficial owners (84% matched; [T-rank, 18 Sep 2026](https://trank.no/news/the-danish-beneficial-ownership-register/)):
for every Estonian company that holds an LEI, are the people it has declared to the
e-Business Register as its beneficial owners the people its own shareholder list
points to?

Post: *[link to follow]*

## Input

`estonia-2026-07-04.jsonl.gz` from the OpenCheck release
[`dataset-estonia-2026-07-04`](https://github.com/StephenAbbott/opencheck/releases/tag/dataset-estonia-2026-07-04)
(CC BY 4.0; RIK layer CC BY 4.0, GLEIF layer CC0). 209,529 BODS v0.4 statements:
every Estonian LEI holder, joined on the registry code to the e-Business Register's
bulk open data of 4 July 2026 (shareholders with their percentage, officers, and
declared beneficial owners). SHA-256 of the file used is in `results/inputs.json`.

## Run order

```
python3 01_load.py /path/to/estonia-2026-07-04.jsonl.gz   # -> tables.json.gz, results/inputs.json
python3 02_compare.py                                     # -> results/company_outcomes.csv, person_differences.csv, summary.json
python3 03_summarise.py                                   # -> results/*.csv, results/post_figures.json
python3 04_family_surnames.py                             # -> results/family_surnames.json
cd .. && python3 charts/make_estonia_charts.py            # -> charts/png/e*.png
```

No dependencies beyond the standard library (and matplotlib for the charts).
`ownership_math.py` is copied unchanged from [OpenCheck](https://github.com/StephenAbbott/opencheck)
(`backend/opencheck/ownership_math.py`, Phase 339).

## Method

**Who is a beneficial owner in Estonia.** The Money Laundering and Terrorist Financing
Prevention Act (RahaPTS § 9): the natural person who ultimately owns or controls the
company. Direct ownership is a holding of *more than 25%*; indirect ownership is a
holding of more than 25% by a company the person controls. Where nobody qualifies, the
management board is recorded.

**Calculated owners.** From each company's shareholder list (several participations
held by one owner are added), stakes are multiplied along each chain of companies and
added across chains: T-rank's *integrated ownership*, with a company's own shares given
back to its other holders. A person above 25% is a calculated beneficial owner. Two
other readings are reported as sensitivities:

| Reading | Rule |
|---|---|
| integrated, more than 25% | the headline |
| integrated, 25% or more | the EU AML Regulation (2024/1624) from 10 July 2027 |
| majority control | more than 25% directly, or through a company the person controls by a majority, followed up the chain |

**Declared owners.** Every interest the register flags as beneficial ownership.

**Matching people.** By the register's person hash; failing that, by exact name within
the one company (case, accents, hyphens, spacing, and the securities register's
"Omanikukonto:" owner-account prefix aside). Hash-only figures are reported too.

**Classes** (T-rank's four, for comparability): the same people · the register names
someone the shares do not · the shares show someone the register does not name · both
ways. Three cases are left out of the comparison: no declared beneficial owner at all,
shareholdings that add up to more than 100% (below), and companies where a holding of more than 25% passes to a company whose shareholders are
not in the dataset (a foreign company, or an Estonian company without an LEI).

## Caveats

- **Population.** Estonian LEI holders only (about 23,000 of the register's companies),
  which leans towards companies that trade, borrow or invest. Public limited companies
  (AS) keep their shareholder lists at Nasdaq CSD, not in the e-Business Register, so
  almost every company compared is a private limited company (OÜ).
- **One date.** Both lists are as the register published them on 4 July 2026.
- **Shares only.** Control by other means (agreements, family, voting arrangements) is
  not in a shareholder list; some of the register's "extra" people will be right.
- **The reading of the law is mine,** and so is the reading of "controls"; the three
  rules above show how much it matters.
- **Shares that do not add up.** 235 companies' shareholdings total more than 100.5%,
  most often exactly 200% or 300%: a co-owned holding listed in full against each
  co-owner. They cannot be read as stakes, so the 231 of them with a declared owner are
  left out of the comparison.
- **Person data.** The outputs carry company names and registry codes but no person names.
