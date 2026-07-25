# apps/web — Next.js Frontend

This package contains the **OpenUni web application**, built with [Next.js](https://nextjs.org/) (App Router, TypeScript).

## Responsibilities

- Provide the student-facing chat interface and search UI.
- Render source citations alongside AI answers.
- Talk exclusively to `apps/api` — no direct database or vector-store access.

Currently implemented (v0): a single page where a student can ask a question
and see the answer with its sources. The academic calendar, student
dashboard, and document explorer mentioned in earlier planning are not built
yet.

## Structure

```
apps/web/
├── src/
│   ├── app/              # Next.js App Router pages & layouts
│   └── lib/
│       └── api.ts        # Thin client for apps/api (sendChatMessage, getUniversities)
├── public/                # Static assets
├── next.config.ts
├── package.json
└── README.md              # ← you are here
```

## Getting started

Requires `apps/api` running locally (see [apps/api/README.md](../api/README.md)) — this app is a plain client with no backend of its own.

```bash
cd apps/web
cp .env.example .env.local   # NEXT_PUBLIC_API_URL defaults to http://localhost:8000
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). If `apps/api` isn't reachable, the page still loads — the university selector falls back to "demo" and submitting a question shows a clear error instead of crashing.

Note: `apps/api` doesn't allow browser requests from other origins by
default. Its `CORS_ORIGINS` setting already includes
`http://localhost:3000` (this app's default dev port) out of the box, so
this "just works" for local dev — you only need to change it if you run
`apps/web` on a different port or host.
