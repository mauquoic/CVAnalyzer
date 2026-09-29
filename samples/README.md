# Sample data

A complete, fictional data set for trying out and demonstrating `/match-request` without real personal data. Run it with `/match-request data/requests/example-rfp-fullstack.md --samples`.

| Path | Contents |
|---|---|
| `cvs/` | 10 one-slide PowerPoint CVs. `Markus_Mustermann_-_202501.pptx` and `Manuela_Mustermann_-_08.2023.pptx` were provided by the resource manager. The other 8 were generated from Markus's template with `make_sample_cvs.py`. |
| `requests/` | Four test requests (T1–T4) used for the first end-to-end test runs on 29.09.2026. |
| `team/team_list.xlsx` | The team list with dummy levels, assignments and availability as of 29.09.2026. Generated with `make_team.py`. |

Designed test cases:
- **Availability:** Aylin Demir, Elena Rossi and Nikolai Petrov are available now. Tomasz Nowak is available from 13.10.2026 (in two weeks). Everyone else is staffed until 31.12.2026.
- **Name matching:** "Sophie Marie Keller" (list) vs. `Sophie_Keller_…` (file), and "Lukas Brändle" vs. `Lukas_Braendle_…`.
- **File-name dates:** the formats `202609`, `2026-03` and `04.2026`. Markus (01.2025), Manuela (08.2023) and Nikolai (12.2022) have outdated CVs.
- **Intended profiles for the RFP request** (the agent's assessment decides the actual tiers):
  - clear fits: Sophie Keller, Aylin Demir;
  - full stack but a German gap: Tomasz Nowak (German B1);
  - frontend only, with German A2: Elena Rossi;
  - data or backend focus, no frontend: Lukas Brändle, David Okafor;
  - junior, under 5 years: Julia Hofmann;
  - test automation, not development: Nikolai Petrov.

This folder is committed. Real data belongs in `data/`, which is gitignored.
