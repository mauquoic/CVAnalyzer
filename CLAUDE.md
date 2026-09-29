# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

CVAnalyzer is at the use-case framing stage of an agentic enablement lab. There is no application code, build, lint or test setup yet. The only content is the use case brief for the planned **CV Match Agent**. The agent will match staffing requests (skills, experience, languages, headcount, seniority mix) against the CVs of a group of about 80 people.

The brief in `docs/cv-match-agent-brief.html` is the source of truth for the agent's intended behavior and scope:
- **Requirement triage.** Classify each request line as key, nice to have (alternatives accepted) or baseline.
- **Availability check.** Read-only, and only when the request needs it.
- **Evidence-based scoring.** Every match must cite CV text.
- **Team proposal.** Ranked shortlist per role or seniority slot, with gaps.
- **Clarifying questions** when a request is ambiguous.
- **Out of scope:** contacting people and changing HR records.

Keep future implementation work consistent with it.

## The brief deck (`docs/cv-match-agent-brief.html`)

It's a single self-contained HTML file, presented as a click-through deck. It's also published as a claude.ai Artifact: https://claude.ai/artifact/Ltdmt8bphszgu2wEYNk7Da. Republishing the same file updates that link.

- **No document skeleton.** The file has no `<!doctype>`, `<html>`, `<head>` or `<body>` tags, because the Artifact publisher adds them. Keep it that way. Explicit rules like `.slide[hidden] { display: none; }` make it also render correctly when opened locally.
- **Slides.** Each slide is a `<section class="slide" data-title="…">` inside `<main id="stage">`. All slides except the first carry `hidden`. The inline script at the bottom builds the left-rail table of contents from `data-title` and assigns ids `s1…sN`. It also handles the Back/Next buttons, arrow/PageUp/PageDown/Home/End keys and `#sN` deep links. To add or reorder slides, edit the sections only. The counter and TOC update automatically.
- **Theming.** All colors are tokens on `:root`, redefined twice for dark mode (the `prefers-color-scheme` block and `:root[data-theme="dark"]`). A new color must be added to all three blocks.
- **Placeholders.** Values still to be supplied use `<span class="fill">[…]</span>`, shown as dashed amber chips. Run `grep -n 'class="fill"'` to find any that remain.
- **Embedded image.** The original request email (the example on the "The problem today · Real request" slide) is embedded as a base64 WebP data URI. Avoid printing that line in full when reading the file.
- **External resources.** Fonts load from Google Fonts only. Everything else is inline, as required by the Artifact CSP.
