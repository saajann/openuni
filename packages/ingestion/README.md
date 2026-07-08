# packages/ingestion — Document Ingestion Pipeline

This package contains the **offline ingestion pipeline** that turns raw university documents into searchable vector embeddings.

## Responsibilities

- Crawl and download official university documents (PDFs, HTML pages, structured data).
- Parse, clean, and chunk content into embedding-ready text segments.
- Generate embeddings via a configurable model (e.g. OpenAI, local model).
- Upsert vectors into the vector store (e.g. Pinecone, Qdrant, pgvector).
- Store document metadata (source URL, title, university slug, ingested-at timestamp).

## Planned structure

```
packages/ingestion/
├── ingestion/
│   ├── crawlers/        # Per-source scrapers / downloaders
│   ├── parsers/         # PDF, HTML, and structured-data parsers
│   ├── chunkers/        # Text splitting strategies
│   ├── embedders/       # Embedding model wrappers
│   └── vector_store/    # Vector DB client abstraction
├── scripts/             # CLI entry-points (e.g. `ingest.py --university demo`)
├── tests/
├── pyproject.toml
└── README.md            # ← you are here
```

## Getting started (coming soon)

```bash
cd packages/ingestion
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python scripts/ingest.py --university demo
```
