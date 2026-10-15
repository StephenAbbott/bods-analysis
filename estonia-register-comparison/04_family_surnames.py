"""Step 4 — how often a person the register names, but the shares do not,
shares a surname with an owner the shares do point to.

A shared surname is a hint of family, never proof: it is counted, not used to
reclassify anything. Covers the companies in the two classes where the
register names someone extra ("register_adds_someone", "both_ways").

Output: results/family_surnames.json
"""
import contextlib, io, json, os, runpy, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(os.path.join(HERE, "02_compare.py"))
people, declared = g["people"], g["declared"]


def surname(p):
    n = (people.get(p, {}).get("name") or "")
    for pre in g["ACCOUNT_PREFIXES"]:
        n = n.replace(pre, "")
    parts = n.split()
    return parts[-1].casefold() if parts else ""


counts = Counter()
for c in g["companies"]:
    if not g["known"](c) or not declared[c]: continue
    bos, ok, _ = g["by_integrated"](g["integrated"](c), 25, False)
    o, _, _ = g["outcome"](bos, declared[c], ok, over_100=sum(g["holders"][c].values()) > 100.5)
    if o not in ("register_adds_someone", "both_ways"): continue
    calc_keys = {g["name_key"](x) for x in bos}
    extra = [p for p in declared[c] if g["name_key"](p) not in calc_keys]
    shared = bool(bos) and any(surname(e) in {surname(x) for x in bos} for e in extra)
    counts[o + (":shared_surname" if shared else ":other")] += 1
out = dict(sorted(counts.items()))
out["companies"] = sum(counts.values())
out["shared_surname"] = sum(v for k, v in counts.items() if k.endswith("shared_surname"))
json.dump(out, open(os.path.join(HERE, "results", "family_surnames.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
