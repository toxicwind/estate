# README audit — toxicwind/sovereign-router-backup @ 621a6fda — 2026-09-14

**Verdict:** NEEDS UPDATE

Context: private repo, single commit ever (`621a6fda`, 2026-07-29, "sovereign-router backup from sovereign"). README is a verbatim copy of the monorepo's `tools/sovereign-router/README.md` — paths were never adjusted for this repo, whose root *is* the router dir. No recent changes to cross-check (no commits since the backup).

## Claims

| Claim (README section) | Evidence | Verdict |
|---|---|---|
| 7 strategies: hybrid/free/ast_race/sticky_affinity/weighted_elo/circuit_chain/fifo_matrix | `sovereign-router-ts/router.ts:341` (/ui dropdown lists all 7) | VERIFIED |
| `hybrid` default = sticky → ast_race → circuit_chain | `router.ts:7` "Default hybrid: sticky → ast_race → circuit_chain" | VERIFIED |
| Per-request strategy via `X-Sovereign-Strategy` | `router.ts:1329` | VERIFIED |
| sticky_affinity = 30-min session pinning | `router.ts:60` `STICKY_TTL = 1800` | VERIFIED |
| WAL health DB | `router.ts:410` `PRAGMA journal_mode=WAL` | VERIFIED |
| `free` strategy races local llama-swap + all `:free` cloud models | `router.ts:148-157` free pool; `router.ts:234-238` local aliases | VERIFIED |
| Example aliases `free`, `hy3`, `quality`, `nim-inkling` | `router.ts:240` hy3, `router.ts:267` nim-inkling, `router.ts:234-238` local-*; no bare `free` alias (it's a strategy) — examples loosely worded but grounded | VERIFIED |
| Endpoints: /v1/chat/completions, /v1/models, /health, /ui, /ui/data, /debug/health, /debug/sqlite, /mesh/* | `router.ts:1321,1262,1276,1267,1272,1306,1298,1254` | VERIFIED |
| Port via `SOVEREIGN_ROUTER_PORT` (:25104) | `router.ts:48-53` env required; 25104 not hardcoded — it's the documented deployment value | VERIFIED |
| `sovereign-ast-matrix-py/` = v2 Python reference | `router.ts:4` "Port of sovereign-router/router.py" | VERIFIED |
| Layout paths under `tools/sovereign-router/` | No `tools/` dir in this repo; mechanical check also flagged `tools/sovereign-router/` as missing | STALE |
| Run: `cd tools/sovereign-router/sovereign-router-ts` / `mise run up` | No `tools/` subdir; no mise config in this repo — neither command works from repo root | STALE |
| Naming note: "the directory is now `tools/sovereign-router`" | False for this repo (root = router dir) | STALE |
| "THE LIVE ROUTER (run by pitchfork :25104)"; canonical = Go port in `~/projects/llama-swap-main/internal/astmatrix/` | External claims; nothing in this tree confirms live deployment or the Go port | UNVERIFIED |

## Missing from README

- `sovereign-mcp-gateway/` (`gateway.ts`, `gateway-core.ts`) — undocumented in Layout; relationship to the router unclear.
- The whole README assumes the sovereign monorepo layout; as a standalone backup repo, every path/Run instruction needs the `tools/sovereign-router/` prefix dropped.

## Quickstart check

- [ ] Commands exist — `cd tools/sovereign-router/sovereign-router-ts` fails at repo root; should be `cd sovereign-router-ts`
- [x] Ports/config keys match code (`SOVEREIGN_ROUTER_PORT`)
- [ ] A fresh user could follow it end to end — `mise run up` has no mise config here; the direct `bun run router.ts` line works only after fixing the `cd`

## Action taken

- None (report only, per task rules). Suggested fix: strip the `tools/sovereign-router/` prefix from Layout/Run/naming-note, drop or qualify `mise run up`, and add a one-line note on `sovereign-mcp-gateway/`.
