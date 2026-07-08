# apps/web — Next.js Frontend

This package contains the **OpenUni web application**, built with [Next.js](https://nextjs.org/).

## Responsibilities

- Provide the student-facing chat interface and search UI.
- Render source citations alongside AI answers.
- Display the academic calendar, student dashboard, and document explorer.
- Talk exclusively to `apps/api` — no direct database or vector-store access.

## Planned structure

```
apps/web/
├── src/
│   ├── app/             # Next.js App Router pages & layouts
│   ├── components/      # Reusable React components
│   ├── lib/             # API client, utilities, types
│   └── styles/          # Global CSS / design tokens
├── public/              # Static assets
├── next.config.ts
├── package.json
└── README.md            # ← you are here
```

## Getting started (coming soon)

```bash
cd apps/web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the app.
