# Team list

Put the Excel list (`.xlsx`) of the ~80 people in the group here, with their availability. `.csv` also works. The contents of this folder are gitignored.

**Columns** are recognised by their header, in English or German. A title row above the headers is fine.

| Field | Recognised headers | Required |
|---|---|---|
| Name | Name, Full name, Mitarbeiter, or First name + Last name (Vorname + Nachname) | Yes |
| Availability | Availability, Verfügbarkeit, Free capacity. Values like `50%`, `0.5`, `free`, `booked`, `ja`, `nein`. | For availability checks |
| Available from | Available from, Verfügbar ab | Optional |
| Level | Level, Career level, Grade, Stufe. Shown for context, never used for ranking. | Optional |

If your headers are different, add `columns.json` to map them, e.g.:

```json
{"name": "Mitarbeitende", "availability": "Freie Kapazität Q4", "available_from": "Frei ab"}
```

**Manual CV links.** If a CV can't be linked automatically, or a probable match is wrong, add `cv_links.json`:

```json
{"CV_A_Mueller_final.pptx": "Anna Maria Müller"}
```
