# README audit — toxicwind/sovereign-projects @ 91cb84a1 (main) — 2026-09-14

**Verdict:** NEEDS UPDATE

Method: tarball endpoint 404'd (repo is 557 MB), so the mechanical checks from
`bin/audit.py` were run adapted against the recursive git-tree API (37,608
entries, not truncated) plus targeted `contents` API fetches of
`config/ports.env`, `pitchfork.toml`, `mise.toml`, `package.json`. REPORT ONLY —
nothing edited, committed, or pushed.

## Claims

| Claim (README section) | Evidence | Verdict |
|---|---|---|
| Orchestration: `mise` + `pitchfork` | `mise.toml`, `pitchfork.toml` exist in tree | VERIFIED |
| LLM front door llama-swap **:25100** (toxicwind fork) | `pitchfork.toml` `[daemons.herd]` `ready_http = http://127.0.0.1:25100/health` | VERIFIED |
| Ports SSOT `config/ports.env` | exists; all service ports below cross-checked against it | VERIFIED |
| No Caddy, no landing service | no caddy/landing in pitchfork daemons or tree | VERIFIED |
| Quickstart `mise run up/down/health/status/doctor` | `mise/tasks/{up,down,health,status,doctor}` all exist | VERIFIED |
| Chat UI `:25100/ui`, API `:25100/v1` | consistent with herd daemon :25100 | VERIFIED |
| Ops dashboard `:25101`, `/ops/api/status` | `RUST_WEB_PORT=25101` in ports.env | VERIFIED |
| OpenFang UI `:25103`, API `:25203` | pitchfork openfang `:25103`; `OPENFANG_API_PORT=25203` | VERIFIED |
| HF Downloader `:25106`, Grafana `:25110`, Prometheus `:25105`, null-g-proxy `:25107`, ghas-api `:25112`, byte-vision `:25121`, redis `:25199`, Qdrant `:25133` | all match pitchfork daemons / ports.env | VERIFIED |
| MCP Gateway `:25120/health` | pitchfork `[daemons.mcp-gateway]` `:25120` (named mcp-gateway, README calls it byte-vision-proxy) | VERIFIED |
| Mesh Hub `:25115` | pitchfork `[daemons.mesh-hub]` `:25115` | VERIFIED |
| `src/mcp/llama_swap.ts` (MCP stdio wrapper) | exists in tree | VERIFIED |
| `tools/sovereign-router/sovereign-router-ts/router.ts` | exists in tree | VERIFIED |
| `tools/sovereign-monitor/{recursive-fallback,watchdog,repo-radar}.ts` | all three exist | VERIFIED |
| `tailscale/README.md`, `src/lib/ports.ts`, `stack/lib-ports.sh`, `rust_algo_web/` | all exist | VERIFIED |
| mcpproxy **:25109** "MCP federation (43 MCPs → 1 endpoint)" | pitchfork runs mcpproxy-go on **:25127** (`[daemons.mesh]`, `MCPPROXY_GO_PORT=25127`); `:25109` appears nowhere in ports.env or pitchfork | STALE |
| sovereign-router **:25104** in `mise run up` table | no 25104 in ports.env, no pitchfork daemon | STALE |
| Binary launcher `stack/services/llama-swap.ts` | only `stack/services/llama-swap.sh` exists | STALE |
| `tools/llama-swap/config.yaml` = "Model matrix, macros, backends" | `tools/llama-swap/` is **empty**; neither config.yaml nor config.yml exists (commit `ef59448f` renamed yaml→yml, but the file itself is gone) | STALE |
| `tools/llama-swap/README.md` (Related forks) | dir empty | STALE |
| Backends `LLAMA_START_PORT`–`LLAMA_END_PORT` = **25001–25099** | no `LLAMA_START/END_PORT` in ports.env; backends are `BEELLAMA_PORT=25122`, `IK_LLAMA_PORT=25123`, `TURBO_PORT=25124` | STALE |
| pitchfork.toml "native config, no generation" | file header: "GENERATED from config/ports.env + service definitions" | STALE |
| `bun test` = "all tests (131+ tests across 9 files)" | `tests/` has **8** files; package.json `test` script runs only `tests/open_web_uis.test.ts` | STALE |
| `grafana/provisioning/` "plugins/ + alerting/ dirs" | only `dashboards/` + `datasources/` exist | STALE |
| Workspaces table: OpenFang = "C++ inference engine fork" | OpenFang is RightNow-AI's **Rust Agent OS**; README's own services table says "Agent kernel — OpenFang OS" | WRONG |
| Zed custom providers `crates/language_models/src/provider/*.rs` | no `crates/` dir in repo; providers live in the separate Zed fork (`/home/toxic/projects/zed`) | WRONG |
| `:25130` claimed twice: itvx-browserless (services table) and QED (Workspaces table) | ports.env: `ZEDRA_HOST_PORT=25130`; one port, two owners in the doc | WRONG |
| "MCP federation" on :25109 (services table) vs :25127 (Workspaces table) | pitchfork: :25127; README contradicts itself | WRONG |
| mcpproxy "43 MCPs" vs Zed section "30+ MCPs" | internally inconsistent; config at `/home/toxic/.mcpproxy/mcp_config.json` is outside the repo | WRONG |
| Project layout: `bin/llama-swap` symlink | missing from tree | WRONG |
| Project layout: `backup/` dir | missing from tree | WRONG |
| Workspaces table: `shell/`, `boundless/` subfolders | both dirs missing from tree | WRONG |
| openfang "206 models, 61 skills, Discord bridge" | `openfang/` contains only `README.md`; no supporting evidence in tree | UNVERIFIED |
| itvx-telemetry `:25198`, itvx-browserless `:25130` (Docker) | zero `itvx` hits in 37k-entry tree | UNVERIFIED |
| Quickshell Screenshot Integration section | all paths under `~/.config/quickshell/`, none in repo | UNVERIFIED |
| Zed Provider Integration (providers, bounty models, OpenCode) | describes `~/.config/zed/settings.json`, external to repo | UNVERIFIED |
| Inference chain `internal/astmatrix/` at `~/projects/llama-swap-main` | external repo, not this tree | UNVERIFIED |
| "40+ model aliases", "7 providers", "6 strategies", ELO/SQLite claims | code lives in llama-swap fork, not here | UNVERIFIED |
| Monitor coverage numbers (88%+, 100%, 100%) | files exist; numbers not re-derived | UNVERIFIED |
| "All public-facing services bind to 0.0.0.0" | pitchfork: mcpproxy-go listens on `127.0.0.1:25127`; mixed in practice | UNVERIFIED |
| Tau `:25192` | `PI_WEB_DASHBOARD_PORT=25192` in ports.env but no daemon serves it; `[daemons.tau]` is a CLI with no HTTP port | UNVERIFIED |

