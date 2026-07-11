# OpenUni

> **Open-source AI assistant for university students.**

OpenUni lets students ask plain-language questions and get accurate, cited answers drawn exclusively from official university sources — regulations, degree programmes, deadlines, forms, FAQs, and more.

No more hunting through dozens of PDFs and web pages.  
Just ask, get an answer, see the source.

📖 Read the full product vision → [VISION.md](./VISION.md)

---

## Repo structure

```
openuni/
├── apps/
│   ├── api/          # FastAPI backend — REST endpoints, RAG orchestration, LLM calls
│   └── web/          # Next.js frontend — chat UI, search, student dashboard
│
├── packages/
│   └── ingestion/    # Offline pipeline: crawl → parse → embed → upsert to vector store
│
├── universities/
│   └── demo/         # Placeholder university config (copy this to add a new university)
│
├── infra/            # docker-compose, Nginx, deployment configs
├── docs/             # Architecture docs, ADRs, contribution guide
│
├── .github/
│   ├── ISSUE_TEMPLATE/ # Bug, feature & task issue templates
│   └── pull_request_template.md
├── .gitignore
├── CONTRIBUTING.md   # How to contribute
├── LICENSE
├── VISION.md
└── README.md         # ← you are here
```

### Where to put new code

| What you're working on | Where it lives |
|---|---|
| API endpoint or service | `apps/api/` |
| UI page or component | `apps/web/` |
| Document crawler / parser / embedder | `packages/ingestion/` |
| New university configuration | `universities/<slug>/` |
| Docker / deployment config | `infra/` |
| Architectural decisions or guides | `docs/` |

---

## Local development

You only need **Docker** installed.  No Python, Node, or databases required on your machine.

```bash
# 1. Clone the repo
git clone https://github.com/your-org/openuni.git
cd openuni

# 2. Copy the env template
cp .env.example .env

# 3. Start the full stack
docker compose -f infra/docker-compose.yml up --build
```

This brings up three services:

| Service  | URL                     | Notes                           |
|----------|-------------------------|---------------------------------|
| API      | http://localhost:8000   | `/docs` for interactive Swagger |
| Qdrant   | http://localhost:6333   | Vector DB dashboard             |
| Postgres | localhost:5432          | Any Postgres client works       |

Verify the API is healthy:

```bash
curl http://localhost:8000/health
# → {"status": "ok"}
```

See **[apps/api/README.md](./apps/api/README.md)** for more details (env vars, local-without-Docker setup, endpoint reference).

---

## Contributing

We welcome contributions of all kinds! Please read **[CONTRIBUTING.md](./CONTRIBUTING.md)** before opening an issue or pull request. It covers:

- Branch naming & commit message conventions
- How to open a focused, well-scoped PR
- Code style expectations

Each subdirectory also has its own `README.md` explaining its purpose and structure. Start there, then check `docs/` for architecture context.

---

## License

[MIT](./LICENSE)
