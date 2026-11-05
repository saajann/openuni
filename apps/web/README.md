# apps/web — Next.js Frontend

This package contains the **OpenUni web application**, built with [Next.js](https://nextjs.org/).

## Responsibilities

- Provide the student-facing chat interface and search UI.
- Render source citations alongside AI answers.
- Display the academic calendar, student dashboard, and document explorer.
- Talk exclusively to `apps/api` — no direct database or vector-store access.

## Structure

```
apps/web/
├── src/
│   ├── app/             # Next.js App Router pages & layouts
│   ├── components/      # Shared shell, chat workspace and calendar view
│   │   └── ui/          # shadcn/ui primitives (Button, Input, Select, …)
│   ├── lib/             # API client, utilities, types
│   ├── test/            # Vitest setup, fixtures and render helpers
│   └── app/globals.css  # Tailwind import, design tokens, legacy page rules
├── docs/                # design-system.md: tokens, typography, conventions
├── components.json      # shadcn/ui configuration
├── public/              # Static assets
├── next.config.ts
├── postcss.config.mjs   # Tailwind v4 PostCSS plugin
├── package.json
├── vitest.config.mts
└── README.md            # ← you are here
```

The root layout provides the shared OpenUni shell: a branded header with
keyboard-accessible links to **Ask** (`/`) and **Calendar** (`/calendar`), a compact
footer, page metadata and a skip link. Route pages stay server components that export
metadata and render the interactive client views from `src/components`.

Styling uses Tailwind CSS v4 with shadcn/ui primitives and semantic dark-first design
tokens. Read [`docs/design-system.md`](docs/design-system.md) before adding UI: use
the tokens and `src/components/ui` primitives, and no colour literals.

## Getting started

Ensure the backend API is running locally (usually on port 8000). The frontend expects the backend URL to be defined in `.env`. The project root `.env.example` already includes `NEXT_PUBLIC_API_URL`.

To run the frontend:

```bash
cd apps/web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the app.

## Checks

Run these before opening a pull request:

```bash
npm run lint
npm test
npm run build
```

`npm test` uses Vitest with jsdom. Tests mock `@/lib/api`, so they do not need
the API, Qdrant or Ollama running. Shared helpers live in `src/test`
(`fixtures.ts`, `render.tsx`, `setup.ts`).
