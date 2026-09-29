# Match report: {{REQUEST_TITLE}}

| | |
|---|---|
| Date | {{DATE}} |
| Request | {{REQUEST_SOURCE}} |
| Team data | {{TEAM_SOURCE}}: {{TEAM_SIZE}} people · {{ASSESSED}} assessed · {{NOT_ASSESSED}} not assessed |
| Run | `{{RUN_DIR}}` |

> Recommendation only. The final selection, the seniority mix and anything shared with the requester are decided by the resource manager.

## Summary

{{3–5 SENTENCES: WHO IS PROPOSED, HOW WELL THEY FIT, MAIN GAPS, WHAT TO DISCUSS WITH THE REQUESTER}}

## Request as understood

| # | Requirement | Weight | Accepted alternatives | Reasoning |
|---|---|---|---|---|
{{ONE ROW PER REQUIREMENT FROM request.json}}

- **Positions:** {{POSITIONS PER ROLE}}
- **Seniority mix requested:** {{SENIORITY_MIX or "none"}}. Not used for ranking. See the seniority indications below.
- **Availability:** {{REQUIRED / NOT REQUIRED, AND FROM WHEN}}
- **Assumptions:** {{LIST}}
- **Not checkable from CVs:** {{LIST or "none"}}

## Proposed team

| Position | Name | Fit | Key skills | Languages | Nice to have | Notes |
|---|---|---|---|---|---|---|
{{ONE ROW PER PROPOSED PERSON, IN RANKING ORDER; "open" ROWS FOR UNFILLED POSITIONS}}

## Shortlist

{{PER ROLE: ONE BLOCK PER SHORTLISTED PERSON, IN RANKING ORDER}}

### {{RANK}}. {{NAME}} ({{FIT LABEL}})

{{ONE-SENTENCE FIT SUMMARY}}

| Requirement | Assessment | Evidence from CV |
|---|---|---|
{{ONE ROW PER REQUIREMENT: STATE AND SHORT QUOTE; MARK INFERRED VALUES}}

- **Seniority indication:** {{INDICATION WITH QUOTE, or "no clear indication in the CV"}}
- **Availability:** {{ONLY IF REQUIRED}}
- **CV:** `{{CV_FILE}}`, dated {{CV_DATE}}
- **Notes:** {{FLAGS: LANGUAGE GAP, OUTDATED CV, PROBABLE NAME MATCH, UNKNOWN AVAILABILITY}}

## Gaps

{{REQUIREMENTS NOBODY OR TOO FEW PEOPLE MEET, OR "none"}}

## Everyone else assessed

| Name | Fit | Key skills | Languages | Nice to have | Main missing |
|---|---|---|---|---|---|
{{EVERY OTHER ASSESSED PERSON, IN RANKING ORDER}}

## Not assessed

| Name | Reason |
|---|---|
{{EVERY PERSON WITHOUT AN ASSESSMENT, or "Everyone on the team list was assessed."}}

## Data warnings

{{OUTDATED CVS, PROBABLE NAME MATCHES TO CONFIRM, CVS MATCHING NOBODY, UNAVAILABLE PEOPLE, or "none"}}

## How this report was produced

Every CV was checked against every requirement. A requirement counts as met only with a quote from the CV, and all quotes were verified automatically against the CV text. Candidates are ranked in tiers:
1. Everything key met.
2. Key skills met, with a language gap.
3. At least half the key skills.
4. Below that.

Within each tier, candidates are sorted by key skills, languages, nice-to-haves and baseline items. Seniority, age, gender, nationality and other personal attributes play no role.
