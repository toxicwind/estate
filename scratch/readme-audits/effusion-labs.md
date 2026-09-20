# README audit — toxicwind/effusion-labs @ a2feea8c — 2026-09-14

**Verdict:** NEEDS UPDATE

Method note: the API tarball endpoint 302-redirects to codeload.github.com
without a tokenized URL (404). Tree was instead rebuilt via
`GET /git/trees/main?recursive=1` (4106 entries, not truncated): all 3506 blob
paths materialized as placeholders, real content fetched for README.md,
package.json, .eleventy.js, netlify.toml, docs/AGENTIC-LENS-FIRST.md, and
services/mcp-stack/lens-server/package.json. Mechanical checks ran against
that reconstruction.

## Claims

| Claim (README section) | Evidence | Verdict |
|---|---|---|
| "static digital garden and studio site" (intro) | docs/AGENTIC-LENS-FIRST.md: "effusion-labs is **no longer a static site generator**. It is an **autonomous knowledge organism**" (2026-09-01) | STALE |
| Powered by Eleventy, Nunjucks, Tailwind CSS, Bun tooling (intro) | package.json: @11ty/eleventy 3.1.6, nunjucks 3.2.4, tailwindcss ^4.3.3, bun scripts throughout | VERIFIED |
| License ISC (badge + License section) | package.json `"license": "ISC"`; LICENSE in tree | VERIFIED |
| Prerequisites: Node >=22.19.0, Bun | package.json `engines.node >=22.19.0`; .nvmrc in tree | VERIFIED |
| `bun install` / `bun run dev` / `bun run build` / `bun run test` (Quickstart) | scripts dev→`eleventy --serve`, build→build:site→`NODE_ENV=production eleventy`, test→`c8 bun test/integration/runner.spec.mjs` — all present in package.json | VERIFIED |
| Common commands: check, quality:check, quality:apply, test:playwright, mcp:start | All five in scripts; mcp:start→services/mcp-stack/gateway/server.mjs exists in tree | VERIFIED |
| Project structure: src/, lib/, docs/, services/mcp-stack/, tools/ | All five dirs present in tree | VERIFIED |
| "Current build audit" → docs/build-output-weirdness-audit-2026-03-12.md | File exists; it is the only build-output audit in docs/ | VERIFIED |
| "builds to `_site/`, containerized via `.portainer/Dockerfile`" | netlify.toml `publish = "_site"`; .portainer/Dockerfile in tree | VERIFIED |

Mechanical (bin/audit.py): readme-exists PASS (1409 chars); mentioned-paths
PASS; relative-links PASS; versions PASS (no version strings in README);
badge-workflows PASS (no badges referencing workflows); quickstart-entrypoints
PASS; external-links PASS (ISC badge URL alive).

## Missing from README

Major feature area with zero coverage — 18 of the last 20 commits
(a4f7c08e…af77a1f2, 2026-09-01 to 2026-09-14):
- **Agentic lens-first architecture**: lib/lens-orchestrator.js, 11 build-time
  lenses in src/_11ty/lenses/ (semantic, stylometric, tectonic, quantum
  superposition, temporal drift, probabilistic, OSINT, cryptographic…),
  swarm DAG, vector embedding pipeline, WebSocket sync layer, knowledge graph
  adapter, consensus engine — documented as LIVE in docs/AGENTIC-LENS-FIRST.md.
- **Lens MCP server**: services/mcp-stack/lens-server/ (@effusion/lens-server
  2.0.0, server.ts) — runtime tool exposure of lens profiles, separate from
  the gateway server the README's `mcp:start` covers.
- Vite integration: @11ty/eleventy-plugin-vite + vite.config.mjs exist but
  Vite is absent from the stated stack.
- Netlify deployment: netlify.toml (`npm run build` → `_site`) exists but
  deployment notes mention only `.portainer/Dockerfile`.

## Quickstart check

- [x] Commands exist
- [x] Ports/config keys match code (no ports claimed; `dev` uses Eleventy's
      default :8080)
- [x] A fresh user could follow it end to end

## Action taken

- None — report only per task instructions. README needs its intro
  rewritten to the "autonomous knowledge organism" framing and a section
  covering the lens subsystem; quickstart/structure sections are accurate
  and should be kept.
