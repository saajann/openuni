# Repository Guidelines

## Project Structure & Module Organization

This repo is split into three main areas:

- `apps/api/` — FastAPI backend, RAG orchestration, calendar endpoints, and tests.
- `apps/web/` — Next.js frontend, UI components, and browser-facing API helpers.
- `packages/ingestion/` — Offline document ingestion, chunking, embeddings, and Qdrant upserts.

University-specific config lives in `universities/<slug>/` (for example `universities/demo/`). Infrastructure and local deployment files live in `infra/`. Keep code, tests, and assets close to the package they belong to.

## Build, Test, and Development Commands

- `docker compose -f infra/docker-compose.yml up --build` — start the full local stack.
- `cd apps/api && uvicorn app.main:app --reload --port 8000` — run the API locally.
- `cd apps/web && npm run dev` — start the Next.js frontend.
- `cd apps/api && pytest` — run API tests.
- `cd packages/ingestion && pytest` — run ingestion tests.
- `cd apps/web && npm run lint` — lint the frontend.

## Coding Style & Naming Conventions

Use the repo’s existing formatters and linters: Ruff and Mypy for Python, ESLint and TypeScript for the web app. Follow the current style in each package: 100-character line length for Python, explicit type hints, and snake_case for Python modules/functions. Use PascalCase for React components and CamelCase types/interfaces. Prefer descriptive file names that match their purpose, such as `app/rag/retrieval.py` or `src/lib/api.ts`.

## Testing Guidelines

Tests use `pytest` on the Python side and are named `test_*.py` under each package’s `tests/` directory. Write focused tests for route behavior, config validation, and ingestion helpers. Mock external services such as OpenAI, Ollama, Postgres, and Qdrant unless the test is explicitly integration-level.

## Commit & Pull Request Guidelines

Commit messages follow a conventional style seen in history: `feat:`, `fix:`, `chore:`, and occasionally scoped forms like `test(ingestion): ...`. Keep commits small and focused. Pull requests should include a short summary, linked issue number when available, and screenshots or logs for UI/runtime changes. Mention any environment variables or setup steps needed to verify the change.

## Security & Configuration Tips

Never commit secrets. Use `.env.example` as the source of truth for local configuration. When changing API behavior, check `/health` and `/ready` expectations as well as any affected docs in `README.md` and `apps/api/README.md`.
