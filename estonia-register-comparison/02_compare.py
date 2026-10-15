"""Step 2 — the beneficial owners the shareholder lists imply, against the
beneficial owners each company has declared to the register.

Estonia's definition (Money Laundering and Terrorist Financing Prevention Act,
RahaPTS § 9): a beneficial owner is the natural person who ultimately owns or
controls the company. Direct ownership is a holding of MORE THAN 25%; indirect
ownership is a holding of more than 25% by a company the person controls.
Where no person qualifies, the management board is recorded instead.

The shareholder lists are read three ways, per company:

  integrated  T-Rank's integrated ownership (OpenCheck's ownership_math):
              stakes multiplied along each chain and added across chains;
              a person qualifies above 25% (Estonia's threshold). THE HEADLINE.
  amlr        the same arithmetic at 25% OR MORE — the EU AML Regulation
              (2024/1624), which applies from 10 July 2027.
  majority    a strict reading of "a company the person controls": a person
              qualifies by holding more than 25% directly, or by controlling,
              by a majority of shares followed up the chain, a company that
              holds more than 25%.

A company is INCOMPLETE under a rule when a company the dataset holds no
shareholders for (a foreign company, or an Estonian company without an LEI)
could carry a qualifying stake: under `integrated`/`amlr`, when its own
integrated stake meets the threshold; under `majority`, when it sits on a
chain of more-than-25% / majority links.

People are compared by the register's person hash and, failing that, by exact
name within the one company (see same_person_sets).

Outputs: results/company_outcomes.csv, results/summary.json
"""
import csv, gzip, json, os, unicodedata
from collections import Counter, defaultdict

from ownership_math import Edge, integrated_ownership

HERE = os.path.dirname(os.path.abspath(__file__))
T = json.load(gzip.open(os.path.join(HERE, "tables.json.gz"), "rt", encoding="utf-8"))
companies, people, eparty = T["companies"], T["people"], T["entity_parties"]

# company -> {owner: pct}. One owner can hold several participations (osad) in
# one company; the register lists each, and they add up.
holders = defaultdict(dict)
for o, c, pct, _ in T["holdings"]:
    holders[c][o] = holders[c].get(o, 0.0) + pct
declared = defaultdict(set); declared_kind = defaultdict(dict)
for p, c, typ, label, _ in T["declared"]:
    declared[c].add(p); declared_kind[c][p] = label or "(control type not stated)"
board = defaultdict(set)
for p, c, _ in T["officers"]: board[c].add(p)

EPS = 1e-9


def known(c):
    """Does the dataset hold this company's shareholders?"""
    return bool(holders.get(c))


def is_company(o): return o.startswith("e:")


# --- integrated ownership (integrated / amlr) --------------------------------
def integrated(c):
    """{owner: integrated % of c} for every person and company above c, using
    every chain the dataset holds."""
    sub, stack, seen = [], [c], {c}
    while stack:
        n = stack.pop()
        for o, pct in holders.get(n, {}).items():
            # Every company is keyed "e:<rid>" on both sides, the target too, so
            # a company holding its own shares is a self-edge and its shares are
            # given back to its other holders (ownership_math's normalisation).
            sub.append(Edge(o, "e:" + n, pct / 100, pct / 100))
            if is_company(o) and o[2:] not in seen: seen.add(o[2:]); stack.append(o[2:])
    target = "e:" + c
    out = {}
    for o in {e.owner for e in sub}:
        if o == target: continue                        # the company's own shares
        r = integrated_ownership(sub, {o}, target)
        out[o] = r.minimum if r.minimum is not None else None
    return out


def by_integrated(stakes, threshold, inclusive):
    ok = (lambda v: v >= threshold - EPS) if inclusive else (lambda v: v > threshold + EPS)
    bos = {o for o, v in stakes.items() if v is not None and not is_company(o) and ok(v)}
    unknown = {o for o, v in stakes.items() if is_company(o) and not known(o[2:]) and v is not None and ok(v)}
    unsettled = any(v is None for v in stakes.values())
    return bos, not unknown and not unsettled, unknown


