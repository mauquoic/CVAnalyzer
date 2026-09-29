# CVs

Put the CVs here, one PowerPoint file (`.pptx`) per person. Subfolders are fine. `.docx`, `.pdf` and `.txt` also work, and old `.ppt` files work if LibreOffice is installed.

The contents of this folder are gitignored: CVs stay on the machine that runs the agent.

**Linking to the team list.** The agent finds each person's CV by their name in the file name (e.g. `CV Anna Müller.pptx`, `Mueller_Anna_2026-03.pptx`). If that fails, it looks for the name on the first slide. It tolerates:
- upper/lower case, word order and extra middle names (`Anna Maria Müller` = `Anna Mueller`);
- umlauts and accents (`Müller` = `Mueller` = `Muller`, `Weiß` = `Weiss`);
- words like "CV", "Lebenslauf", "Profil", and dates.

Near misses (e.g. `Jana` vs. `Jan`) are linked but flagged in the report for you to confirm. For anything the agent can't link, add the file to `data/team/cv_links.json`.

**Versions.** If a person has several CV files, the newest is used. The date is read from the file name (`_2026-03`) if present, otherwise from the file's last-saved date. A CV older than 12 months is flagged as possibly outdated.
