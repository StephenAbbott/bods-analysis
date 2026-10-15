"""Step 1 — read the OpenCheck Estonia BODS dataset into plain tables.

Input: estonia-2026-07-04.jsonl.gz from the OpenCheck release
`dataset-estonia-2026-07-04` (github.com/StephenAbbott/opencheck/releases).
Output: tables.json.gz in this folder (not committed) and results/inputs.json.

The dataset joins two layers on the Estonian registry code:
  * the e-Business Register (RIK bulk open data, downloaded 4 July 2026) —
    shareholders (osanikud) with their percentage, officers, and declared
    beneficial owners (kasusaajad) with the register's control code;
  * GLEIF (Open Ownership's gleif_version_0_4, statements to 9 Feb 2025) —
    LEI records, group links and reporting exceptions.

People are keyed on the register's person hash (EE-ARIREGISTER-HASH) when a
statement carries one — the same hash on a shareholder row and a
beneficial-owner row is the same person — and on the statement's recordId
otherwise (foreign people the register lists without an Estonian ID).

Usage: python3 01_load.py /path/to/estonia-2026-07-04.jsonl.gz
"""
import gzip, hashlib, json, os, sys
from collections import Counter

RIK = "Estonian e-Business Register (e-Äriregister)"
HERE = os.path.dirname(os.path.abspath(__file__))


def main(path):
    ents, pers, rels = {}, {}, []
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            s = json.loads(line)
            t = s["recordType"]
            if t == "entity": ents[s["recordId"]] = s
            elif t == "person": pers[s["recordId"]] = s
            else: rels.append(s)

    def person_key(rid):
        p = pers[rid]
        for i in p["recordDetails"].get("identifiers") or []:
            if i.get("scheme") == "EE-ARIREGISTER-HASH": return "h:" + i["id"]
        return "r:" + rid

    def party(rid):
        if rid in pers: return person_key(rid)
        if rid in ents: return "e:" + rid
        return None

    def is_rik(s): return (s.get("source") or {}).get("description") == RIK

    companies = {}          # subject recordId -> {name, code, founded}
    holdings = []           # [owner, company, pct, startDate]
    declared = []           # [person, company, interest type, control label or "", startDate]
    officers = []           # [person, company, role]
    counts = Counter()
    for r in rels:
        if not is_rik(r): continue
        d = r["recordDetails"]; subj = d["subject"]; ip = party(d["interestedParty"]) if isinstance(d["interestedParty"], str) else None
        if subj not in ents or ip is None:
            counts["dropped_unresolved"] += 1; continue
        companies.setdefault(subj, None)
        for i in d["interests"]:
            if i.get("endDate"): counts["ended_interest"] += 1; continue
            if i.get("beneficialOwnershipOrControl"):
                declared.append([ip, subj, i["type"], i.get("details") or "", i.get("startDate")]); counts["declared"] += 1
            elif i["type"] == "shareholding":
                if "share" in i:
                    holdings.append([ip, subj, float(i["share"]["exact"]), i.get("startDate")]); counts["holding_with_share"] += 1
                else: counts["holding_without_share"] += 1
            elif i["type"] in ("boardMember", "seniorManagingOfficial"):
                officers.append([ip, subj, i.get("details") or i["type"]]); counts["officer"] += 1
            else: counts["other_" + i["type"]] += 1

    for rid in list(companies):
        rd = ents[rid]["recordDetails"]
        code = next((i["id"] for i in rd.get("identifiers") or [] if i.get("scheme") in ("EE-KMKR", "EE-ARIREGISTER") and i["id"].isdigit()), None)
        companies[rid] = {"name": rd.get("name"), "code": code, "founded": rd.get("foundingDate")}

    entity_parties = {}     # e:<rid> -> {name, jurisdiction, code, in_scope}
    for o, c, _, _ in holdings:
        if o.startswith("e:"):
            rid = o[2:]; rd = ents[rid]["recordDetails"]
            code = next((i["id"] for i in rd.get("identifiers") or [] if i.get("scheme") in ("EE-KMKR", "EE-ARIREGISTER") and i["id"].isdigit()), None)
            entity_parties[o] = {"name": rd.get("name"), "jurisdiction": (rd.get("jurisdiction") or {}).get("code"),
                                 "code": code, "in_scope": rid in companies}

    people = {}
    for rid in pers:
        k = person_key(rid)
        if k not in people:
            n = pers[rid]["recordDetails"].get("names") or [{}]
            people[k] = {"name": n[0].get("fullName"), "estonian_id": k.startswith("h:")}

    # GLEIF reporting exceptions on the Estonian LEIs, and the LEI -> company join.
    lei_of = {}
    for e in ents.values():
        ids = e["recordDetails"].get("identifiers") or []
        lei = next((i["id"] for i in ids if i.get("scheme") == "XI-LEI"), None)
        code = next((i["id"] for i in ids if i.get("scheme") == "EE-KMKR" and i["id"].isdigit()), None)
        if lei and code: lei_of.setdefault(code, lei)
    exceptions = Counter(); natural_person_leis = []
    for r in rels:
        if is_rik(r): continue
        ip = r["recordDetails"]["interestedParty"]
        if isinstance(ip, dict):
            det = " ".join(i.get("details") or "" for i in r["recordDetails"]["interests"])
            reason = (ip.get("description") or "").split(".")[0].replace("Exception Reason: ", "")
            exceptions[(reason, det.replace("Exception Category: ", ""))] += 1
            if reason == "NATURAL_PERSONS":
                natural_person_leis.append([r["recordDetails"]["subject"].replace("XI-LEI-", ""), det.replace("Exception Category: ", "")])

    sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
    out = {"companies": companies, "holdings": holdings, "declared": declared, "officers": officers,
           "entity_parties": entity_parties, "people": people, "lei_of_code": lei_of,
           "natural_person_exceptions": natural_person_leis}
    with gzip.open(os.path.join(HERE, "tables.json.gz"), "wt", encoding="utf-8") as f: json.dump(out, f)
    inputs = {"file": os.path.basename(path), "sha256": sha, "statements": len(ents) + len(pers) + len(rels),
              "rik_companies_with_rows": len(companies), "people": len(people),
              "lei_with_registry_code": len(lei_of), "counts": dict(counts),
              "gleif_exceptions": {f"{a} | {b}": n for (a, b), n in exceptions.most_common()}}
    json.dump(inputs, open(os.path.join(HERE, "results", "inputs.json"), "w"), indent=1, ensure_ascii=False)
    print(json.dumps(inputs, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1])
