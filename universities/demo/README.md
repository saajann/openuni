# universities/demo — Demo University

This is a **placeholder university configuration** used for local development, testing, and onboarding new contributors.

## Purpose

Every real university deployment will have its own folder under `universities/<slug>/` containing only configuration — no code changes required to add a new university.

## Planned structure

```
universities/demo/
├── config.yaml          # University metadata (name, locale, base URLs)
├── sources.yaml         # Document sources to ingest (URLs, crawl rules)
├── prompts/             # University-specific system prompt overrides (optional)
└── README.md            # ← you are here
```

## Adding a real university

1. Copy this folder: `cp -r universities/demo universities/<your-slug>`
2. Fill in `config.yaml` with the university's name, locale, and branding.
3. List official document sources in `sources.yaml`.
4. Run the ingestion pipeline: `python scripts/ingest.py --university <your-slug>`
5. Submit a pull request — no application code changes needed.
