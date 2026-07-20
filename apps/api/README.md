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

## LLM Provider (v0)

**Provider**: [OpenAI Chat Completions API](https://platform.openai.com/docs/guides/chat)  
**Default model**: `gpt-4o-mini`

### Decision record

| Factor | Detail |
|---|---|
| Availability | Widely available API key, no self-hosting required for v0 |
| Instruction-following | Reliable adherence to the system prompt's grounding and citation rules |
| JSON mode | Native `response_format: {type: "json_object"}` removes the need to parse fenced code blocks |
| Cost | `gpt-4o-mini` is cost-efficient for short, grounded Q&A exchanges |
| Future switch | Provider is isolated to `app/rag/generation.py`; swapping to Anthropic/Gemini only requires updating that file |

### Alternatives considered

- **Anthropic Claude** — excellent instruction-following but requires an additional client library and no native JSON mode in older versions; deferred.
- **Local Ollama** — already used for embeddings; could unify the stack, but quality of citation following varies significantly by model; deferred.
- **Streaming** — token-by-token SSE/WebSocket streaming; deferred to a later issue to keep v0 simple.

### Setup

```bash
# Add to your .env (never commit real keys)
OPENAI_API_KEY=sk-...
# Optionally override the model
OPENAI_MODEL=gpt-4o-mini
```

The `generate_answer()` function in `app/rag/generation.py` accepts an optional
`client` parameter for dependency injection during testing — no real API key is
needed to run the unit-test suite.

