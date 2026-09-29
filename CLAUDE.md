# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

CVAnalyzer is at the specification stage of an agentic enablement lab. There is no application code, build, lint or test setup yet. Don't write implementation code until the build plan has been agreed with the user. The open questions in `docs/use-case.md` §8 have to be answered first.

## Use case: CV Match Agent

**Goal:** turn a staffing request (skills, experience, languages, headcount, seniority mix, optional availability) into a shortlist of people from the resource manager's group of about 80. Every match is backed by evidence from the person's CV. The resource manager makes the final decision.

- `docs/use-case.md` is the source of truth for behavior: capabilities, output contents, edge cases, acceptance criteria and open questions. Read it before designing or changing agent behavior.
- `docs/cv-match-agent-brief.html` is the pitch deck. It's the same use case, written for people.
- The reference test case is the RFP request on the deck's "The problem today · Real request" slide: 4 fullstack developers, 2 senior and 2 more junior, German and English, 9 skill lines.

### Constraints (non-negotiable)

- **Recommend only.** Never contact people, and never write to CV, HR or planning systems. Availability is read-only and only checked when the request needs it.
- **Evidence or no credit.** A requirement counts as met only with a CV quote. Inferred values are marked as inferred.
- **No protected attributes** (age, gender, nationality, photo, family status…) in matching or reasoning.
- **Complete coverage.** Every person on the team list is assessed, or listed as not assessed with a reason.
- **Never guess silently.** For ambiguous or contradictory requests, ask a question with a proposed default.
- **Personal data.** Never commit real CVs, team lists or availability data to this repo. Use anonymised or synthetic samples for development and tests.

### Conventions

- Requirement triage uses exactly three classes: **Key**, **Nice to have** (alternatives accepted) and **Baseline** (expected, tie-breaker only).
- Per-requirement assessment uses exactly three states: **met**, **partly met** and **not evidenced**.
- Output language follows the request language (English or German). CVs in either language are matched.

## The brief deck (`docs/cv-match-agent-brief.html`)

It's a single self-contained HTML file, presented as a click-through deck. It's also published as a claude.ai Artifact: https://claude.ai/artifact/Ltdmt8bphszgu2wEYNk7Da. Republishing the same file updates that link.

- **No document skeleton.** The file has no `<!doctype>`, `<html>`, `<head>` or `<body>` tags, because the Artifact publisher adds them. Keep it that way. Explicit rules like `.slide[hidden] { display: none; }` make it also render correctly when opened locally.
- **Slides.** Each slide is a `<section class="slide" data-title="…">` inside `<main id="stage">`. All slides except the first carry `hidden`. The inline script at the bottom builds the left-rail table of contents from `data-title` and assigns ids `s1…sN`. It also handles the Back/Next buttons, arrow/PageUp/PageDown/Home/End keys and `#sN` deep links. To add or reorder slides, edit the sections only. The counter and TOC update automatically.
- **Theming.** All colors are tokens on `:root`, redefined twice for dark mode (the `prefers-color-scheme` block and `:root[data-theme="dark"]`). A new color must be added to all three blocks.
- **Placeholders.** Values still to be supplied use `<span class="fill">[…]</span>`, shown as dashed amber chips. Run `grep -n 'class="fill"'` to find any that remain.
- **Embedded image.** The original request email is embedded as a base64 WebP data URI. Avoid printing that line in full when reading the file.
- **External resources.** Fonts load from Google Fonts only. Everything else is inline, as required by the Artifact CSP.
