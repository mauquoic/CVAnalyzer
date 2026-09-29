#!/usr/bin/env python3
"""Check a run's CV assessments against the CV texts ("evidence or no credit").

For every assessable person in .work/manifest.json it checks that:
  - an assessment file exists in <run>/assessments/<key>.json
  - it covers every requirement in <run>/request.json, with a valid state
  - every "met" or "partly met" has at least one quote that really appears in the CV text

With --fix, quotes that can't be found are removed, and a requirement left without a
verified quote is downgraded to "not evidenced" with a note. Missing assessment files
are never fixed automatically.

Usage: python3 tools/verify_evidence.py <run-dir> [--fix]
Exit code 0 when everything checks out (after fixing), 1 otherwise.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import WORK, normalise, quote_in_text, read_json, write_json  # noqa: E402

STATES = {"met", "partly met", "not evidenced"}
UNVERIFIED_NOTE = "Evidence could not be verified against the CV text; downgraded."


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run", type=Path)
    ap.add_argument("--fix", action="store_true")
    args = ap.parse_args()

    request = read_json(args.run / "request.json")
    req_ids = [r["id"] for role in request["roles"] for r in role["requirements"]]
    manifest = read_json(WORK / "manifest.json")
    people = [p for p in manifest["people"] if p["status"] == "ok"]

    missing, errors, fixed = [], [], []
    for p in people:
        path = args.run / "assessments" / f"{p['key']}.json"
        if not path.exists():
            missing.append(p["name"] or p["key"])
            continue
        a = read_json(path)
        norm_cv = normalise((WORK / "cvs" / f"{p['key']}.txt").read_text(encoding="utf-8"))
        by_id = {r.get("id"): r for r in a.get("requirements", [])}
        who = p["name"] or p["key"]
        for rid in req_ids:
            if rid not in by_id:
                errors.append(f"{who}: requirement {rid} not assessed")
        changed = False
        for r in a.get("requirements", []):
            rid, state = r.get("id"), r.get("state")
            if rid not in req_ids:
                errors.append(f"{who}: unknown requirement id {rid}")
                continue
            if state not in STATES:
                errors.append(f"{who} {rid}: invalid state {state!r}")
                continue
            if state == "not evidenced":
                continue
            ev = r.get("evidence") or []
            good = [e for e in ev if (e.get("quote") or "").strip() and quote_in_text(e["quote"], norm_cv)]
            bad = [e.get("quote", "") for e in ev if e not in good]
            if bad and args.fix:
                r["evidence"] = good
                changed = True
            if not good:
                if args.fix:
                    r["state"] = "not evidenced"
                    r["note"] = ((r.get("note") or "") + " " + UNVERIFIED_NOTE).strip()
                    changed = True
                    fixed.append(f"{who} {rid}: downgraded to not evidenced")
                else:
                    errors.append(f"{who} {rid}: '{state}' without a quote found in the CV "
                                  + (f"(not found: {bad[0][:80]!r})" if bad else "(no quote given)"))
            elif bad:
                if args.fix:
                    fixed.append(f"{who} {rid}: removed {len(bad)} unverifiable quote(s)")
                else:
                    errors.append(f"{who} {rid}: quote not found in CV: {bad[0][:80]!r}")
        if changed:
            write_json(path, a)

    print(f"Assessed: {len(people) - len(missing)}/{len(people)} · problems: {len(errors)} · fixed: {len(fixed)}")
    for m in missing:
        print(f"Missing assessment: {m}")
    for e in errors:
        print(f"Problem: {e}")
    for f in fixed:
        print(f"Fixed: {f}")
    return 0 if not missing and not errors else 1


if __name__ == "__main__":
    sys.exit(main())
