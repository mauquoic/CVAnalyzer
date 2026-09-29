#!/usr/bin/env python3
"""Read the team list and all CVs, link them, and write a manifest for the CV Match Agent.

Linking a CV file to a person on the team list, in this order:
  1. data/team/cv_links.json  {"<CV file name>": "<name or ID on the team list>"}   (manual fixes)
  2. a CV-file column in the team list
  3. an ID column whose value the file name starts with
  4. the person's name in the file name, then on the CV's first slide or page.
     Tolerates case, accents/umlauts (Müller = Mueller), word order and extra middle names.
     Unique "probable" matches (e.g. Jan vs. Jana) are linked but flagged for confirmation.
     A file that matches several people equally is not linked and is reported.

Outputs (in .work/, not committed):
  .work/cvs/<key>.txt    plain text of each person's current CV
  .work/manifest.json    one entry per person: CV file, link method, CV date, outdated flag, status, availability

Usage: python3 tools/prepare_data.py [--cvs DIR] [--team DIR]
Exit code 1 if nobody can be assessed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (CV_DIR, CV_EXTENSIONS, OUTDATED_MONTHS, ROOT, TEAM_DIR, TEAM_EXTENSIONS, WORK,  # noqa: E402
                    _csv_rows, _xlsx_rows, extract_text, map_columns, name_match, parse_availability,
                    parse_date, read_json, slug, write_json)

# Dates in CV file names: 2025-03, 2025-03-10, 202501, 20250110, 08.2023, 08-2023, 11_2024.
FILENAME_DATES = [
    (re.compile(r"(?<!\d)(20\d{2})[-_.]?(0[1-9]|1[0-2])(?:[-_.]?(0[1-9]|[12]\d|3[01]))?(?!\d)"), (1, 2, 3)),
    (re.compile(r"(?<!\d)(0[1-9]|1[0-2])[-_.](20\d{2})(?!\d)"), (2, 1, None)),
]
LEVELS = {"manual": 5, "column": 4, "id": 4, "exact": 3, "strong": 2, "probable": 1}


def rel(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(ROOT))
    except ValueError:
        return str(p)


def load_team(team_dir: Path, warnings: list[str]) -> tuple[list[dict], str | None]:
    files = sorted(p for p in team_dir.glob("*") if p.suffix.lower() in TEAM_EXTENSIONS and not p.name.startswith(("~$", ".")))
    if not files:
        warnings.append(f"No team list found in {rel(team_dir)}/ (.xlsx or .csv). "
                        "Every CV is treated as a team member and availability is unknown.")
        return [], None
    if len(files) > 1:
        warnings.append(f"Several team lists found; using {files[0].name}.")
    path = files[0]
    rows = _xlsx_rows(path) if path.suffix.lower() == ".xlsx" else _csv_rows(path)
    override_path = team_dir / "columns.json"
    override = read_json(override_path) if override_path.exists() else None
    # The header is the first row that maps a name or ID column (Excel lists often have a title row first).
    header_idx = next((i for i, r in enumerate(rows[:10]) if {"name", "id", "last_name"} & set(map_columns(r, override))), None)
    if header_idx is None:
        raise SystemExit(f"Team list {path.name}: no name or ID column found in the first rows. "
                         'Map it in data/team/columns.json, e.g. {"name": "<your name column>"}.')
    headers = rows[header_idx]
    cols = map_columns(headers, override)
    for field in ("availability", "available_from"):
        if field not in cols:
            warnings.append(f"Team list: no '{field}' column recognised (headers: {headers}). "
                            "Map it in data/team/columns.json if it exists.")
    used = set(cols.values())
    people, keys = [], set()
    for row in rows[header_idx + 1:]:
        def get(f: str) -> str:
            return row[cols[f]].strip() if f in cols and cols[f] < len(row) else ""
        name = get("name") or " ".join(x for x in (get("first_name"), get("last_name")) if x)
        pid = get("id")
        if not (name or pid):
            continue
        key = pid or slug(name)
        if key in keys:
            warnings.append(f"Team list: '{name or pid}' appears twice; only the first row is used.")
            continue
        keys.add(key)
        raw_av = get("availability")
        people.append({
            "key": key, "name": name or None, "id": pid or None,
            "availability_raw": raw_av or None,
            "availability_pct": parse_availability(raw_av),
            "available_from": parse_date(get("available_from")) or (get("available_from") or None),
            "level": get("level") or None,
            "cv_file_hint": get("cv_file") or None,
            "extra": {h: row[i] for i, h in enumerate(headers) if i not in used and i < len(row) and row[i]},
        })
    return people, path.name


def cv_files(cv_dir: Path) -> list[Path]:
    return sorted(p for p in cv_dir.rglob("*") if p.is_file() and p.suffix.lower() in CV_EXTENSIONS
                  and p.name.lower() != "readme.md" and not p.name.startswith(("~$", ".")))


def filename_date(path: Path) -> str | None:
    """The last date found in the file name, as YYYY-MM-DD (day 01 if only a month is given)."""
    found = []
    for rx, (y, m, d) in FILENAME_DATES:
        for hit in rx.finditer(path.stem):
            day = hit.group(d) if d and hit.group(d) else "01"
            found.append((hit.start(), f"{hit.group(y)}-{hit.group(m)}-{day}"))
    return max(found)[1] if found else None


def strip_date(stem: str) -> str:
    for rx, _ in FILENAME_DATES:
        stem = rx.sub("", stem)
    return stem


def head_lines(text: str, n: int = 15) -> list[str]:
    return [ln for ln in text.splitlines() if ln.strip() and not ln.startswith("--- Slide")][:n]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cvs", type=Path, default=CV_DIR)
    ap.add_argument("--team", type=Path, default=TEAM_DIR)
    args = ap.parse_args()

    warnings: list[str] = []
    team, team_source = load_team(args.team, warnings)
    files = cv_files(args.cvs)

    # Extract every CV once; unreadable files are kept with their error.
    texts: dict[Path, tuple[str | None, str | None, str | None]] = {}
    for f in files:
        try:
            text, doc_date = extract_text(f)
            problem = None if len(text.strip()) >= 200 else "Almost no text extracted (scanned image or empty file?)"
            texts[f] = (text, doc_date, problem)
        except Exception as e:  # an unreadable file must not stop the run
            texts[f] = (None, None, str(e) or type(e).__name__)

    if not team:
        team = [{"key": slug(f.stem) or f.stem, "name": re.sub(r"[_\-]+", " ", strip_date(f.stem)).strip(),
                 "id": None, "availability_raw": None, "availability_pct": None, "available_from": None,
                 "level": None, "cv_file_hint": None, "extra": {}} for f in files]

    links_path = args.team / "cv_links.json"
    manual = read_json(links_path) if links_path.exists() else {}

    # For each file, collect (person index, level) candidates.
    assigned: dict[Path, tuple[int, str]] = {}
    ambiguous: list[str] = []
    for f in files:
        cands: list[tuple[int, str]] = []
        target = manual.get(f.name) or manual.get(f.stem)
        if target:
            cands = [(i, "manual") for i, p in enumerate(team) if target in (p["name"], p["id"], p["key"])]
            if not cands:
                warnings.append(f"cv_links.json: '{target}' for {f.name} is not on the team list.")
        if not cands:
            cands = [(i, "column") for i, p in enumerate(team) if p["cv_file_hint"] and p["cv_file_hint"].lower() in (f.name.lower(), f.stem.lower())]
        if not cands:
            cands = [(i, "id") for i, p in enumerate(team) if p["id"] and re.match(rf"{re.escape(p['id'].lower())}(?![a-z0-9])", f.stem.lower())]
        if not cands:
            for i, p in enumerate(team):
                if p["name"] and (lvl := name_match(p["name"], strip_date(f.stem))):
                    cands.append((i, lvl))
        if not cands and texts[f][0]:
            for i, p in enumerate(team):
                if not p["name"]:
                    continue
                best = max((name_match(p["name"], ln) or "" for ln in head_lines(texts[f][0])), key=lambda l: LEVELS.get(l, 0))
                if best in ("exact", "strong"):
                    cands.append((i, f"{best} (CV text)"))
        if not cands:
            continue
        top = max(LEVELS[c[1].split(" ")[0]] for c in cands)
        best = [c for c in cands if LEVELS[c[1].split(" ")[0]] == top]
        if len(best) > 1:
            ambiguous.append(f"{f.name} matches several people ({', '.join(team[i]['name'] or team[i]['key'] for i, _ in best)}); "
                             "not linked. Add it to data/team/cv_links.json.")
            continue
        assigned[f] = best[0]

    out_dir = WORK / "cvs"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    today = dt.date.today()
    cutoff = (today - dt.timedelta(days=round(OUTDATED_MONTHS * 30.44))).isoformat()

    people = []
    to_confirm = []
    for i, person in enumerate(team):
        person = {k: v for k, v in person.items() if k != "cv_file_hint"}
        mine = [f for f, (j, _) in assigned.items() if j == i]
        entry = {**person, "status": "ok", "cv_file": None, "link": None, "cv_versions": len(mine),
                 "cv_date": None, "cv_date_source": None, "outdated": None, "chars": 0, "problem": None}
        if not mine:
            entry.update(status="no_cv", problem="No CV file linked to this person")
            people.append(entry)
            continue
        # Newest version: date in file name, then document date, then file name.
        chosen = sorted(mine, key=lambda f: (filename_date(f) or texts[f][1] or "", f.name))[-1]
        text, doc_date, problem = texts[chosen]
        entry["cv_file"] = rel(chosen)
        entry["link"] = assigned[chosen][1]
        if entry["link"].startswith("probable"):
            to_confirm.append(f"{chosen.name} → {person['name']}")
        if problem:
            entry.update(status="unreadable", problem=problem)
            people.append(entry)
            continue
        date = filename_date(chosen)
        entry["cv_date_source"] = "file name" if date else ("document properties" if doc_date else None)
        entry["cv_date"] = date or doc_date
        entry["outdated"] = (entry["cv_date"] < cutoff) if entry["cv_date"] else None
        entry["chars"] = len(text)
        (out_dir / f"{person['key']}.txt").write_text(text, encoding="utf-8")
        people.append(entry)

    unlinked = [f.name for f in files if f not in assigned]
    ambiguous_names = {a.split(" matches")[0] for a in ambiguous}
    orphans = [n for n in unlinked if n not in ambiguous_names]
    warnings += ambiguous
    if orphans:
        warnings.append(f"{len(orphans)} CV file(s) match nobody on the team list and are ignored: {', '.join(orphans)}. "
                        "If they belong to someone, add them to data/team/cv_links.json.")
    if to_confirm:
        warnings.append("Probable name matches, please confirm (or correct in data/team/cv_links.json): " + "; ".join(to_confirm))
    multi = [p["name"] or p["key"] for p in people if p["cv_versions"] > 1]
    if multi:
        warnings.append(f"Several CV files for {', '.join(multi)}; the newest is used.")

    manifest = {
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "team_source": team_source,
        "outdated_before": cutoff,
        "counts": {s: sum(p["status"] == s for p in people) for s in ("ok", "no_cv", "unreadable")},
        "people": people,
        "unlinked_cvs": unlinked,
        "warnings": warnings,
    }
    write_json(WORK / "manifest.json", manifest)

    c = manifest["counts"]
    print(f"Team list: {team_source or 'none'} · people: {len(people)} · assessable: {c['ok']} · "
          f"no CV: {c['no_cv']} · unreadable: {c['unreadable']}")
    outdated = [p["name"] or p["key"] for p in people if p["outdated"]]
    undated = [p["name"] or p["key"] for p in people if p["status"] == "ok" and not p["cv_date"]]
    if outdated:
        print(f"Outdated CVs (before {cutoff}): {', '.join(outdated)}")
    if undated:
        print(f"CV date unknown: {', '.join(undated)}")
    for p in people:
        if p["status"] != "ok":
            print(f"Not assessable: {p['name'] or p['key']}: {p['problem']}")
    for w in warnings:
        print(f"Warning: {w}")
    print(f"Manifest: {rel(WORK / 'manifest.json')}")
    return 0 if c["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
