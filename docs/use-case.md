# CV Match Agent: use case specification

This file defines **what** the agent must do, not how it is built. The pitch version is `docs/cv-match-agent-brief.html`. If they disagree, this file wins for behavior.

## 1. Goal

Given a staffing request, produce a shortlist of people from the resource manager's group (about 80 people) that best fits the request. Every match must be backed by evidence from the person's CV. The resource manager makes the final decision.

**Success means:** a complex request is shortlisted in under 15 minutes instead of about 3 hours. The top 5 per role includes the people a human would have picked in at least 80% of past requests.

## 2. Users and trigger

| | |
|---|---|
| Primary user | The resource manager (MVP: the only user) |
| Trigger | A staffing request from a project lead or bid team |
| Frequency | About 8 requests per month, about 2 of them complex (several people, full CV review) |
| Request forms | Email text, RFP excerpt, skill list; English or German |

## 3. What gets automated

| # | Capability | Result |
|---|---|---|
| 1 | **Understand the request** | A structured requirement list: roles and headcount, seniority slots, skills, experience, languages, availability need, other constraints |
| 2 | **Triage requirements** | Each line is classified as **Key**, **Nice to have** or **Baseline**, with a one-line reason and the accepted alternatives. Shown to the user, who can override before matching. |
| 3 | **Ask when unclear** | Specific clarifying questions, each with a proposed default, so the user can answer "yes" and continue |
| 4 | **Check availability** | Only when the request needs it. Read-only. |
| 5 | **Assess every person** | Per person and per requirement: met / partly met / not evidenced, with the CV passage that supports it |
| 6 | **Rank and fill slots** | A ranked shortlist per role or seniority slot, a proposed team (one person per slot), and runners-up |
| 7 | **Report gaps** | Requirements nobody (or too few people) meets, stated plainly |
| 8 | **Hand over** | An output the resource manager can review and adjust. Nothing is sent to anyone. |

### Output contents (per request)

- The interpreted requirements with their triage, plus any assumptions the agent made.
- Per slot: ranked candidates with a fit summary, key requirements met, nice-to-haves met, missing items, evidence quotes (with the CV reference) and CV date.
- The proposed team, and why this combination.
- Gaps and warnings (old CVs, missing CVs, availability unknown).

## 4. Constraints

- **Recommend only.** The agent never contacts people, sends emails or invites, or writes to CV, HR or planning systems.
- **Evidence or no credit.** A skill counts only if the CV shows it. Inferred items (e.g. years calculated from project dates) are marked as inferred.
- **No protected attributes.** Name (beyond identification), age, gender, nationality, photo, family status and similar are not used for matching and not shown in the reasoning.
- **Personal data stays inside approved tooling.** CVs and availability are personal data (GDPR). Only the resource manager sees the output.
- **Transparent.** Every ranking can be explained by its per-requirement assessments. No unexplained score.
- **Complete coverage.** Every person in the group is assessed. Anyone who couldn't be assessed is listed with the reason.

## 5. Out of scope (MVP)

- Contacting candidates or requesters.
- Changing HR, CV or planning records.
- Writing or rewriting CVs or RFP profiles.
- Making the final selection.
- People outside the resource manager's group.

## 6. Edge cases and ambiguity

### Request

| Situation | Expected behavior |
|---|---|
| "X or Y" (e.g. "Java or Python") | Either one fully satisfies the requirement. |
| "X or similar" | Alternatives accepted. The agent names what it counted as similar, so the user can reject it. |
| No priorities given | The agent proposes a triage. The user confirms or edits it before matching. |
| Contradiction (e.g. "5+ years" and "2 more junior") | The agent asks, with a proposed reading (e.g. "junior = 5–8 years, senior = 10+"). It doesn't guess silently. |
| "German/English required" | Ambiguous: both, or either? The agent asks. Default: both required. |
| Vague skill ("cloud", "AI skills") | Broad match, with the concrete evidence found listed. The agent asks only if the vagueness changes the ranking. |
| Experience: total vs. in the skill ("5 years in this area") | Measured in the relevant area, not total career. The agent states how it counted. |
| Headcount or seniority mix missing | The agent asks. Default: 1 person, any seniority. |
| Several roles in one request | Each role is matched separately, and one person is proposed for only one slot. |
| Request in German, CVs in English (or the reverse) | Matched across languages. Output in the language of the request. |
| Constraints the CVs can't answer (clearance, rate, location, start date) | Listed as "not checkable from CVs", not ignored. |
| Availability "not required" | The availability step is skipped and all people are considered. |

### CV data

| Situation | Expected behavior |
|---|---|
| Person on the team list has no CV | Listed as "not assessed: no CV". Not silently skipped. |
| CV older than a threshold (default: 12 months) | Still assessed, but flagged as outdated. |
| Several CV versions for one person | Uses the newest, and says which. |
| Skill listed without any project or duration | Counts as partly met, with lower confidence than skills backed by projects. |
| Unreadable file (scanned image, corrupt, unsupported) | Listed as "not assessed: unreadable". |
| CV in German | Assessed like an English CV. |
| CV belongs to someone no longer on the team | Excluded. Mismatches between the team list and the CVs are reported. |

### Matching and results

| Situation | Expected behavior |
|---|---|
| Nobody meets all key requirements | Shows the closest candidates, what each is missing, and a clear gap statement. Doesn't pad the list. |
| Fewer good candidates than slots | Fills what it can and says how many slots remain open. |
| The same person is best for two slots | Assigns them to the slot where they add most, and shows a runner-up for the other. |
| Ties | Broken by nice-to-haves, then baseline items. If still tied, shown as equal. |
| The same few people top every request | Shown as-is (no artificial rotation), but visible through the fairness KPI. |

### Availability (when required)

| Situation | Expected behavior |
|---|---|
| Availability source unreachable | Says so and marks availability as unknown. Never assumes "available". |
| Partial availability (e.g. 50%, or from a later date) | Shown per person. Only excluded if clearly below what the request needs. |

## 7. Acceptance criteria

1. **Reference request:** the RFP example in the brief (4 fullstack developers, 2 senior and 2 more junior, German and English, 9 skill lines). The agent:
   - produces the triage shown in the brief;
   - asks about the seniority contradiction and the language requirement;
   - skips availability;
   - proposes 4 people in 2+2 slots, each with cited evidence.
2. **Back-test:** on 10 past requests, the top 5 per role includes the actually picked people in at least 80% of cases.
3. **No claim without evidence:** a spot check finds 0 requirements marked "met" without a supporting CV quote.
4. **Complete coverage:** everyone on the team list appears either in the assessment or in the "not assessed" list.
5. **Time:** from pasting the request to a reviewed shortlist, under 15 minutes.

## 8. Open questions (block the build plan)

| # | Question | Why it matters |
|---|---|---|
| 1 | Where do the CVs live, and in what format (Word, PDF, company template, HR system)? | Decides how the agent reads them |
| 2 | Is there a reliable list of the ~80 people in the group? | Needed for the complete-coverage check |
| 3 | Where is availability tracked, and can it be read by a tool? | Decides whether the availability step works in the MVP |
| 4 | Which AI tools are approved for personal data? Where may the CVs be processed? | Decides the runtime (e.g. Claude Code locally, a company-hosted agent) |
| 5 | How is seniority defined in your organisation (career levels, years)? | Needed to fill senior vs. junior slots consistently |
| 6 | What format should the output have (on-screen summary, Excel, Markdown report)? | Decides the hand-over step |
| 7 | Can you provide anonymised or sample CVs for building and testing? | Real CVs shouldn't be committed to this repo |
