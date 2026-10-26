# Consolidate GitHub search into Pylae ("main of pylae")

Status: staging. Owner: estate. Goal: make the estate's GitHub/GitHub-search
surfaces a first-class part of Pylae (`ranch/mesh/pylae`), the OpenAI-gateway /
mesh hub, so agents stop hand-flailing on raw `gh` CLI quirks.

## Staged set (evidence — grabbed from GitHub 2026-10-22)

Full enum: 707 repos owned by `toxicwind`. The GitHub-search "family" (9) is
cloned under `ranch/mesh/pylae/tmp/github-search-family/`:

- `github-advanced-search-mcp` (priv) — the GHAS MCP: high-recall client + API
  - Next frontend. This is the primary engine (Blackbird + REST dual-engine,
    `packages/{github-client,search-core,contracts}`).
- `github-search` (pub) — the standalone search repo (API+MCP on
  `:25112`/`:25113`; the vendored engine source).
- `hb-gh-search` (priv, Rust) — Rust-first GitHub search orchestrator (CLI +
  Axum HTTP/OpenAI facade + Vite SPA).
- `universal-search-fuzzer` (pub) — multi-source search router with fallback.
- `websearch-mcp` (priv) — web search MCP.
- `repo-first-class` (pub) — repo-first-class metadata/search.
- `github-grade` (priv) — GitHub-grade research lanes (citation graph, ...).
- `crawlee-python-toxicwind` (pub) — crawlee web scraping/browser automation.
- `awesome-osint-crawler` (priv) — OSINT crawler toolkit.

Distinguish two things: (a) the ENGINE/MCP that would have fed pylae's tool
surface (`github-advanced-search-mcp`'s `@ghas/*` packages, staged at
`tmp/github-search-family/`), and (b) related-but-separate search repos staged
for review.

> **SUPERSEDED (2026-10-22).** This plan proposed wiring GHAS into pylae. That
> target is wrong: pylae/OmniRoute is legacy (not running; its MCP-tool role was
> never merged into rhodochrosite, which is an LLM-only model gateway). The corrected,
> authoritative inventory + decision is
> `docs/github-search-consolidation-INVENTORY.md` — GHAS stays live standalone
> (`:25112`/`:25113`), and the engine lives at
> `ranch/github-search/packages/*` with a staged copy under
> `tmp/github-search-family/github-search/packages/`. Keep this plan only as
> historical rationale for the family-stage + the engine copy.

## Why (the flailing point)

Without a consolidated github-forward search, agents waste turns on: `gh
--page` flag drift, `run-fast`/kairos wrapper polluting stdout JSON, truncation
shims. Pylae as "github super-forward" removes that friction: one
`ghas_search_*`/`github_search_*` surface backed by real engines.

## Why

- Pylae already hosts GitHub tooling (`open-sse/mcp-server/tools/githubSkillTools.ts`
  - `src/lib/skills/githubCollector.ts`), but that only does skill discovery
    (`search/repositories?q=...`), not full code/issues/PR/commit search.
- The real search engine lives in `ranch/github-search/packages/github-client`
  (Blackbird + REST dual-engine: `searchGithubDetailed`, `searchGithub`,
  `searchIssues`, `getRepository`, `searchBlackbirdCode`) + `packages/search-core`
  (`buildResponse` ranking) + `packages/contracts` (`SearchCategory`).
- Consolidation = reuse that engine as Pylae-native MCP tools so the estate has
  ONE GitHub-search surface (pylae) that is "main", and the standalone repo
  becomes the reference/API serving the same packages.

## Inventory (evidence)

- `ranch/github-search/apps/mcp` — MCP server (HTTP :25113), tools in
  `apps/mcp/src/tools.ts` (`ghas_search_code/repositories/issues/pull_requests/...`),
  handlers in `apps/mcp/src/handlers.ts` (`performSearch`, `performCompare`,
  `dispatchTool`).
- `ranch/github-search/packages/github-client`, `packages/search-core`,
  `packages/contracts` — the engines.
- `ranch/mesh/pylae/open-sse/mcp-server/server.ts` — registers tool modules
  (`webTools`, `githubSkillTools`, `memoryTools`, ...). This is where we add the
  GHAS module.
- `ranch/mesh/pylae/open-sse/mcp-server/tools/githubSkillTools.ts` + `webTools.ts` —
  existing GitHub/web search; GHAS broadens code/issue/PR/commit coverage.

## Consolidation plan (additive, no regressions, real files, no monkeypatch)

1. Vendor the GHAS engine packages into pylae as `open-sse/ghas/` (copy from
   `ranch/github-search/packages/*` + contracts), keeping `@ghas/*` import local
   (node_modules-relative or workspace alias) so pylae is self-contained.
2. Add `open-sse/mcp-server/tools/ghasTools.ts` exposing `ghas_search_code`,
   `ghas_search_repositories`, `ghas_search_issues`, `ghas_search_pull_requests`,
   `ghas_search_commits`, `ghas_search_users`, `ghas_health` — backed by the
   vendored engines (dispatch to `searchGithubDetailed` per category).
3. Register the module in `open-sse/mcp-server/server.ts` alongside existing tools.
4. Keep `ranch/github-search` running (search-api :25112 + MCP :25113) — do NOT
   break it; it stays as the reference/standalone API + the vendored source of
   truth. Add a README pointer noting pylae now owns the consolidated client
   surface.
5. Verify: pylae MCP lists the new `ghas_search_*` tools and returns results for
   a known repository (`toxicwind/ranch`), without touching running services.

## Future-proof note

- Reuse over rewrite: do not reimplement Blackbird/REST; import the vendored
  engine. If `ranch/github-search` moves packages, update the vendored copy.
- Repo visibility: `toxicwind/ranch` is PUBLIC (verified) so both REST and
  Blackbird search reach our own code — no privacy wall.
