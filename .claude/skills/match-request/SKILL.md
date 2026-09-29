---
name: match-request
description: Match a staffing request (skills, experience, languages, headcount) against the team's CVs and write a Markdown shortlist report with evidence. Use when the user wants to find, match or shortlist people for a request, RFP, project or role.
argument-hint: "[request file in data/requests/ or pasted request text] [--samples]"
allowed-tools: Read, Write, Glob, Grep, Bash(python3 tools/*)
---

# /match-request

Turn a staffing request into a Markdown report in `reports/`. Follow `docs/guardrails.md` at every step: recommend only, evidence or no credit, no protected attributes, seniority never ranked, and nothing in `data/` changed.

Request: $ARGUMENTS

## 1. Get the request

- If the argument is a file path, read it. If it is text, use it as the request.
- If it is empty, list the files in `data/requests/` and ask which one to use, or ask the user to paste the request. Stop until they answer.
- Pick a run id: `YYYY-MM-DD-<short-slug>`, e.g. `2026-09-29-rfp-fullstack`. Create `.work/runs/<run-id>/` and save the request text there as `request.md`.

## 2. Prepare the data

Run `python3 tools/prepare_data.py`. If the arguments contain `--samples`, use the fictional sample set instead: `python3 tools/prepare_data.py --cvs samples/cvs --team samples/team`, and say in the report that sample data was used.

- Exit code 1 means nobody can be assessed. Tell the user what is missing (CVs in `data/cvs/`, the team list in `data/team/`), mention that `--samples` runs on the sample data in `samples/`, and stop.
- Keep the printed warnings (probable name matches, CVs matching nobody, outdated CVs). They go into the report. Don't try to fix data.

## 3. Triage the request

Read `reference/triage-guide.md` and `reference/skill-alternatives.md`. Then write `.work/runs/<run-id>/request.json` following `reference/request-schema.md`.

Show the user, in the request's language:
- the requirements table: requirement, weight (Key / Nice to have / Baseline), accepted alternatives, one-line reason;
- positions per role, the recorded seniority mix (not used for ranking) and whether availability is checked;
- the assumptions;
- questions, only for real contradictions (see guardrails §8), each with a proposed default.

Then ask: "Proceed with this triage, or change something?" and **stop until the user answers**. Apply any changes to `request.json`.

## 4. Assess every CV

- Read `.work/manifest.json`. Take every person with `"status": "ok"`.
- Split them into batches of about 8. Launch one `cv-assessor` subagent per batch, **all in one message so they run in parallel**.
- Give each subagent this prompt: `Run dir: .work/runs/<run-id>. Assess: <key1>, <key2>, ...`
- When all have finished, check that `.work/runs/<run-id>/assessments/` has one file per assessable person. Re-launch a subagent for any that are missing.

## 5. Verify the evidence

Run `python3 tools/verify_evidence.py .work/runs/<run-id>`.

- If it reports problems, run a `cv-assessor` again for the affected people. Tell it which requirements failed, and ask it to re-check them and quote exactly.
- Then run `python3 tools/verify_evidence.py .work/runs/<run-id> --fix`. This downgrades whatever still can't be verified.
- Continue only when it exits with 0.

## 6. Rank

Run `python3 tools/rank.py .work/runs/<run-id>`. The ranking and team proposal in `ranking.json` are final. Don't re-order or swap people in the report. If you think the ranking is wrong, say so in the summary and explain why.

## 7. Write the report

Write `reports/<run-id>.md` from `templates/match-report.md`:

- **Language.** Write in the request's language. Translate the headings for German requests.
- **Sources.** Use `request.json`, `ranking.json`, `.work/manifest.json` and the assessment files. Read the full assessment only for shortlisted and proposed people.
- **Fit labels:**

  | Tier | Label |
  |---|---|
  | `full` | Strong fit |
  | `language_gap` | Strong fit, language gap |
  | `partial` | Partial fit |
  | `weak` | Weak fit |

- **Coverage.** Every person on the team list appears exactly once: in the shortlist, "Everyone else assessed", "Not assessed" or the unavailable list.
- **Quotes.** Copy the evidence quotes from the assessments. Don't rephrase them.
- **Seniority.** Show seniority indications only as written by the assessor, labelled as an indication. Put the requested seniority mix in the summary as a point for the resource manager to decide.
- **Language gaps.** For a `language_gap` person, write the note "language may be an issue: discuss with the requester".
- **Placeholders.** Remove every `{{...}}`.

## 8. Check the report

Run `python3 tools/check_report.py reports/<run-id>.md .work/runs/<run-id>`.

- Fix all errors and run it again.
- Review every protected-attribute warning. Remove the wording if it refers to a person's age, origin, gender, family or similar. Keep it only if it clearly doesn't, e.g. "Stage" or "image".

## 9. Hand over

Reply in a few lines:
- the report path;
- the proposed people with their fit labels;
- the main gaps;
- data warnings the user should act on (e.g. confirm a probable name match in `data/team/cv_links.json`).

Don't paste the full report. Don't contact anyone or send the report anywhere.
