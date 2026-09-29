# Tools

Deterministic helpers that the `/match-request` skill calls. Run any of them with `--help` for usage. See `CLAUDE.md` for how they fit together.

| Script | Does |
|---|---|
| `prepare_data.py` | Links the team list and CVs, extracts CV text, and writes `.work/manifest.json` |
| `verify_evidence.py` | Checks every evidence quote against the CV text |
| `rank.py` | Tiers and ranks candidates, proposes a team, and lists gaps |
| `check_report.py` | Checks the finished report for coverage, placeholders and protected-attribute wording |
| `common.py` | Shared helpers: file readers, name matching, text normalisation |
