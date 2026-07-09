# Contributing to OpenUni

Thank you for taking the time to contribute! 🎉  
OpenUni is an open-source project and we welcome improvements of all kinds — bug fixes, new features, documentation, university configurations, and infrastructure work.

Please read this guide before opening an issue or pull request so your contribution lands smoothly.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Branch Naming Convention](#branch-naming-convention)
4. [Commit Message Convention](#commit-message-convention)
5. [How to Open a Pull Request](#how-to-open-a-pull-request)
6. [Code Style & Linting](#code-style--linting)
7. [Repo Structure Cheatsheet](#repo-structure-cheatsheet)

---

## Code of Conduct

By participating you agree to abide by our [Code of Conduct](./CODE_OF_CONDUCT.md) (coming soon). In short: be kind, be constructive, and assume good faith.

---

## Getting Started

1. **Fork** the repository and clone your fork locally.
2. Create a branch from `main` following the naming convention below.
3. Make your changes, commit them using [Conventional Commits](#commit-message-convention), and push.
4. Open a pull request against `main` using the PR template that auto-fills when you open one.

> **Tip:** For large features, open a draft PR early so maintainers can give feedback before you invest too much time.

---

## Branch Naming Convention

Use one of the following prefixes, followed by a short kebab-case description:

| Prefix | When to use |
|--------|-------------|
| `feat/` | A new feature or user-facing addition |
| `fix/` | A bug fix |
| `chore/` | Build, tooling, dependency, or infrastructure changes |
| `docs/` | Documentation-only changes |
| `refactor/` | Code restructuring with no behaviour change |
| `test/` | Adding or fixing tests |

**Examples:**

```
feat/chat-streaming-response
fix/embedding-timeout-retry
chore/upgrade-nextjs-15
docs/add-contributing-guide
refactor/split-ingestion-pipeline
```

---

## Commit Message Convention

OpenUni follows **[Conventional Commits](https://www.conventionalcommits.org/)**.

### Format

```
<type>(<optional scope>): <short description>

[optional body]

[optional footer(s)]
```

### Types

| Type | When to use |
|------|-------------|
| `feat` | A new feature |
| `fix` | A bug fix |
| `chore` | Build process, tooling, or dependency updates |
| `docs` | Documentation only |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test` | Adding or correcting tests |
| `perf` | Performance improvement |
| `ci` | Changes to CI/CD configuration |

### Examples

```
feat(api): add streaming endpoint for chat responses
fix(ingestion): retry on 429 from embedding API
chore(deps): upgrade langchain to 0.2.0
docs: add architecture overview to docs/
refactor(web): extract ChatMessage into shared component
```

**Rules:**
- Use the **imperative mood** in the description ("add", not "added" or "adds").
- Keep the first line ≤ 72 characters.
- Reference related issues in the footer: `Closes #42` or `Refs #17`.

---

## How to Open a Pull Request

1. **Link to an issue.** Every PR should address an open issue. If no issue exists yet, open one first and get a thumbs-up from a maintainer before starting work on non-trivial changes.
2. **Keep PRs small and focused.** One logical change per PR makes review faster and reduces the risk of conflicts. Split large features into a series of smaller PRs if possible.
3. **Fill out the PR template.** When you open a PR, a checklist template will auto-fill — please complete all relevant sections.
4. **Request a review.** Assign at least one reviewer from the maintainers list once your PR is ready.
5. **Respond to feedback.** Address review comments with follow-up commits or replies. Mark threads as resolved after addressing them.
6. **Squash on merge.** Maintainers will squash-merge PRs to keep the history clean. Your commit message on the PR title will become the squash commit — make sure it follows the Conventional Commits format.

---

## Code Style & Linting

> ⚠️ **Placeholder — linting tooling is not yet configured.**  
> This section will be updated once linters and formatters are set up for each sub-project.

### General expectations (applies now)

- **Python** (`apps/api/`, `packages/ingestion/`): follow [PEP 8](https://peps.python.org/pep-0008/). We plan to adopt **Ruff** for linting and formatting.
- **TypeScript / JavaScript** (`apps/web/`): follow standard React/Next.js conventions. We plan to adopt **ESLint** + **Prettier**.
- Avoid committing debug prints, commented-out code blocks, or TODO comments that belong in an issue.
- All new public functions and modules should have docstrings / JSDoc comments.

Once linting is configured, CI will enforce it automatically and PRs that fail lint checks will not be merged.

---

## Repo Structure Cheatsheet

| What you're working on | Where it lives |
|---|---|
| API endpoint or service | `apps/api/` |
| UI page or component | `apps/web/` |
| Document crawler / parser / embedder | `packages/ingestion/` |
| New university configuration | `universities/<slug>/` |
| Docker / deployment config | `infra/` |
| Architecture decisions or guides | `docs/` |

See the root [README.md](./README.md) for the full directory layout.

---

*Have questions? Open a [Discussion](../../discussions) or ping a maintainer in an issue. We're happy to help!*