# --- majority control (majority) ----------------------------------------------
_ctrl = {}
def controllers(c, seen=()):
    """People who control company c by a majority of shares, up the chain."""
    if c in _ctrl: return _ctrl[c]
    if c in seen or not known(c): return set(), False, ({c} if not known(c) else set())
    out, complete, unknown = set(), True, set()
    for o, pct in holders[c].items():
        if pct <= 50 + EPS: continue
        if not is_company(o): out.add(o)
        else:
            s, ok, u = controllers(o[2:], seen + (c,)); out |= s; complete &= ok; unknown |= u
    _ctrl[c] = (out, complete, unknown)
    return _ctrl[c]


def by_majority(c):
    out, complete, unknown = set(), True, set()
    for o, pct in holders[c].items():
        if pct <= 25 + EPS: continue
        if not is_company(o): out.add(o)
        else:
            s, ok, u = controllers(o[2:], (c,)); out |= s; complete &= ok; unknown |= u
    return out, complete, {"e:" + u for u in unknown}


# --- comparing people ---------------------------------------------------------
ACCOUNT_PREFIXES = ("Omanikukonto:", "Lihtkonto:")   # owner / simple account at the securities register


def name_key(p):
    n = (people.get(p) or {}).get("name") or p
    for pre in ACCOUNT_PREFIXES:
        if n.startswith(pre): n = n[len(pre):]
    n = unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode()
    return " ".join(n.casefold().replace("-", " ").split())


def same_person_sets(calc, decl, strict=False):
    """Two rows are one person when they carry the same register hash or —
    unless strict — the same name within the one company (case, accents,
    hyphens and spacing aside, and the securities register's "Omanikukonto:"
    account prefix removed). The register gives a foreign shareholder no hash
    on the shareholder row while it hashes the same person on the
    beneficial-owner row, and an owner-account row carries its own hash."""
    if strict: return set(calc), set(decl)
    canon, parent = {}, {}
    def find(x):
        while parent.setdefault(x, x) != x: x = parent[x]
        return x
    for p in sorted(calc | decl):
        k = name_key(p)
        if k in canon: parent[find(p)] = find(canon[k])
        else: canon[k] = p
    return {find(p) for p in calc}, {find(p) for p in decl}


def outcome(calc, decl, complete, strict=False, over_100=False):
    """T-Rank's four classes for Norway (match; in the calculation but missing
    from the register; in the register but not in the calculation; both ways),
    plus the two cases where no comparison is possible."""
    calc, decl = same_person_sets(calc, decl, strict)
    if not decl: return "no_declared_bo", calc, decl
    # Shares listed against each co-owner in full (200%, 300% …) cannot be read
    # as stakes; such companies are left out of the comparison.
    if over_100: return "shares_over_100", calc, decl
    if not complete: return "incomplete", calc, decl
    if calc == decl: return "same_people", calc, decl
    if decl < calc: return "register_misses_someone", calc, decl
    if calc < decl: return "register_adds_someone", calc, decl
    return "both_ways", calc, decl


def unknown_kind(unknown):
    kinds = {"estonian_no_lei" if eparty.get(o, {}).get("jurisdiction") == "EE" else "foreign" for o in unknown}
    return "+".join(sorted(kinds))


