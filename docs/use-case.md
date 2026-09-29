# CV Match Agent: use case specification

This file defines **what** the agent must do, not how it is built. The pitch version is `docs/cv-match-agent-brief.html`. If they disagree, this file wins for behavior.

## 1. Goal

Given a staffing request, produce a Markdown report with a shortlist of people from the resource manager's group (about 80 people) that best fits the request. Every match must be backed by evidence from the person's CV. The resource manager makes the final decision.

**Success means:** a complex request is shortlisted in under 15 minutes instead of about 3 hours. The top 5 per role includes the people a human would have picked in at least 80% of past requests.

## 2. Users and trigger

| | |
|---|---|
| Primary user | The resource manager (MVP: the only user) |
| Trigger | A staffing request from a project lead or bid team |
| Frequency | About 8 requests per month, about 2 of them complex (several people, full CV review) |
| Request forms | Email text, RFP excerpt, skill list; English or German |
| Where it runs | In Claude Code, in this repository |
| Inputs on disk | Anonymised CVs in `data/cvs/`, team list with availability in `data/team/`, requests in `data/requests/` (or pasted in) |
| Output | A Markdown report in `reports/` |

## 3. What gets automated

| # | Capability | Result |
|---|---|---|
| 1 | **Understand the request** | A structured requirement list: roles and headcount, skills, experience, languages, availability need, other constraints. A requested seniority mix is recorded but not used for ranking (see §4). |
| 2 | **Triage requirements** | Each line is classified as **Key**, **Nice to have** or **Baseline**, with a one-line reason and the accepted alternatives. Shown to the user, who can override before matching. |
| 3 | **Ask when unclear** | Specific clarifying questions, each with a proposed default, so the user can answer "yes" and continue |
| 4 | **Check availability** | Only when the request needs it. Read-only, from the team list. |
| 5 | **Assess every person** | Per person and per requirement: met / partly met / not evidenced, with the CV passage that supports it |
| 6 | **Rank and propose** | A ranked shortlist per role, a proposed team (one person per open position), and runners-up |
| 7 | **Report gaps** | Requirements nobody (or too few people) meets, stated plainly |
| 8 | **Hand over** | A Markdown report in `reports/` that the resource manager reviews. Nothing is sent to anyone. |

### Report contents (one Markdown file per request)

- The interpreted requirements with their triage, plus any assumptions the agent made and any open questions.
- Per role: ranked candidates with a fit summary, key requirements met, nice-to-haves met, missing items, evidence quotes (with the CV reference), CV date and availability (when relevant).
- Notes per candidate, e.g. "language may be an issue: discuss with the requester" or a seniority indication where one can be read from the CV.
- The proposed team, and why this combination.
- Gaps and warnings (old CVs, missing CVs, availability unknown, team list and CV mismatches).

## 4. Constraints

- **Recommend only.** The agent never contacts people, sends emails or invites, or writes to CV, HR or planning systems.
- **Evidence or no credit.** A skill counts only if the CV shows it. Inferred items (e.g. years calculated from project dates) are marked as inferred.
- **No protected attributes.** Name (beyond identification), age, gender, nationality, photo, family status and similar are not used for matching and not shown in the reasoning.
- **Personal data stays inside approved tooling.** CVs and availability are personal data (GDPR). Only the resource manager sees the output.
- **Transparent.** Every ranking can be explained by its per-requirement assessments. No unexplained score.
- **Complete coverage.** Every person on the team list is assessed. Anyone who couldn't be assessed is listed with the reason.
- **Seniority is the resource manager's call.** The agent doesn't rank or fill slots by seniority. Where the CV clearly shows it (e.g. lead roles, years), it may add a seniority *indication* as a note, labelled as a recommendation.

## 5. Out of scope (MVP)

