# MEIP's UK subsidiaries vs the UK register of people with significant control

Question: MEIP marks 84% of its 15,678 UK subsidiaries "Unknown" (no public source gave it a
parent). Does the UK PSC register link them to their MEIP group, and to its head?

Headline, for subsidiaries that existed on 31 Dec 2024: of 10,459 "Unknown" rows, the PSC chain
reaches the MEIP group for 9,589 (91.7%) and the head MEIP records for 7,244 (69.3%).

## Run order (from this folder)

| Step | Script | Output |
|---|---|---|
| 1 | `../meip-global/01_export_meip_rows.py` then copy `meip_rows.jsonl.gz` here | MEIP rows |
| 2a | `02a_load_basic_company_data.py` | `basic_company_data.sqlite` (live companies, 1 Sep 2026) |
| 2b | `02b_build_subjects.py` | `subjects.jsonl` (UK rows + company numbers), `group_index.json` |
| 3 | `03_walk_and_classify.py` | `results.jsonl`: PSC walk + outcome per subject (needs `psc_graph.sqlite`) |
| 4 | `04_summarise.py` | tables on all rows (`results/summary.txt`) |
| 5 | `05_live_register_check.py` | store vs live Companies House pages (`results/live_register_check.txt`) |
| 6 | `06_dissolution_dates.py` | `dissolution.jsonl`. **Slow (about an hour, it reads public web pages): copy `results/dissolution.jsonl` here instead to skip it** |
| 7 | `07_per_group.py` | `results/per_group.csv` |
| 8 | `08_vintage.py` | `results_with_vintage.jsonl` + `results/vintage_summary.txt` (status at 31 Dec 2024) |
| 9 | `09_alias_sensitivity.py` | sensitivity run with `aliases.json` (renamed heads); see its docstring for the env vars |
| 10 | `10_natures_of_control.py` | `results/natures_of_control.txt` |
| 11 | `11_post_figures.py` | `results/uk_*.csv`, `results/uk_summary.json` (the post's charts) |

Every script's docstring states its rules. `common.py` holds the Companies House number
normaliser (the same rule OpenCheck uses) and the name keys used for matching.

## Method in brief
- Company numbers: the OpenCorporates id (`gb/<n>`) and every `GBBR:<n>` in Business ID.
- Walk: breadth-first up **active** corporate and legal-person PSCs that carry a UK registration
  number; depth cap 12; cycles walked once.
- Matching a PSC to a group, strongest first: UK company number → strict name key (legal forms
  folded, initialisms re-joined, German umlauts also transliterated) → loose name key (legal-form
  words dropped; only keys of 5+ characters with a non-generic word).
- Outcomes: `no_uk_number`, `no_psc_dissolved`, `no_psc_live`, `reaches_group`,
  `reaches_other_group`, `individuals_only`, `unmatched_corporate`.
- Base for the post: subjects live on 1 Sep 2026 or dissolved after 31 Dec 2024.

## Checks
- 40 random subjects: store PSC names = live register PSC names, 40/40.
- 30 random matches and all 65 loose name matches read by hand.
- Aliases (`aliases.json`) are a separate sensitivity run; the headline never uses them.
  Headline run reproduced byte-for-byte with and without the alias code.

## Caveats
Active PSCs only, and no PSC statements, so "no PSC" is not "no owner". PSC data is Sept 2026;
MEIP is 31 Dec 2024. About 4% of MEIP groups have a head row that isn't the listed parent.
PSC thresholds (25%+) differ from MEIP's >50% control test; 96.3% of first links are majority.
