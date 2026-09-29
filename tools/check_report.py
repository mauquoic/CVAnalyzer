#!/usr/bin/env python3
"""Check a finished match report against the guardrails before it is handed over.

Errors (exit code 1):
  - template placeholders ({{...}}) left in the report
  - a person on the team list who doesn't appear in the report (complete coverage)
  - a proposed person from ranking.json missing from the report
Warnings (review, then fix or keep deliberately):
  - words that point to protected attributes (age, nationality, gender, family status, photo, ...)

Usage: python3 tools/check_report.py <report.md> <run-dir>
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import WORK, name_tokens, read_json  # noqa: E402

PROTECTED = [
    r"age", r"aged", r"years old", r"born", r"date of birth", r"geboren", r"geburtsdatum", r"alter",
    r"nationality", r"nationalität", r"staatsangehörigkeit", r"citizenship", r"ethnic\w*", r"race",
    r"gender", r"male", r"female", r"männlich", r"weiblich", r"geschlecht",
    r"married", r"verheiratet", r"children", r"kinder", r"pregnan\w*", r"schwanger",
    r"religio\w*", r"konfession", r"disabilit\w*", r"behinderung", r"photo", r"foto",
]
PROTECTED_RE = re.compile(r"\b(" + "|".join(PROTECTED) + r")\b", re.IGNORECASE)


def mentioned(person: dict, text_tokens: set[str], text_lower: str) -> bool:
    if person.get("key") and person["key"].lower() in text_lower:
        return True
    toks = name_tokens(person.get("name") or "")
    return bool(toks) and all(t in text_tokens for t in toks)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report", type=Path)
    ap.add_argument("run", type=Path)
    args = ap.parse_args()

    text = args.report.read_text(encoding="utf-8")
    lower = text.lower()
    tokens = set(name_tokens(text))
    manifest = read_json(WORK / "manifest.json")
    ranking = read_json(args.run / "ranking.json")

    errors, warnings = [], []
    for m in re.finditer(r"\{\{[^}]*\}\}", text):
        errors.append(f"Template placeholder left: {m.group(0)}")
    for p in manifest["people"]:
        if not mentioned(p, tokens, lower):
            errors.append(f"Not in report (coverage): {p['name'] or p['key']}")
    people = {p["key"]: p for p in manifest["people"]}
    for role in ranking["roles"]:
        for key in role["proposed"]:
            if not mentioned(people[key], tokens, lower):
                errors.append(f"Proposed person missing: {people[key]['name'] or key}")
    for n, line in enumerate(text.splitlines(), 1):
        for m in PROTECTED_RE.finditer(line):
            warnings.append(f"Line {n}: '{m.group(0)}' may refer to a protected attribute: {line.strip()[:100]}")

    print(f"Report check: {len(errors)} error(s), {len(warnings)} warning(s)")
    for e in errors:
        print(f"Error: {e}")
    for w in warnings:
        print(f"Warning: {w}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
