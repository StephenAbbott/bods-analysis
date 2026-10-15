"""Step 3 — every number the post quotes, from the step 2 outputs.

Outputs (results/): funnel.csv, outcomes.csv, declared_only.csv,
calculated_only.csv, trank_comparison.csv, post_figures.json
"""
import csv, json, os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "results")
rows = list(csv.DictReader(open(os.path.join(R, "company_outcomes.csv"), encoding="utf-8")))
diffs = list(csv.DictReader(open(os.path.join(R, "person_differences.csv"), encoding="utf-8")))
inputs = json.load(open(os.path.join(R, "inputs.json"), encoding="utf-8"))
summary = json.load(open(os.path.join(R, "summary.json"), encoding="utf-8"))

CLASSES = ["same_people", "register_adds_someone", "register_misses_someone", "both_ways"]
LABEL = {"same_people": "Same people", "register_adds_someone": "Register names someone the shares do not",
         "register_misses_someone": "Shares show someone the register does not name",
         "both_ways": "Differences both ways"}


def pct(a, b): return round(100 * a / b, 1) if b else 0.0
def w(name, header, data):
    with open(os.path.join(R, name), "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f); wr.writerow(header); wr.writerows(data)


oc = Counter(r["outcome"] for r in rows)
comparable = sum(oc[k] for k in CLASSES)

# The funnel: from the dataset to the companies that can be compared.
funnel = [
    ("Estonian LEI holders with a registry code", inputs.get("lei_with_registry_code", 23310)),
    ("found in the e-Business Register", summary["companies_in_dataset"]),
    ("with a shareholder list giving percentages", summary["companies_with_shareholder_list"]),
    ("with at least one declared beneficial owner", summary["companies_with_shareholder_list"] - oc["no_declared_bo"]),
    ("whose shareholdings add up to no more than 100%", summary["companies_with_shareholder_list"] - oc["no_declared_bo"] - oc["shares_over_100"]),
    ("whose ownership chains stay inside the dataset", comparable),
]
w("funnel.csv", ["step", "companies"], funnel)

# The four classes under each reading of the shares.
out = []
for rule, key in (("integrated, more than 25%", "outcome"), ("integrated, 25% or more (AMLR)", "outcome_amlr"),
                  ("majority control, more than 25%", "outcome_majority"), ("integrated, more than 25%, hash only", "outcome_hash_only")):
    c = Counter(r[key] for r in rows); n = sum(c[k] for k in CLASSES)
    for k in CLASSES: out.append((rule, k, LABEL[k], c[k], pct(c[k], n)))
    out.append((rule, "comparable", "Comparable companies", n, 100.0))
w("outcomes.csv", ["rule", "class", "label", "companies", "pct_of_comparable"], out)

# Who the register names that the shares do not.
dec = [d for d in diffs if d["side"] == "declared_only"]
def dec_reason(d):
    band, board = d["stake_band"], d["is_board"] == "1"
    if band == "exactly 25%": return "holds exactly 25%"
    if band == "under 25%": return "holds less than 25%"
    if board: return "board member, holds no shares"
    return "neither a shareholder nor on the board"
dr = Counter(dec_reason(d) for d in dec)
order = ["holds exactly 25%", "holds less than 25%", "board member, holds no shares", "neither a shareholder nor on the board"]
w("declared_only.csv", ["reason", "people", "pct"], [(k, dr[k], pct(dr[k], len(dec))) for k in order])

cal = [d for d in diffs if d["side"] == "calculated_only"]
def cal_reason(d):
    direct = float(d["direct_stake"])
    if direct > 25: return "holds more than 25% directly"
    return "holds more than 25% through companies"
cr = Counter(cal_reason(d) for d in cal)
w("calculated_only.csv", ["reason", "people", "pct"], [(k, v, pct(v, len(cal))) for k, v in cr.most_common()])
cal_board = sum(1 for d in cal if d["is_board"] == "1")

# T-Rank's Norway figures (trank.no/news/the-danish-beneficial-ownership-register,
# 18 Sep 2026) beside Estonia's: match / missing from the register / extra in
# the register / both ways.
est = {k: pct(oc[k], comparable) for k in CLASSES}
w("trank_comparison.csv", ["class", "norway_trank_pct", "estonia_pct"], [
    ("Same people", 84, est["same_people"]),
    ("Shares show someone the register does not name", 7, est["register_misses_someone"]),
    ("Register names someone the shares do not", 7, est["register_adds_someone"]),
    ("Differences both ways", 2, est["both_ways"]),
])

amlr = Counter(r["outcome_amlr"] for r in rows)
amlr_comparable = sum(amlr[k] for k in CLASSES)
changed = [r for r in rows if r["calculated"] != r["calculated_amlr"]]
newly_missing = sum(1 for r in rows if r["outcome"] != "register_misses_someone" and r["outcome_amlr"] == "register_misses_someone")
chain = [r for r in rows if r["has_company_shareholder_over_25"] == "1"]
chain_c = Counter(r["outcome"] for r in chain); chain_cmp = sum(chain_c[k] for k in CLASSES)
direct_only = [r for r in rows if r["has_company_shareholder_over_25"] == "0"]
direct_c = Counter(r["outcome"] for r in direct_only); direct_cmp = sum(direct_c[k] for k in CLASSES)
def shape(r):
    if r["has_company_shareholder_over_25"] == "1": return "a company holds more than 25%"
    if r["shareholders"] == "1": return "one shareholder"
    return "several shareholders"
SHAPES = ["one shareholder", "several shareholders", "a company holds more than 25%"]
by_shape = {k: Counter(r["outcome"] for r in rows if shape(r) == k) for k in SHAPES}
w("by_shape.csv", ["shape", "comparable", "same_people", "pct_same"],
  [(k, sum(by_shape[k][c] for c in CLASSES), by_shape[k]["same_people"],
    pct(by_shape[k]["same_people"], sum(by_shape[k][c] for c in CLASSES))) for k in SHAPES])
hashc = Counter(r["outcome_hash_only"] for r in rows)
unk = Counter(r["unknown_holder_kind"] for r in rows if r["outcome"] == "incomplete")
no_decl = [r for r in rows if r["outcome"] == "no_declared_bo"]

figures = {
    "dataset": {"file": inputs["file"], "sha256": inputs["sha256"], "statements": inputs["statements"]},
    "funnel": dict(funnel),
    "comparable": comparable,
    "classes": {k: {"companies": oc[k], "pct": est[k]} for k in CLASSES},
    "not_comparable": {"no_declared_bo": oc["no_declared_bo"],
                       "no_declared_bo_with_a_qualifying_shareholder": sum(1 for r in no_decl if r["calculated"] != "0"),
                       "shares_over_100": oc["shares_over_100"],
                       "incomplete_chain": oc["incomplete"], "incomplete_by_kind": dict(unk.most_common())},
    "declared_only_people": {"total": len(dec), **dict(dr)},
    "calculated_only_people": {"total": len(cal), **dict(cr), "of_whom_board_members": cal_board},
    "nobody_over_25_but_register_names_someone": sum(1 for r in rows if r["outcome"] == "register_adds_someone" and r["nobody_over_threshold"] == "1"),
    "amlr": {"same_people": amlr["same_people"], "comparable": amlr_comparable,
             "same_people_pct": pct(amlr["same_people"], amlr_comparable),
             "companies_whose_calculated_owners_change": len(changed),
             "companies_newly_missing_someone": newly_missing},
    "majority_reading": {k: Counter(r["outcome_majority"] for r in rows)[k] for k in CLASSES},
    "hash_only": {"same_people": hashc["same_people"], "both_ways": hashc["both_ways"],
                  "same_people_pct": pct(hashc["same_people"], sum(hashc[k] for k in CLASSES))},
    "chains": {"companies_with_a_company_shareholder_over_25": len(chain), "comparable": chain_cmp,
               "same_people_pct": pct(chain_c["same_people"], chain_cmp),
               "direct_only_same_people_pct": pct(direct_c["same_people"], direct_cmp)},
    "by_shape": {k: {"comparable": sum(by_shape[k][c] for c in CLASSES), "same_people": by_shape[k]["same_people"],
                     "pct_same": pct(by_shape[k]["same_people"], sum(by_shape[k][c] for c in CLASSES)),
                     **{c: by_shape[k][c] for c in CLASSES if c != "same_people"}} for k in SHAPES},
    "share_total_not_100": summary["share_total_not_100"],
}
json.dump(figures, open(os.path.join(R, "post_figures.json"), "w"), indent=1)
print(json.dumps(figures, indent=1))