- Contacting candidates or requesters.
- Changing HR, CV or planning records.
- Writing or rewriting CVs or RFP profiles.
- Making the final selection.
- People outside the resource manager's group.
- Deciding seniority or filling seniority slots.
- A separate user interface. The agent is triggered from Claude Code.

## 6. Edge cases and ambiguity

### Request

| Situation | Expected behavior |
|---|---|
| "X or Y" (e.g. "Java or Python") | Either one fully satisfies the requirement. |
| "X or similar" | Alternatives accepted. The agent names what it counted as similar, so the user can reject it. |
| No priorities given | The agent proposes a triage. The user confirms or edits it before matching. |
| Contradiction in hard requirements (e.g. "Java" and "no JVM") | The agent asks, with a proposed reading. It doesn't guess silently. |
| Seniority mix requested (e.g. "2 more junior, 2 more senior") | Recorded in the report. Candidates are ranked by fit only. The resource manager picks the mix. Seniority indications are notes only. |
| "German/English required" | Default reading: both required. The agent states this assumption in the report. |
| A person meets everything except a required language | Still shown in the shortlist, with the note "language may be an issue: discuss with the requester". Ranked after candidates who meet all key requirements. |
| Vague skill ("cloud", "AI skills") | Broad match, with the concrete evidence found listed. The agent asks only if the vagueness changes the ranking. |
| Experience: total vs. in the skill ("5 years in this area") | Measured in the relevant area, not total career. The agent states how it counted. |
| Headcount missing | Default: 1 person. The agent states this assumption. |
| Several roles in one request | Each role is matched separately, and one person is proposed for only one position. |
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
| Fewer good candidates than open positions | Proposes what it can and says how many positions remain open. |
| The same person is best for two roles | Assigns them to the role where they add most, and shows a runner-up for the other. |
| Ties | Broken by nice-to-haves, then baseline items. If still tied, shown as equal. |
| The same few people top every request | Shown as-is (no artificial rotation), but visible through the fairness KPI. |

### Availability (when required)

| Situation | Expected behavior |
|---|---|
| Availability missing or unreadable for a person | Marks availability as unknown for that person. Never assumes "available". |
| Partial availability (e.g. 50%, or from a later date) | Shown per person. Only excluded if clearly below what the request needs. |

## 7. Acceptance criteria

1. **Reference request:** the RFP example in the brief (4 fullstack developers, German and English, 9 skill lines, seniority mix requested). The agent:
   - produces the triage shown in the brief;
   - states its assumptions (both languages required, experience counted in the relevant area);
   - skips availability;
   - records the seniority mix without ranking by it;
   - proposes 4 people with cited evidence, plus runners-up, in a Markdown report in `reports/`.
2. **Back-test:** on 10 past requests, the top 5 per role includes the actually picked people in at least 80% of cases.
3. **No claim without evidence:** a spot check finds 0 requirements marked "met" without a supporting CV quote.
4. **Complete coverage:** everyone on the team list appears either in the assessment or in the "not assessed" list.
5. **Time:** from pasting the request to a reviewed shortlist, under 15 minutes.

## 8. Decisions

| Topic | Decision |
|---|---|
| CVs | Anonymised CVs, provided by the resource manager in `data/cvs/` |
| Team list and availability | One list of the ~80 people including availability, in `data/team/` |
| Runtime | Claude Code, in this repository. No separate UI. |
| Seniority | Not used for ranking. At most a labelled indication, judged by the resource manager. |
| Output | Markdown report in `reports/` |
| Test data | The anonymised CVs in `data/cvs/` |
| Languages | "German/English" means both required. A person missing only the language is still shown, with a note. |
| Outdated CV | Older than 12 months |
| Missing headcount | 1 person |

## 9. Open questions

| # | Question | Needed for |
|---|---|---|
| 1 | Which CV file formats will be in `data/cvs/` (Word, PDF, text)? | Reading the CVs |
| 2 | The team list's columns, and how a person is linked to their CV file | Complete coverage and availability |
