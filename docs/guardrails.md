# CV Match Agent: guidelines and guardrails

These rules apply to every run of `/match-request` and to any future skill or agent in this repository. `docs/use-case.md` describes what the agent does. This file describes the limits it works within. If they conflict, this file wins.

## 1. The agent recommends, people decide

| The agent does | The resource manager decides |
|---|---|
| Interprets and triages the request | Whether the triage is right (can override before matching) |
| Assesses every CV against every requirement | The final selection |
| Ranks candidates and proposes a team | Whether to propose someone with a language gap |
| Adds a seniority *indication* where the CV shows one | The seniority mix of the team |
| Flags uncertain data (probable name matches, old CVs, unknown availability) | Whether flagged data can be trusted |

The report is always worded as a recommendation ("proposed", "suggested"), never as a decision.

## 2. Actions the agent never takes

- Contacting anyone: candidates, requesters or managers. No emails, messages, invitations or calendar entries.
- Changing anything in `data/`. CVs, the team list and link files are read-only for the agent.
- Writing to HR, CV or planning systems.
- Looking people up outside the provided data (web search, LinkedIn, company directories).
- Sharing the report anywhere. It stays in `reports/` and is handed to the resource manager only.

## 3. Evidence

- **Evidence or no credit.** A requirement is **met** or **partly met** only with a quote copied from the person's CV. Without a quote it is **not evidenced**.
- **Verbatim quotes.** Quotes are copied exactly and kept short. `tools/verify_evidence.py` checks every quote against the CV text. Quotes that can't be found are removed, and the requirement is downgraded.
- **Inferred values are labelled.** Examples are years of experience calculated from project dates, or "similar" technologies. The quote shows the basis.
- **Absence is not a negative claim.** "Not evidenced" means the CV doesn't show it, not that the person can't do it. The report says so.

## 4. Fairness

- Matching and reasoning use only skills, experience, projects, certifications and the languages the request asks for.
- Never used, never mentioned: age or date of birth, gender, nationality or origin, family status, religion, health or disability, photos, and appearance. The same applies to anything inferred from a name.
- The same rules apply to everyone. There is no "culture fit" and no personal impression.
- The report lists every person on the team list, so nobody is silently left out.
- `tools/check_report.py` warns about words that point to protected attributes. Every warning is reviewed before hand-over.

## 5. Seniority

- Candidates are **ranked by fit only**. Seniority never changes a ranking.
- A requested seniority mix (e.g. "2 more junior, 2 more senior") is recorded in the report as a note for the resource manager.
- A seniority indication is added only when the CV shows it explicitly: role titles such as lead, architect or senior, or years in the field. It is labelled "indication", with the supporting quote. If there is no clear evidence, there is no indication.
- The team list's level column may be shown for context. It is not used for ranking.

## 6. Languages

- "German/English" means both are required unless the request says otherwise. The assumption is stated in the report.
- Level mapping:
  - **met:** native, fluent, business fluent, C1, C2, *verhandlungssicher*, *fließend*
  - **partly met:** good, B1, B2, *gut*
  - **not evidenced:** basic, A1, A2, *Grundkenntnisse*, or not mentioned
- Someone who meets every key skill but misses a required language is **still shown**. They rank after candidates who meet everything and carry the note "language may be an issue: discuss with the requester".

## 7. Availability

- Checked only when the request needs it. For RFP sample profiles it usually doesn't.
- Read-only, from the team list.
- Someone is marked unavailable only when that's clear: 0 % free, below a stated minimum, or free only after the needed start date. Everything else stays on the shortlist.
- Unknown availability is shown as unknown. It is never assumed to be available.

## 8. Ambiguity

- **Default and state.** For common ambiguities (languages, headcount, "or similar", how experience is counted), the agent applies the default from `docs/use-case.md` and lists it under *Assumptions* in the report.
- **Ask.** When hard requirements contradict each other, or a wrong reading would change the result substantially, the agent asks before matching, with a proposed default.
- **One confirmation step.** Before matching, the triage and assumptions are shown once for the resource manager to confirm or correct.
- **Data problems are reported, not fixed.** This covers probable name matches, CVs matching several people, CVs matching nobody, missing or unreadable CVs, and old CVs. The resource manager fixes them in `data/team/cv_links.json` or by updating files.

## 9. Personal data

- CVs and the team list contain personal data. `data/cvs/`, `data/team/` and `reports/` are gitignored and stay on the machine that runs the agent.
- Extracted CV text and intermediate results live in `.work/`, which is also gitignored. `.work/` is rebuilt on every run.
- Test data in `tests/fixtures/` is synthetic and fictional.

## 10. How each guardrail is enforced

| Guardrail | Enforced by |
|---|---|
| No changes to `data/` | Deny rule in `.claude/settings.json`, plus instructions |
| No web lookups of people | Deny rule for WebSearch and WebFetch in `.claude/settings.json` |
| Evidence or no credit | `tools/verify_evidence.py` (blocking) |
| Ranking by fit, seniority ignored, language gap shown | `tools/rank.py` (deterministic) |
| Complete coverage, no placeholders | `tools/check_report.py` (blocking) |
| Protected attributes | `tools/check_report.py` (warning, reviewed), plus instructions to the subagent |
| Recommend only, one confirmation step | `/match-request` skill instructions |
| Personal data stays local | `.gitignore` |
