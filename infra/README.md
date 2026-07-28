# infra — Infrastructure & Deployment

This folder contains everything needed to **run and deploy** the OpenUni stack.

## Contents

| File / folder          | Purpose                                                  |
|------------------------|----------------------------------------------------------|
| `docker-compose.yml`   | Local full-stack dev environment (API + Qdrant + Postgres) |
| `docker-compose.prod.yml` | Production overrides *(coming soon)*               |
| `nginx/`               | Reverse-proxy config *(coming soon)*                     |
| `k8s/`                 | Kubernetes manifests *(coming soon)*                     |

---

## Getting started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose plugin on Linux)
- That's it — no Python, Node, or databases needed on your machine.

### 1. Copy the env template

From the **repo root**:

```bash
cp .env.example .env
```

The defaults in `.env.example` work out of the box for local dev.
Edit `.env` only if you need to change ports or use a different password.

### 2. Start the stack

```bash
docker compose -f infra/docker-compose.yml up --build
```

Three services start in order (Qdrant and Postgres first, API waits for both to be healthy):

| Service  | Host port | Image                  |
|----------|-----------|------------------------|
| qdrant   | 6333, 6334 | `qdrant/qdrant:latest` |
| postgres | 5432      | `postgres:16-alpine`   |
| api      | 8000      | Built from `apps/api/Dockerfile` |

### 3. Verify

```bash
# API liveness
curl http://localhost:8000/health
# → {"status": "ok"}

# Readiness (checks Postgres + Qdrant)
curl http://localhost:8000/ready
# → {"status": "ready", "checks": {"postgres": "ok", "qdrant": "ok"}}

# Swagger docs (development mode only)
open http://localhost:8000/docs
```

### Stopping the stack

```bash
# Stop containers (keeps volumes)
docker compose -f infra/docker-compose.yml down

# Stop containers AND wipe all data (Postgres + Qdrant volumes)
docker compose -f infra/docker-compose.yml down -v
```

---

## Environment variables

All configuration lives in `.env` at the repo root.
See [`.env.example`](../.env.example) for the full reference.

| Variable          | Default              | Description               |
|-------------------|----------------------|---------------------------|
| `POSTGRES_USER`   | `openuni`            | Postgres username         |
| `POSTGRES_PASSWORD` | `openuni`          | Postgres password         |
| `POSTGRES_DB`     | `openuni`            | Postgres database name    |
| `DATABASE_URL`    | *(derived)*          | Full DSN used by the API  |
| `QDRANT_URL`      | `http://qdrant:6333` | Qdrant base URL for the API |
| `API_PORT`        | `8000`               | Host port for the API     |
| `ENVIRONMENT`     | `development`        | `development` or `production` |
| `UNIVERSITIES_DIR` | `/app/universities` | Absolute path inside the container where university config folders are read from |

---

## Data persistence

Named Docker volumes are used so data survives container restarts:

- `qdrant_data` → `/qdrant/storage` inside the Qdrant container
- `postgres_data` → `/var/lib/postgresql/data` inside the Postgres container

Run `docker compose down -v` to delete them and start fresh.

---

## University configs

University configuration files live in the **repo-root `universities/`** directory and are
bind-mounted into the API container at `/app/universities` (read-only):

```yaml
# infra/docker-compose.yml (api service)
volumes:
  - ../universities:/app/universities:ro
environment:
  UNIVERSITIES_DIR: /app/universities
```

The API reads every sub-directory of `UNIVERSITIES_DIR` as a separate university on
startup (and on restart).

### Adding a new university

1. Create a sub-directory under `universities/` in the repo root:

   ```
   universities/
   └── my-uni/
       └── config.yaml
   ```

2. **No image rebuild is needed.** Because the directory is a bind-mount, the new
   folder is visible inside the container immediately.

3. Restart (not rebuild) the API container to pick up the change:

   ```bash
   docker compose -f infra/docker-compose.yml restart api
   ```

   Or, if you are running with `docker compose watch`, edits to any file inside
   `universities/` are synced into the container automatically:

   ```bash
   docker compose -f infra/docker-compose.yml watch
   ```

### Verifying universities are loaded

```bash
curl http://localhost:8000/universities
# → [{"id": "demo", ...}, ...]
```

If the response is an empty list, check the API logs:

```bash
docker compose -f infra/docker-compose.yml logs api | grep -i universit
```