## Missing from README

Real features, renames, or config changes in recent commits with no README coverage:

- **coyote :25143** — pitchfork daemon + `COYOTE_PORT=25143` + `stack/services/coyote.sh` + `hal-substrate.sh` compat shim; **5 of the last 20 commits** are the hal-substrate→coyote rename (`10623baa`, `78cb99a5`, `06f52c28`, `f763c8e6`, `91cb84a1`). Zero README mentions.
- **kimi-code :25126** — pitchfork daemon (`bun run dist/main.mjs web --port 25126`), commit `669752b2`. Zero mentions.
- **tau-code :25145** — pitchfork daemon; note ports.env says `TAU_CODE_PORT=25144` while pitchfork uses 25145 (config drift; pitchfork also assigns 25144 to kafka).
- **nginx daemon :62200** — pitchfork-managed reverse proxy; the "Why no Caddy" section doesn't mention what, if anything, replaced that role.
- **packages/** (`sovereign-scripts`, `sovereign-skills`, `utils`) — absent from Workspaces table; commit `531f7dab` repointed the launcher at `engine/packages` after packages deprecation.
- **ghas-mcp :25113** is listed under `mise run up` but has no pitchfork daemon (port only in ports.env) — README overstates what's orchestrated.
- **openfang/README.md on main** still contains the old wrong "C++ inference engine" text (corrected only on `kimi-collab-transport`, commit `c807f56729`, not merged to main).
- search-api/search-ui (pitchfork names) vs ghas-api/ghas-mcp (README names) naming drift.

## Quickstart check

- [x] Commands exist (`mise/tasks/up|down|health|status|doctor`)
- [~] Ports/config keys match code (mostly; :25109, :25104, :25001–25099 range, `llama-swap.ts`, `config.yaml` are stale)
- [~] A fresh user could follow it end to end (`cd /home/toxic/sovereign` assumes local dir name; prerequisites like Bun/Rust/Go toolchains not listed; `bun test` doesn't run the full suite as claimed)

## Action taken

- None — REPORT ONLY per task. Suggested follow-up: fix stale ports/paths, resolve the double-claimed `:25130`, add coyote + kimi-code rows, correct the OpenFang Workspaces-table description, and merge the openfang README fix (`c807f56729`) to main.
