# Triage guide

Every requirement line gets exactly one class. When in doubt, choose the less strict class and say why. A requirement wrongly marked key hides good people. One wrongly marked nice to have only changes the order.

## Classes

| Class | Meaning | Typical signals |
|---|---|---|
| **Key** | Must be evidenced for a strong fit | The core language or framework of the role title; "required", "must", "zwingend", "Voraussetzung"; explicit minimum years; required languages |
| **Nice to have** | Raises the ranking; alternatives accepted | "would be great", "ideally", "plus", "wünschenswert", "von Vorteil"; "or similar"; long lists of tools; specialist add-ons to the role |
| **Baseline** | Expected of nearly everyone in the role and rarely on CVs; used only as a tie-breaker | Git, code reviews, agile/Scrum, Office tools, "team player" |

## Rules

1. **The role title decides the core.** For "Fullstack developer", one backend language and one frontend framework are key. For "Data engineer", Spark or similar would be key.
2. **"X or Y"** is one requirement. Either one fully satisfies it. List both under `alternatives`.
3. **"X or similar"** is usually nice to have. Put the concrete technologies you will accept in `alternatives` (see `skill-alternatives.md`) so the user can reject them in the confirmation step.
4. **Languages.** One requirement per language, each `kind: "language"`. "German/English" means both, which is a stated assumption.
5. **Experience.** "More than N years in this area" is key, `kind: "experience"`, counted in the relevant field, not total career. State this as an assumption.
6. **Seniority mix** ("2 junior, 2 senior") is not a requirement. Put it in `seniority_mix_requested`.
7. **Soft skills and vague items** ("communication", "AI skills") are nice to have, unless the request says required. Be concrete in `alternatives` about what you will count.
8. **Things CVs can't show** (clearance, rate, location, start date, notice period) go into `not_checkable`, not into requirements.
9. **Availability.** "Don't have to be available" or an RFP sample team means `availability_required: false`. "Start on…" or "for a project from…" means `true`, with `needed_from`.
10. **Keep the requester's wording** in `text`, shortened. Don't add requirements the request doesn't state.

## Example: the RFP request (`tests/fixtures/run-rfp/`)

| Requirement | Class | Why |
|---|---|---|
| Java or Python | Key | Core backend language; either one |
| TypeScript / Angular | Key | Fullstack needs a frontend |
| > 5 years in the area | Key | Hard number |
| German · English | Key (2 language requirements) | "required" |
| REST APIs or web services | Key | Standard backend expectation |
| Git workflow and code reviews | Baseline | Expected of everyone |
| Spark / Spark SQL or similar | Nice to have | "or similar" |
| Data pipelines, ETL/ELT | Nice to have | Adds value; fullstack first |
| Containers, Kubernetes or cloud | Nice to have | Listed with "or" |
| AI tooling in the SDLC | Nice to have | "would be great" |

Seniority mix "2 more junior, 2 more senior" → `seniority_mix_requested`. Availability not required.
