# request.json

Written by `/match-request` in step 3, and read by `cv-assessor`, `tools/verify_evidence.py` and `tools/rank.py`. A complete example is `tests/fixtures/run-rfp/request.json`.

```json
{
  "run_id": "2026-09-29-rfp-fullstack",
  "request_source": "data/requests/example-rfp-fullstack.md",
  "language": "en",
  "availability_required": false,
  "needed_from": null,
  "min_availability_pct": null,
  "seniority_mix_requested": "2 more junior, 2 more senior",
  "assumptions": ["\"German/English required\" read as both languages required."],
  "not_checkable": ["Security clearance"],
  "roles": [
    {
      "id": "role-1",
      "title": "Fullstack developer",
      "positions": 4,
      "requirements": [
        {
          "id": "R1",
          "text": "Java or Python",
          "class": "key",
          "kind": "skill",
          "alternatives": ["Java", "Python"],
          "reason": "Core language of the role; either one satisfies it."
        }
      ]
    }
  ]
}
```

| Field | Values and rules |
|---|---|
| `language` | `"en"` or `"de"`: the request's language, and the language of the report |
| `availability_required` | `true` only when the request asks for available people |
| `needed_from` | `YYYY-MM-DD` or `null` |
| `min_availability_pct` | Number 0–100 or `null` |
| `seniority_mix_requested` | The request's wording, or `null`. Recorded only, never ranked. |
| `roles[].positions` | Number of people for that role. Default 1. |
| `requirements[].id` | `R1`, `R2`, … unique across all roles |
| `requirements[].class` | `"key"`, `"nice"` or `"baseline"` |
| `requirements[].kind` | `"skill"`, `"experience"`, `"language"`, `"certification"` or `"other"`. Each required language is its own requirement with `kind: "language"`, so `rank.py` can recognise a language gap. |
| `requirements[].alternatives` | What also counts, including what "or similar" was taken to mean |
