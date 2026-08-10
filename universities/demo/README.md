# universities/demo — Demo University

This is a **placeholder university configuration** used for local development, testing, and onboarding new contributors.

## Purpose

Every real university deployment will have its own folder under `universities/<slug>/` containing only configuration — no code changes required to add a new university.

## Planned structure

```
universities/demo/
├── config.yaml          # University metadata (name, locale, base URLs)
├── sources.yaml         # Document sources to ingest (URLs, crawl rules)
├── calendar.yaml        # Academic calendar entries (exams, deadlines, holidays, events)
├── prompts/             # University-specific system prompt overrides (optional)
└── README.md            # ← you are here
```

## Adding a real university

1. Copy this folder: `cp -r universities/demo universities/<your-slug>`
2. Fill in `config.yaml` with the university's name, locale, and branding.
3. List official document sources in `sources.yaml`.
4. Run the ingestion pipeline: `python scripts/ingest.py --university <your-slug>`
5. Submit a pull request — no application code changes needed.

## Academic Calendar (`calendar.yaml`)

Optionally include a `calendar.yaml` in the university folder to expose structured
academic dates (exams, enrollment deadlines, holidays, and events). Entries are
validated against the `CalendarEntry` model in the API and are intended for
listing, filtering, and calendar views.

Schema per item (YAML):

```yaml
- type: exam        # one of: exam, deadline, holiday, event
  title: "Final exam registration"
  date: 2026-06-01
  end_date: 2026-06-10   # optional inclusive end date for ranges
  description: "Registration window for final exams."
  source_url: "https://example.edu/academic-calendar"
```

Add at least one item per type for development/testing convenience. See
`calendar.yaml` in this demo folder for a minimal example.
