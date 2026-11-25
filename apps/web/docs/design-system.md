# OpenUni web design system

Tailwind CSS v4 + shadcn/ui conventions for `apps/web`. Tokens live in
[`src/app/globals.css`](../src/app/globals.css); primitives in
[`src/components/ui`](../src/components/ui).

## Setup (reproducible)

- Tailwind v4 via `@tailwindcss/postcss` (`postcss.config.mjs`). There is no
  `tailwind.config`: v4 scans the project automatically (so no `content` paths to
  maintain) and the theme is declared in CSS with `@theme inline`.
- shadcn/ui is configured by [`components.json`](../components.json) (style
  `new-york`, base colour `zinc`, CSS variables, `@/components/ui` destination,
  `@/*` alias). To add a primitive: `npx shadcn@latest add <name>`, then replace any
  colour it hard-codes with the tokens below.
- `cn()` (`src/lib/utils.ts`) merges class names (`clsx` + `tailwind-merge`).

## Tokens

Dark-first: `<html class="dark">` and `color-scheme: dark`; there is no light theme yet.
Use the Tailwind names (`bg-surface`, `text-muted-foreground`, …) or `var(--token)`
in CSS. **Do not use colour literals in components or pages.**

| Token | Value | Use |
| --- | --- | --- |
| `background` / `surface` / `surface-raised` | `#0a0a0a` / `#111111` / `#1a1a1a` | page, cards and panels, inputs and nested cards |
| `foreground` | `#fafafa` | body text |
| `muted-foreground` | `#a1a1aa` | secondary text, labels |
| `link` | `#60a5fa` | links and source titles |
| `border` | `#27272a` | decorative dividers and card borders |
| `input` | `#71717a` | control boundaries (needs 3:1) |
| `ring` | `#60a5fa` | keyboard focus |
| `primary` / `primary-hover` / `primary-foreground` | `#2563eb` / `#1d4ed8` / `#ffffff` | main action |
| `success` | `#34d399` | positive status |
| `destructive` / `destructive-foreground` | `#ef4444` / `#f87171` | error border / error text |
| `cal-exam`, `cal-deadline`, `cal-holiday`, `cal-event` | `#60a5fa`, `#f87171`, `#34d399`, `#c084fc` | calendar categories (text; 15% tint as background) |

### Contrast (WCAG AA, computed)

Text needs 4.5:1, control boundaries and focus 3:1.

| Pair | Ratio |
| --- | --- |
| `foreground` on `background` | 18.97 |
| `muted-foreground` on `background` / `surface-raised` | 7.72 / 6.79 |
| `primary-foreground` on `primary` / `primary-hover` | 5.17 / 6.70 |
| `link` on `surface-raised` | 6.85 |
| `ring` on `background` / `surface-raised` | 7.79 / 6.85 |
| `input` border on `surface-raised` | 3.60 |
| calendar category text on its 15% tint (exam / deadline / holiday / event) | 5.33 / 5.04 / 6.74 / 5.17 |
| `destructive-foreground` on its 10% tint | 5.46 |

`primary` is `#2563eb`, not the earlier `#3b82f6`: white on `#3b82f6` is only 3.68:1.
Re-check the table when changing a token.

## Typography

- **Inter** (sans, body/UI) and **JetBrains Mono** (mono, dates and technical
  detail), both SIL Open Font License 1.1, so free for commercial use and
  redistribution.
- Loaded with `next/font/google` in `src/app/layout.tsx`: files are downloaded at
  build time and served from our own origin (no request to Google at runtime), Latin
  subset only, `display: swap`, exposed as `--font-inter` and `--font-jetbrains-mono`
  and mapped to `font-sans` / `font-mono`.
- Scale: Tailwind's default (`text-sm` 14px, `text-base` 16px, `text-xl`, …) with
  1.5 line height; never go below `text-xs` (12px) and keep body text at `text-sm`
  or larger.

## Components

- `Button` (`default`, `outline`, `ghost`; `size`; `block`; `asChild` to wrap a link),
  `Input`, `Select` (native), `Label`, `Alert` (`role="alert"`), `Badge` (calendar
  category variants).
- Focus: one global `:focus-visible` outline using `--ring`. Do not remove it; do not
  add per-component focus colours.
- Do not add a new `.class` to `globals.css` for something a primitive covers.

## Migration status

Legacy page rules (shell, chat results, calendar cards) remain in the
`@layer components` block of `globals.css`, already on tokens. Because they sit in a
lower layer, Tailwind utilities override them. Buttons, text fields, selects, labels,
alerts and calendar badges are fully on the primitives and their old rules are gone.
Remove the remaining legacy rules as each screen is rebuilt.
