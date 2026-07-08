# apps/api — FastAPI Backend

This package contains the **OpenUni REST API**, built with [FastAPI](https://fastapi.tiangolo.com/).

## Responsibilities

- Expose HTTP endpoints consumed by `apps/web` (chat, search, document retrieval).
- Orchestrate calls to the vector store and language model.
- Handle authentication, rate-limiting, and request validation.
- Serve per-university configuration loaded from `universities/<slug>/`.

## Planned structure

```
apps/api/
├── app/
│   ├── main.py          # FastAPI application entry-point
│   ├── routers/         # Route handlers (chat, search, health, …)
│   ├── services/        # Business logic (RAG pipeline, LLM calls, …)
│   ├── models/          # Pydantic request/response schemas
│   └── core/            # Settings, logging, dependency injection
├── tests/
├── Dockerfile
├── pyproject.toml
└── README.md            # ← you are here
```

## Getting started (coming soon)

```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```
