#!/usr/bin/env python3
"""Rank candidates per role from a run's verified assessments and propose a team.

Ranking rules (docs/guardrails.md):
  - Points per requirement: met = 1, partly met = 0.5, not evidenced = 0.
  - Tiers, in order:
      full           all key requirements met, including languages
      language_gap   all key skills met, a required language not met (shown, flagged for the requester)
      partial        at least half of the key-skill points
      weak           below that; listed, never proposed
  - Within a tier: key-skill points, then language points, nice-to-have points, baseline points.
  - Seniority is never used. Availability only matters when request.json says it's required.
    With a needed_from date, the team list's "available from" date decides (later = unavailable).
    Without one, 0 % free means unavailable. Below min_availability_pct is unavailable.
    Unknown availability is kept and flagged.
  - Gaps are counted among the people who can be proposed, and mention how many unavailable
    people would have met the requirement.
  - Team proposal: roles in request order, each takes its best not-yet-proposed people from the
    full, language_gap and partial tiers. Unfilled positions are reported as open.

Usage: python3 tools/rank.py <run-dir> [--top N]
Writes <run-dir>/ranking.json and prints a summary.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import WORK, read_json, write_json  # noqa: E402

POINTS = {"met": 1.0, "partly met": 0.5, "not evidenced": 0.0}
TIERS = ["full", "language_gap", "partial", "weak"]


def score(reqs: list[dict], states: dict[str, str]) -> tuple[float, int, int]:
    """(points, fully met count, total) for a list of requirements."""
    pts = sum(POINTS.get(states.get(r["id"], "not evidenced"), 0) for r in reqs)
    met = sum(states.get(r["id"]) == "met" for r in reqs)
    return pts, met, len(reqs)


def availability_status(p: dict, request: dict) -> tuple[str, str | None]:
    if not request.get("availability_required"):
        return "not required", None
    pct, frm = p.get("availability_pct"), p.get("available_from")
    need_from, min_pct = request.get("needed_from"), request.get("min_availability_pct")
    if pct is None and not frm:
        return "unknown", f"Availability unknown ({p.get('availability_raw') or 'no entry'})"
    if frm and need_from:
        # The team list's "available from" date decides; the percentage is today's value.
        if frm > need_from:
            return "unavailable", f"Available from {frm}, needed from {need_from}"
        if pct == 0:
            return "available", None  # booked today, free by the start date
    elif pct == 0:
        return "unavailable", f"Staffed, available from {frm}" if frm else "0 % available"
    if pct is not None and min_pct is not None and 0 < pct < min_pct:
        return "unavailable", f"{pct:g} % available, {min_pct:g} % needed"
    return "available", None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run", type=Path)
    ap.add_argument("--top", type=int, default=5, help="shortlist length per role (at least the number of positions)")
    args = ap.parse_args()

    request = read_json(args.run / "request.json")
    manifest = read_json(WORK / "manifest.json")
    people = manifest["people"]

    assessments = {}
    for p in people:
        path = args.run / "assessments" / f"{p['key']}.json"
        if p["status"] == "ok" and path.exists():
            a = read_json(path)
            assessments[p["key"]] = {r["id"]: r.get("state") for r in a.get("requirements", [])}

    not_assessed = [{"key": p["key"], "name": p["name"], "reason": p["problem"] or "Assessment missing"}
                    for p in people if p["key"] not in assessments]

    unavailable, proposed_keys, roles_out = {}, set(), []
    for role in request["roles"]:
        reqs = role["requirements"]
        key_core = [r for r in reqs if r["class"] == "key" and r.get("kind") != "language"]
        key_lang = [r for r in reqs if r["class"] == "key" and r.get("kind") == "language"]
        nice = [r for r in reqs if r["class"] == "nice"]
        base = [r for r in reqs if r["class"] == "baseline"]

        rows = []
        for p in people:
            states = assessments.get(p["key"])
            if states is None:
                continue
            k_pts, k_met, k_tot = score(key_core, states)
            l_pts, l_met, l_tot = score(key_lang, states)
            n_pts, n_met, n_tot = score(nice, states)
            b_pts, b_met, b_tot = score(base, states)
            if k_met == k_tot and l_met == l_tot:
                tier = "full"
            elif k_met == k_tot:
                tier = "language_gap"
            elif k_tot == 0 or k_pts >= k_tot / 2:
                tier = "partial"
            else:
                tier = "weak"
            av, av_note = availability_status(p, request)
            flags = []
            if tier == "language_gap":
                missing = [r["text"] for r in key_lang if states.get(r["id"]) != "met"]
                flags.append(f"Language may be an issue ({', '.join(missing)}): discuss with the requester")
            if p.get("outdated"):
                flags.append(f"CV may be outdated ({p['cv_date']})")
            if p["status"] == "ok" and not p.get("cv_date"):
                flags.append("CV date unknown")
            if (p.get("link") or "").startswith("probable"):
                flags.append("CV linked by a probable name match; confirm")
            if av == "unknown":
                flags.append(av_note)
            row = {"key": p["key"], "name": p["name"], "tier": tier,
                   "key_points": k_pts, "key_met": k_met, "key_total": k_tot,
                   "language_met": l_met, "language_total": l_tot,
                   "nice_points": n_pts, "nice_met": n_met, "nice_total": n_tot,
                   "baseline_points": b_pts, "baseline_total": b_tot,
                   "availability": av, "availability_pct": p.get("availability_pct"),
                   "available_from": p.get("available_from"), "flags": flags}
            if av == "unavailable":
                unavailable[p["key"]] = {"key": p["key"], "name": p["name"], "reason": av_note}
                continue
            rows.append(row)

        rows.sort(key=lambda r: (TIERS.index(r["tier"]), -r["key_points"], -r["language_met"],
                                 -r["nice_points"], -r["baseline_points"], (r["name"] or r["key"]).lower()))
        for i, r in enumerate(rows, 1):
            r["rank"] = i

        positions = int(role.get("positions") or 1)
        proposed = []
        for r in rows:
            if len(proposed) == positions:
                break
            if r["tier"] != "weak" and r["key"] not in proposed_keys:
                proposed.append(r["key"])
                proposed_keys.add(r["key"])

        # Gaps count the people who can actually be proposed (available ones, when availability matters).
        candidates = {r["key"] for r in rows}
        gaps = []
        for q in reqs:
            if q["class"] == "baseline":
                continue
            n = sum(assessments[k].get(q["id"]) == "met" for k in candidates)
            n_all = sum(states.get(q["id"]) == "met" for states in assessments.values())
            extra = f" ({n_all - n} more among unavailable people)" if n_all > n else ""
            if n == 0:
                gaps.append({"id": q["id"], "text": q["text"], "class": q["class"], "met_by": 0, "met_by_all": n_all,
                             "note": ("Nobody available meets this" if request.get("availability_required") else "Nobody meets this") + extra})
            elif q["class"] == "key" and n < positions:
                gaps.append({"id": q["id"], "text": q["text"], "class": q["class"], "met_by": n, "met_by_all": n_all,
                             "note": f"Only {n} of the candidates meet this, {positions} positions" + extra})

        roles_out.append({"id": role["id"], "title": role.get("title"), "positions": positions,
                          "shortlist": rows[:max(args.top, positions)], "all_ranked": rows,
                          "proposed": proposed, "open_positions": positions - len(proposed),
                          "tier_counts": {t: sum(r["tier"] == t for r in rows) for t in TIERS},
                          "gaps": gaps})

    out = {"run": str(args.run), "roles": roles_out, "unavailable": list(unavailable.values()),
           "not_assessed": not_assessed, "assessed": len(assessments), "team_size": len(people)}
    write_json(args.run / "ranking.json", out)

    print(f"Assessed {len(assessments)} of {len(people)} · not assessed: {len(not_assessed)} · unavailable: {len(unavailable)}")
    for r in roles_out:
        names = {x["key"]: x["name"] or x["key"] for x in r["all_ranked"]}
        print(f"\n{r['title'] or r['id']}: {r['positions']} position(s) · tiers {r['tier_counts']} · open: {r['open_positions']}")
        for x in r["shortlist"]:
            mark = "*" if x["key"] in r["proposed"] else " "
            print(f" {mark}{x['rank']:>3}. {names[x['key']]:<30} {x['tier']:<13} key {x['key_met']}/{x['key_total']} "
                  f"lang {x['language_met']}/{x['language_total']} nice {x['nice_met']}/{x['nice_total']}"
                  + (f"  [{'; '.join(x['flags'])}]" if x["flags"] else ""))
        for g in r["gaps"]:
            print(f"   Gap: {g['text']}: {g['note']}")
    print(f"\nRanking: {args.run / 'ranking.json'}  (* = proposed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
