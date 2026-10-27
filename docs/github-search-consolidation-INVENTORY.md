# GitHub-Search Consolidation — Complete Inventory (2026-10-22)

Evidence-driven inventory of every GitHub-search-related repo/tooling in the
estate, with per-surface: what it searches / provider / interface / overlap,
and the consolidate decision. Keeps the live GHAS MCP (:25113) + search-api
(:25112) running. All family repos are staged at
`ranch/mesh/pylae/tmp/github-search-family/`.

## ARCHITECTURE CORRECTION (2026-10-22) — pylae is NOT the target

Investigation resolved the earlier premise confusion:

- **pylae/OmniRoute** (`ranch/mesh/pylae`, `@omniroute/*`) is LEGACY — it is NOT
  running (ports 25105-25107 are prometheus-mesh / gibber-mcp / null-g-proxy,
  not pylae). An attempted GHAS→pylae MCP wiring was made, then REVERTED.
- **rhodochrosite** (`ranch/rhodochrosite`, `:25193`) is the LIVE router, but only an **LLM/NIM
  model gateway**: its config store shows `upstream` (NVIDIA NIM), `providers`,
  `routing`, `client_auth`, `governor` — it routes model/LLM API, NOT GitHub
  search. It has no search route and no MCP tool surface.
- So the user's "OmniRoute merged into rhodochrosite" is TRUE for the **model-gateway
  role only**; the **MCP-tool/search role** is a separate concern rhodochrosite does not
  host, and pylae's version is orphaned.
- => **GitHub search stays where it's LIVE and works**: the standalone
  `github-search` MCP (`:25113`) + search-api (`:25112`) + the canonical
  `github-advanced-search-mcp` repo. Do NOT wire GHAS into pylae (legacy) NOR
  rhodochrosite (model-gateway, wrong layer) without user direction.
- Future home (unresolved, needs user): if agents want ONE github-forward search
  in the mesh, it belongs on a DEDICATED GHAS-backed service (or a route rhodochrosite
  proxies to), not pylae/rhodochrosite directly. Engine to reuse: the canonical
  `github-search` packages staged at
  `ranch/mesh/pylae/tmp/github-search-family/github-search/packages/`
  (`github-client`, `search-core`, `contracts`).

## The KEEP / PRIMARY surface

| Repo                                           | Surface                                                                   | Searches                                              | Provider                                                         | Interface                                                 | Decision                                                                                              |
| ---------------------------------------------- | ------------------------------------------------------------------------- | ----------------------------------------------------- | ---------------------------------------------------------------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `github-advanced-search-mcp` (priv, canonical) | GHAS engine: Blackbird + classic REST dual-engine                         | code, repos, issues, PRs, commits, users, discussions | github.com/search (Blackbird UI index) + GitHub REST `/search/*` | MCP (:25113) + REST API (:25112) + Next frontend (:25114) | **KEEP — primary**                                                                                    |
| `github-search` (pub, vendored copy)           | `packages/{search-core,github-client,contracts}` + apps{api,mcp,frontend} | same as above                                         | same                                                             | same                                                      | **KEEP — engine source (canonical copy staged at `tmp/github-search-family/github-search/packages`)** |

These two are the SAME engine (github-search is the source; advanced-search-mcp
is the canonical export). The engine's canonical source is staged (not absorbed
into a legacy home) at `ranch/mesh/pylae/tmp/github-search-family/github-search/packages/`.

## Overlap — candidates to deprecate / point at GHAS

| Repo                            | Surface                                                                          | Searches             | Provider         | Overlap                               | Decision                                                                              |
| ------------------------------- | -------------------------------------------------------------------------------- | -------------------- | ---------------- | ------------------------------------- | ------------------------------------------------------------------------------------- |
| `hb-gh-search` (priv, Rust)     | `hb-gh-search-cli` (CLI) + `-core` + `-web` (Axum HTTP/OpenAI facade + Vite SPA) | GitHub (repos, code) | GitHub API       | Full GitHub-search overlap with GHAS  | **DEPRECATE toward GHAS** (or keep as a Rust facade fronting GHAS API)                |
| `universal-search-fuzzer` (pub) | search router                                                                    | multi-source (web)   | multi (fallback) | Overlaps forge fetch/native providers | **CONSOLIDATE** — fold as a provider behind GHAS/pylae unified search, not standalone |
| `websearch-mcp` (priv)          | python `server.py` MCP                                                           | web (ddg-style)      | DuckDuckGo/etc   | Web-search MCP                        | **CONSOLIDATE** — one unified web + code search MCP in pylae                          |

## Distinct-purpose repos — KEEP separate (not GitHub-search consolidation)

| Repo                             | Purpose                                                              | Decision                           |
| -------------------------------- | -------------------------------------------------------------------- | ---------------------------------- |
| `repo-first-class` (pub)         | repo metadata / search-first-class                                   | KEEP (distinct)                    |
| `github-grade` (priv)            | research citation-graph lanes (build_graph.py, validate_edges.py)    | KEEP (research)                    |
| `crawlee-python-toxicwind` (pub) | upstream apify/crawlee-python fork (web scraping/browser automation) | KEEP (library)                     |
| `awesome-osint-crawler` (priv)   | Bing curl+regex crawler; README admits packaged toolkit missing      | **LEGACY** — retire/link, not core |

## Consolidation decision (final)

1. **Engine stays canonical + staged** (pylae is legacy, not the home): the
   GHAS engine source lives in `ranch/github-search/packages/*` and the staged
   copy at `ranch/mesh/pylae/tmp/github-search-family/github-search/packages/`.
   Any future consolidated home (dedicated service / rhodochrosite-proxied route)
   imports from those, not a dead `packages/ghas/`.
2. **Live surfaces unchanged**: GHAS MCP :25113 + search-api :25112 keep running
   (do not break).
3. **hb-gh-search / universal-search-fuzzer / websearch-mcp** — point at the
   unified GHAS/pylae search rather than being separate entrants. Not deleted;
   linked/retired in docs.
4. **awesome-osint-crawler** — flag as legacy/known-degraded (packaged toolkit
   missing), keep as historical.
5. **What stays standalone**: repo-first-class, github-grade, crawlee-python.

## Why this matters (the flailing point now resolved)

Agents were hand-driving raw `gh` CLI (flag drift, `run-fast`/kairos stdout
pollution, truncation shims). The consolidated GHAS→pylae surface removes that:
one `ghas_search_*` MCP tool set backed by the real dual-engine.

## Status

- Staging complete: family cloned to `ranch/mesh/pylae/tmp/github-search-family/`;
  canonical engine source at `ranch/github-search/packages/*` (diff-verified);
  inventory above written.
- Next (not done): register a `ghasSearchTools` module in
  `open-sse/mcp-server/server.ts` and retire/link the deprecated repos' docs.
