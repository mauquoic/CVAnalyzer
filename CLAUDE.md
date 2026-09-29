# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

The **CV Match Agent** runs in Claude Code. `/match-request <request>` turns a staffing request (skills, experience, languages, headcount, optional availability) into a Markdown report in `reports/`. The report holds a shortlist of people from the resource manager's group of about 80, with every match backed by a quote from the person's CV. The resource manager makes the final decision. There is no separate UI.

Read these before changing agent behavior:
- `docs/use-case.md`: what the agent does, edge cases, acceptance criteria, decisions and open questions.
- `docs/guardrails.md`: the limits it works within and how each is enforced. If the two conflict, the guardrails win.
- `docs/cv-match-agent-brief.html`: the pitch deck (see below).

## Commands

```bash
python3 -m unittest discover -s tests                              # all tests (synthetic fixtures, no real data)
python3 -m unittest tests.test_tools.ToolsTest.test_rank_order     # one test
python3 tools/prepare_data.py                                      # link team list and CVs, extract text into .work/
python3 tools/verify_evidence.py .work/runs/<run-id> [--fix]       # check assessment quotes against CV text
python3 tools/rank.py .work/runs/<run-id>                          # rank and propose a team -> ranking.json
python3 tools/check_report.py reports/<run-id>.md .work/runs/<run-id>
```

The tools use only the Python standard library for `.pptx`, `.docx` and `.xlsx`. `pip install -r requirements.txt` (pypdf) is needed only for PDF CVs. `pypdf` is also picked up from a project `.venv/` if the system install is broken. `requirements-dev.txt` is needed only to regenerate the fixtures with `tests/fixtures/make_fixtures.py`. Set `CVMATCH_WORK` to point the tools at a different work folder (the tests do this).

## How a run works

The `/match-request` skill (`.claude/skills/match-request/SKILL.md`) orchestrates the run. Model judgment and deterministic code are deliberately split:

1. **`prepare_data.py`** reads the Excel team list (`data/team/`) and the PowerPoint CVs (`data/cvs/`). It links CVs to people by fuzzy name matching, which tolerates middle names, umlaut spellings and word order. It writes `.work/cvs/<key>.txt` and `.work/manifest.json`. The person key is the team list's ID column if present, otherwise a slug of the name. Unlinkable or ambiguous files are reported, never guessed. `data/team/cv_links.json` overrides links and `data/team/columns.json` maps column headers.
2. **Triage** (model): the request becomes `.work/runs/<run-id>/request.json` (schema in `reference/request-schema.md`, rules in `reference/triage-guide.md`). It is confirmed by the user once.
3. **`cv-assessor` subagents** (`.claude/agents/cv-assessor.md`), run in parallel batches of about 8. Each writes `assessments/<key>.json` with met / partly met / not evidenced per requirement, plus verbatim quotes.
4. **`verify_evidence.py`** rejects any quote not found in the CV text. `--fix` downgrades what can't be verified.
5. **`rank.py`** ranks deterministically: tiers full → language_gap → partial → weak, then points. Seniority is never used. It proposes a team and lists gaps. The report must not re-order this.
6. **Report** (model) from `templates/match-report.md`, then **`check_report.py`** blocks on missing people or leftover placeholders, and warns on protected-attribute wording.

## Conventions

- **Triage classes:** Key, Nice to have (alternatives accepted), Baseline (tie-breaker only). In JSON: `key`, `nice`, `baseline`.
- **Assessment states:** `met`, `partly met`, `not evidenced`. Points 1 / 0.5 / 0.
- **Languages:** each required language is its own requirement with `kind: "language"`. That's how `rank.py` recognises a language gap. A language gap never excludes anyone. It adds the note "language may be an issue: discuss with the requester".
- **Defaults:** "German/English" means both required. A CV older than 12 months is outdated. A missing headcount means 1 person. Defaults are always stated in the report as assumptions.
- **Run ids:** `YYYY-MM-DD-<short-slug>`. The work files are in `.work/runs/<run-id>/` and the report is `reports/<run-id>.md`.
- **Report language:** follows the request's language (English or German). Evidence quotes stay in the CV's language.
- **Shared vocabulary:** `reference/skill-alternatives.md` holds synonyms and accepted alternatives. Extend it rather than hard-coding equivalences in prompts.
- **New agent behavior** belongs in a skill or subagent. Anything that must be exact (matching rules, ranking, checks) belongs in `tools/` with a test in `tests/test_tools.py` on the synthetic fixtures.

## Guardrails (short version of `docs/guardrails.md`)

- **Recommend only.** Never contact anyone. Never change `data/` (enforced by a deny rule in `.claude/settings.json`). No web lookups of people (WebSearch and WebFetch are denied).
- **Evidence or no credit.** Quotes are verbatim and verified by script.
- **No protected attributes** (age, gender, nationality, family, religion, health, photo, anything inferred from a name) in matching or reasoning.
- **Complete coverage.** Every person on the team list appears in the report.
- **Seniority** is recorded, never ranked. At most there is a labelled indication with a quote.
- **Personal data.** `data/cvs/`, `data/team/`, `data/requests/` (except the example), `reports/` and `.work/` are gitignored. Never commit real CVs, names or reports. `tests/fixtures/` is synthetic.

## The brief deck (`docs/cv-match-agent-brief.html`)

It's a single self-contained HTML file, presented as a click-through deck. It's also published as a claude.ai Artifact: https://claude.ai/artifact/Ltdmt8bphszgu2wEYNk7Da. Republishing the same file updates that link.

- **No document skeleton.** The file has no `<!doctype>`, `<html>`, `<head>` or `<body>` tags, because the Artifact publisher adds them. `.slide[hidden] { display: none; }` keeps it working when opened locally.
- **Slides.** Each slide is a `<section class="slide" data-title="…">`, and all but the first carry `hidden`. The inline script builds the table of contents, the counter, keyboard navigation and `#sN` deep links from the sections.
- **Theming.** Colors are tokens on `:root`, redefined in both dark-mode blocks. A new color must be added to all three.
- **Embedded image.** The original request email is a base64 WebP data URI. Avoid printing that line in full.
- **External resources.** Fonts load from Google Fonts only. Everything else is inline (Artifact CSP).
