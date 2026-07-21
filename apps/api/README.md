# apps/api — FastAPI Backend

This package contains the **OpenUni REST API**, built with [FastAPI](https://fastapi.tiangolo.com/).

## Responsibilities

- Expose HTTP endpoints consumed by `apps/web` (chat, search, document retrieval).
- Orchestrate calls to the vector store and language model.
- Handle authentication, rate-limiting, and request validation.
- Serve per-university configuration loaded from `universities/<slug>/`.

---

## Project structure

```
apps/api/
├── app/
│   ├── main.py          # FastAPI application entry-point & route definitions
│   ├── core/
│   │   └── config.py    # Pydantic-Settings config (reads env vars)
│   ├── routers/         # Route handlers (chat, search, health, …) — coming soon
│   ├── services/        # Business logic (RAG pipeline, LLM calls, …) — coming soon
│   └── models/          # Pydantic request/response schemas — coming soon
├── tests/
├── Dockerfile
├── pyproject.toml
└── README.md            # ← you are here
```

---

## Running via Docker Compose (recommended)

The easiest way to get the full stack running is through Docker Compose from
the **repo root**.  You only need **Docker** installed.

```bash
# 1. Clone the repo
git clone https://github.com/your-org/openuni.git
cd openuni

# 2. Create your local .env from the template
cp .env.example .env
# Edit .env if you want to change ports or credentials (defaults just work)

# 3. Start everything
docker compose -f infra/docker-compose.yml up --build
```

That's it.  Three services will be running:

| Service  | URL                       | Notes                          |
|----------|---------------------------|--------------------------------|
| API      | http://localhost:8000     | FastAPI app; `/docs` for Swagger |
| Qdrant   | http://localhost:6333     | Vector DB REST API & dashboard |
| Postgres | localhost:5432            | Use any Postgres client        |

### Verify the stack

```bash
# Liveness — should return {"status": "ok"}
curl http://localhost:8000/health

# Readiness — checks Postgres + Qdrant reachability
curl http://localhost:8000/ready
```

### Rebuild after code changes

```bash
docker compose -f infra/docker-compose.yml up --build
```

Or, if you have Docker Compose Watch enabled (Compose ≥ 2.22):

```bash
docker compose -f infra/docker-compose.yml watch
```

File changes under `apps/api/app/` are synced into the container automatically.

### Stop and remove containers

```bash
# Stop containers (keeps volumes)
docker compose -f infra/docker-compose.yml down

# Stop containers AND wipe all data (Postgres + Qdrant volumes)
docker compose -f infra/docker-compose.yml down -v
```

---

## Running locally (without Docker)

Requires Python 3.12+.

```bash
cd apps/api

# Create a virtual environment
python -m venv .venv && source .venv/bin/activate

# Install the package with all dependencies
pip install -e ".[dev]"

# Point to locally-running services (or override in your shell)
export DATABASE_URL="postgresql+psycopg://openuni:openuni@localhost:5432/openuni"
export QDRANT_URL="http://localhost:6333"

# Start the dev server with auto-reload
uvicorn app.main:app --reload --port 8000
```

---

## Environment variables

All configuration is read from environment variables.  See [`.env.example`](../../.env.example)
at the repo root for the full list with descriptions.

| Variable        | Default (Docker)                                          | Description                |
|-----------------|-----------------------------------------------------------|----------------------------|
| `DATABASE_URL`  | `postgresql+psycopg://openuni:openuni@postgres:5432/openuni` | PostgreSQL DSN          |
| `QDRANT_URL`    | `http://qdrant:6333`                                      | Qdrant REST base URL       |
| `ENVIRONMENT`   | `development`                                             | `development` or `production` |
| `API_PORT`      | `8000`                                                    | Host port mapped to the API |
| `POSTGRES_USER` | `openuni`                                                 | Postgres superuser         |
| `POSTGRES_PASSWORD` | `openuni`                                             | Postgres password          |
| `POSTGRES_DB`   | `openuni`                                                 | Postgres database name     |

---

## API endpoints

| Method | Path      | Description                                      |
|--------|-----------|--------------------------------------------------|
| GET    | `/health` | Liveness — always 200 if the process is running  |
| GET    | `/ready`  | Readiness — 200 only when DB + Qdrant are reachable |
| GET    | `/docs`   | Swagger UI (development mode only)              |
| GET    | `/redoc`  | ReDoc (development mode only)                   |

---

## LLM Provider

The generation step supports two providers, switchable via `LLM_PROVIDER` in your `.env`.
No code changes or restarts beyond updating the env file are required.

### Comparison

| Factor | `openai` (default) | `ollama` |
|---|---|---|
| **Setup** | API key required (`OPENAI_API_KEY`) | Ollama running locally, model pulled |
| **Cost** | Pay-per-token (`gpt-4o-mini` is cheap) | Free / self-hosted |
| **Offline** | ✗ requires internet | ✓ fully local |
| **JSON mode** | ✓ native, very reliable | ⚠ supported but varies by model |
| **Instruction-following** | Excellent | Good; depends on model size |
| **Recommended for** | Production, CI/CD, reliable structured output | Local dev without an API key |

> **Note on JSON mode with Ollama**: Ollama's `/v1` endpoint accepts
> `response_format: {type: "json_object"}`, but not all models honour it
> consistently. The existing `_parse_llm_response` fallback in
> `generation.py` will return the raw text if the response is not valid
> JSON, so the app stays functional even with less reliable models.

---

### Using OpenAI (default)

```bash
# In your .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...       # required
# OPENAI_MODEL=gpt-4o-mini  # optional override
```

### Using Ollama (local / offline)

```bash
# 1. Make sure Ollama is running and the model is pulled
ollama pull llama3.1

# 2. In your .env
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434   # or http://ollama:11434 inside Docker
# OLLAMA_MODEL=llama3.1             # optional override
```

> **Tip**: If you already run the Docker Compose stack, the `ollama` service
> is already included in `infra/docker-compose.yml` and `OLLAMA_URL` defaults
> to `http://ollama:11434` — no extra infrastructure needed.

---

### Decision record

| Factor | Detail |
|---|---|
| Default provider | OpenAI — widely available key, excellent JSON-mode, good quality/cost tradeoff |
| Provider isolation | All provider logic lives in `app/rag/generation.py`; callers (`app/routers/chat.py`) are unaffected |
| Shared client | Both providers use `openai.OpenAI`; Ollama is reached via its OpenAI-compatible `/v1` endpoint |
| Future providers | Adding Anthropic/Gemini follows the same pattern: add a branch in `_resolve_client_and_model()` |

### Alternatives considered

- **Streaming** — token-by-token SSE/WebSocket streaming; deferred to a later issue to keep v0 simple.
- **Auto-detect from env vars** — e.g. use Ollama if `OPENAI_API_KEY` is missing; rejected in favour
  of an explicit `LLM_PROVIDER` flag, which is easier to reason about and debug.

### Setup summary

The `generate_answer()` function in `app/rag/generation.py` accepts an optional
`client` parameter for dependency injection during testing — no real API key or
running Ollama instance is needed to run the unit-test suite.
