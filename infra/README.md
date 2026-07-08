# infra — Infrastructure & Deployment

This folder contains everything needed to **run and deploy** the OpenUni stack.

## Planned contents

| File / folder | Purpose |
|---|---|
| `docker-compose.yml` | Local full-stack dev environment (API + web + vector DB) |
| `docker-compose.prod.yml` | Production overrides |
| `nginx/` | Reverse-proxy config |
| `k8s/` | Kubernetes manifests (future) |
| `.env.example` | Template for required environment variables |

## Getting started (coming soon)

```bash
cd infra
cp .env.example .env   # fill in your API keys
docker compose up
```

This will start:
- **API** on `http://localhost:8000`
- **Web** on `http://localhost:3000`
- **Vector DB** on its default port
