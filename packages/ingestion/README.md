# packages/ingestion — Document Ingestion Pipeline

This package contains the **offline ingestion pipeline** that turns raw university documents into searchable vector embeddings.

## Responsibilities

- Crawl and download official university documents (PDFs, HTML pages, structured data).
- Parse, clean, and chunk content into embedding-ready text segments.
- Generate embeddings via a configurable model (e.g. OpenAI, local model).
- Upsert vectors into the vector store (e.g. Pinecone, Qdrant, pgvector).
- Store document metadata (source URL, title, university slug, ingested-at timestamp).

## Project structure

```
packages/ingestion/
├── ingestion/
│   ├── chunking/        # Text splitting strategies (text_splitter.py)
│   ├── embeddings/      # Ollama embedding model client (ollama.py)
│   ├── loaders/         # Local document loader for pdf, txt, md (local.py)
│   ├── vector_store/    # Qdrant client & collection management (qdrant.py)
│   └── cli.py           # Ingestion CLI entrypoint
├── tests/               # Unit tests for chunking, embeddings, loaders, vector store
├── pyproject.toml
└── README.md            # ← you are here
```

## Getting started

```bash
cd packages/ingestion
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run ingestion for a university (e.g. demo)
python -m ingestion.cli --university demo
```
