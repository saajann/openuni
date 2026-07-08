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
├── .gitignore
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

## Contributing

Each subdirectory has its own `README.md` explaining its purpose and planned structure.  
Start there, then check `docs/` for architecture context and contribution guidelines (coming soon).

---

## License

[MIT](./LICENSE)