rows, diffs = [], []
for c, info in companies.items():
    if not known(c): continue        # no shareholder list in the register (AS, MTÜ, SA, UÜ, TÜ …)
    decl = declared[c]
    stakes = integrated(c)
    i_bos, i_ok, i_unk = by_integrated(stakes, 25, inclusive=False)
    a_bos, a_ok, a_unk = by_integrated(stakes, 25, inclusive=True)
    m_bos, m_ok, m_unk = by_majority(c)
    over = sum(holders[c].values()) > 100.5
    o_i, ci, di = outcome(i_bos, decl, i_ok, over_100=over)
    o_h, _, _ = outcome(i_bos, decl, i_ok, strict=True, over_100=over)
    o_a, _, _ = outcome(a_bos, decl, a_ok, over_100=over)
    o_m, _, _ = outcome(m_bos, decl, m_ok, over_100=over)
    # Declared people who are on the board and hold no shares themselves —
    # the register's fallback when nobody owns enough.
    board_only = bool(decl) and all(p in board[c] and p not in holders[c] for p in decl)
    direct_people = {o for o, v in holders[c].items() if not is_company(o)}
    if o_i in ("register_misses_someone", "register_adds_someone", "both_ways"):
        # One row per person on one side only — no names, only what explains it.
        by_name = defaultdict(list)
        for x in set(stakes) | decl: by_name[name_key(x)].append(x)
        for side, group in (("calculated_only", ci - di), ("declared_only", di - ci)):
            for p in group:
                rowsof = by_name[name_key(p)]
                stake = max((stakes.get(x) or 0.0) for x in rowsof)
                direct = max((holders[c].get(x) or 0.0) for x in rowsof)
                diffs.append({
                    "registry_code": info["code"], "outcome": o_i, "side": side,
                    "integrated_stake": round(stake, 4), "direct_stake": round(direct, 4),
                    "is_board": int(any(x in board[c] for x in rowsof)),
                    "declared_type": next((declared_kind[c][x] for x in rowsof if x in declared_kind[c]), ""),
                    "nobody_over_threshold": int(not ci),
                    "stake_band": ("none" if stake == 0 else "exactly 25%" if abs(stake - 25) < EPS
                                   else "under 25%" if stake < 25 else "over 25%"),
                })
    rows.append({
        "company": info["name"], "registry_code": info["code"],
        "outcome": o_i, "outcome_hash_only": o_h, "outcome_amlr": o_a, "outcome_majority": o_m,
        "shareholders": len(holders[c]), "company_shareholders": sum(1 for x in holders[c] if is_company(x)),
        "declared": len(di), "calculated": len(ci), "calculated_amlr": len(a_bos), "calculated_majority": len(m_bos),
        "declared_not_calculated": len(di - ci), "calculated_not_declared": len(ci - di),
        "declared_board_only": int(board_only),
        "nobody_over_threshold": int(not ci),
        "declared_types": "; ".join(sorted({declared_kind[c][p] for p in decl})),
        "has_company_shareholder_over_25": int(any(is_company(o) and v > 25 + EPS for o, v in holders[c].items())),
        "holder_at_exactly_25": int(any(abs(v - 25) < EPS for v in stakes.values() if v is not None)),
        "largest_person_stake": round(max([v for o, v in stakes.items() if not is_company(o) and v is not None] or [0]), 4),
        "unknown_holder_kind": unknown_kind(i_unk) if not i_ok else "",
        "declared_not_shareholders": sum(1 for p in decl if p not in direct_people and name_key(p) not in {name_key(x) for x in direct_people}),
        "share_total": round(sum(holders[c].values()), 2),
    })

rows.sort(key=lambda r: (r["outcome"], r["registry_code"] or ""))
with open(os.path.join(HERE, "results", "company_outcomes.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


with open(os.path.join(HERE, "results", "person_differences.csv"), "w", newline="", encoding="utf-8") as f:
    # Sorted on every column, so a re-run writes the same file (people within a
    # company come out of a set, in no fixed order).
    diffs.sort(key=lambda d: tuple(str(d[k]) for k in d))
    w = csv.DictWriter(f, fieldnames=list(diffs[0])); w.writeheader(); w.writerows(diffs)


def tally(key): return dict(Counter(r[key] for r in rows).most_common())


summary = {
    "companies_in_dataset": len(companies),
    "companies_with_shareholder_list": len(rows),
    "outcomes": {"integrated_over_25": tally("outcome"), "integrated_over_25_hash_only": tally("outcome_hash_only"),
                 "amlr_25_or_more": tally("outcome_amlr"), "majority_control": tally("outcome_majority")},
    "companies_with_company_shareholder_over_25": sum(r["has_company_shareholder_over_25"] for r in rows),
    "share_total_not_100": sum(1 for r in rows if abs(r["share_total"] - 100) > 0.5),
}
json.dump(summary, open(os.path.join(HERE, "results", "summary.json"), "w"), indent=1)
print(json.dumps(summary, indent=1))
