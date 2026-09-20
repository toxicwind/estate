# README audit — toxicwind/sovereign-router @ 96936b83 — 2026-09-14

**Verdict:** NEEDS UPDATE

Audited HEAD `96936b83` ("fix(ci): make agentic CI robust", 2026-09-04). Tarball via GitHub API (private; codeload redirect token required — the bare `/tarball/HEAD` endpoint 404s without following the redirect).

## Mechanical (bin/audit.py)

- readme-exists: PASS (3657 chars, 87 lines)
- mentioned-paths-exist: PASS (script parsed 0 paths from the fenced layout block — manual check below found real breakage)
- relative-links-resolve: PASS (none)
- versions-match-manifests: WARN on `127.0.0` — **false positive** (it's `127.0.0.1` in a dashboard URL)
- badge-workflows-exist: PASS
- quickstart-entrypoints-exist: WARN on `tools/sovereign-router/` — **real**, path doesn't exist in this repo
- external-links-alive: PASS

## Claims

| Claim (README section) | Evidence | Verdict |
|---|---|---|
| Multi-provider LLM routing gateway, OpenAI-compatible `/v1/chat/completions` | `sovereign-router-ts/router.ts:1321` POST handler; `:1247` Bun.serve | VERIFIED |
| Strategy failover, circuit breakers, sticky sessions, WAL health DB | `router.ts:1135-1146` ROUTERS; `:410` `PRAGMA journal_mode=WAL`; `:60` `STICKY_TTL=1800` | VERIFIED |
| Naming note: "the directory is now `tools/sovereign-router`" | No such path; repo root IS the router dir | WRONG |
| Layout tree rooted at `tools/sovereign-router/` | All named dirs exist but at top level without prefix; omits `sovereign-mcp-gateway/`, `src/`, `lib/`, `.github/`, `AGENTS.md` | WRONG (stale monorepo copy-paste) |
| `sovereign-router-ts/` = THE LIVE ROUTER, run by pitchfork :25104 | `router.ts` exists (46KB); no pitchfork/mise config in repo | VERIFIED / UNVERIFIED (pitchfork part) |
| `sovereign-ast-matrix-py/` v2 = reference / source-of-truth | exists; `router.ts:4` "Port of sovereign-router/router.py" | VERIFIED |
| `sovereign-ast-router/` v3 TS variant (reference) | exists | VERIFIED |
| `free_zed_gateway/` folded into `free` strategy | dir exists; `routeFree` + `freeCandidates()` race local + `:free` (`router.ts:1147+`) | VERIFIED |
| `ultimate_extract/` NOT router code | recovery scripts + log dumps | VERIFIED |
| `README_COMPLETE.txt` = original research notes | file at root | VERIFIED |
| Strategy table (hybrid/free/ast_race/sticky_affinity/weighted_elo/circuit_chain/fifo_matrix) | ROUTERS map `router.ts:1135-1146` + `/ui` select `:341` | VERIFIED |
| hybrid default: sticky → ast_race → circuit_chain | `router.ts:62` | VERIFIED |
| Per-request `X-Sovereign-Strategy` header | `router.ts:1329` | VERIFIED |
| `free` races local llama-swap + every `:free` cloud model | `freeCandidates()` `:1147+`; `:free` models in PROVIDER_MODELS `:145+` incl. `tencent/hy3:free`, `poolside/laguna-*`, `qwen/qwen3-coder:free`, `google/gemma-4-31b-it:free`, `nvidia/nemotron-3-*:free`, `nousresearch/hermes-3-*:free`, `openai/gpt-oss-20b:free` | VERIFIED |
| Local roles `local-fast`/`local-quality`/`local-longctx` | `LOCAL_ROLES` `router.ts:74-96`, `:146` | VERIFIED |
| Aliases `free`, `hy3`, `quality`, `nim-inkling` | `nim-inkling` `:267`; `hy3` via `tencent/hy3:free` `:148`; quality role `:79-96` | VERIFIED |
| Endpoints `/v1/chat/completions`, `/v1/models`, `/health`, `/ui`, `/ui/data`, `/debug/health`, `/debug/sqlite`, `/mesh/*` | all matched in fetch handler `router.ts:1247+` | VERIFIED |
| Run: `SOVEREIGN_ROUTER_PORT=25104 bun run router.ts` | `:48-53` env required; `:25104` consistent with sibling routers | VERIFIED |
| Run: `cd tools/sovereign-router/sovereign-router-ts` | path doesn't exist; should be `cd sovereign-router-ts` | WRONG |
| Run: `mise run up` starts daemon via pitchfork | no `mise.toml` in repo | UNVERIFIED (monorepo-context only) |
| Canonical/primary impl = Go port at `~/projects/llama-swap-main/internal/astmatrix/` | external path, not in this repo | UNVERIFIED |
| Dashboard `http://127.0.0.1:25104/ui` | `/ui`, `/ui/data` routes verified | VERIFIED |

## Missing from README

Real features/changes in recent commits with no README coverage:

- **Agentic Lens subsystem** — 9 of the last 11 commits (2026-09-03/04), zero README mention:
  - `lib/lens-orchestrator.js` (v2.0.0-agentic; auto-discovers `lens_*.js`)
  - `src/_11ty/lenses/`: `lens_cryptographic.js`, `lens_osint.js`, `lens_stylometric.js`, `lens_tectonic.js` (commits `24e97fe6`, `b3423cb2`, `5e85306f`, `7ec7411e`)
  - `.github/workflows/agentic-lens-ci.yml` ("Agentic Lens-First CI"), `tectonic-drift.yml` (commits `b3cb7d9a`, `cfcd10e9`)
  - agentic lens env config (`01416ddc`)
- `sovereign-mcp-gateway/` top-level dir — absent from layout
- `src/`, `lib/`, `.github/`, root `AGENTS.md` — absent from layout

## Sanitation check

Repo recently had kimi token files purged via Git API history rebuild. `find` for `*kimi*token*` / `*token*.json` returns nothing; README references no such files. Remaining `kimi` mentions are inside `ultimate_extract/` research-dump scripts only. PASS.

## Quickstart check

- [x] Router entrypoint exists (`sovereign-router-ts/router.ts`)
- [ ] `cd` path in quickstart is wrong (`tools/sovereign-router/sovereign-router-ts` → `sovereign-router-ts`)
- [ ] `mise run up` not runnable from this repo (no mise config)
- [x] Ports/config keys match code (`25104`, `SOVEREIGN_ROUTER_PORT`)
- [ ] A fresh user could follow it end to end — **no** (wrong cd path breaks it at step 1)

## Action taken

- None — report only per task rules. Recommended: fix layout paths to repo-root-relative, fix the `cd` line, and add a Lens section covering the orchestrator, the four lenses, and the two CI workflows. Core router documentation is otherwise accurate and needs no rewrite.
