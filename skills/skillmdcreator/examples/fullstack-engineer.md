---
name: jane-doe-fullstack-engineer
description: Load when working on React, Node.js, PostgreSQL, or API design for web applications. Use for code reviews, architecture decisions, and debugging full-stack issues.
---

# Jane Doe — Senior Full-Stack Engineer

8 years building web applications, currently leading a team of 4 on a B2B SaaS product.

## Expertise areas

- **React** (5 years) — complex SPAs, custom hooks, React Query, Zustand for state
- **Node.js + Express** — REST APIs, background workers, queue processing with BullMQ
- **PostgreSQL** (6 years) — schema design, query optimisation, read replicas, partitioning
- **Redis** — caching layers, rate limiting, pub/sub patterns
- **AWS** — Lambda, ECS Fargate, S3, CloudFront, RDS, SQS
- **TypeScript** — strict mode everywhere, inferred types preferred over annotations
- **Testing** — Vitest for units, Playwright for E2E, integration tests that hit real databases

## How I work

- I favour **boring technology** — proven tools over trendy ones. No framework churn.
- I write **integration tests against real databases**, not mocks. Mocks mask migration bugs.
- I prefer **small, focused PRs** (under 400 lines) over bundled changes.
- I value **readability over cleverness** — if a junior can't understand it in 30 seconds, it's wrong.
- I read code **top-down**: entry point → call graph → details. Explain things in that order.
- I'm comfortable with **SQL directly** — don't default to ORM abstractions unless necessary.

## What I avoid

- Premature abstraction — three similar lines beats a speculative helper
- Feature flags for code I can just change
- Defensive code for scenarios that can't happen (validate at system boundaries, trust internal code)
- Comments that restate what the code does — only explain *why*

## Tooling preferences

- **Editor**: VS Code with Vim keybindings
- **Package manager**: pnpm (workspaces for monorepos)
- **Formatter**: Prettier with default config, no arguments
- **Linter**: ESLint with minimal custom rules
- **Git**: conventional commits, rebase-heavy workflow, no squash merges

## Current focus

Migrating a monolith to event-driven microservices — cautious incremental extraction, strangler-fig pattern, never a big-bang rewrite.

## When helping me

- Assume I know the basics; skip introductory explanations
- Show me the code first, explain second
- Flag trade-offs explicitly — don't just pick one approach silently
- If I'm doing something dangerous (dropping columns, force-pushing), stop and ask