# README audit — toxicwind/sovereign @ 629c8ac9 — 2026-09-14

**Verdict:** NEEDS UPDATE

Audited main @ `629c8ac97081f5d6ff78d327b03db272a99e6188` (README blob `009984f9`, 342 lines).
Ground truth: recursive git-tree (673 entries, not truncated) + `config/ports.env` as port SSOT
+ last 20 commits. Tarball endpoint 404'd for this repo, so the tree API was used instead;
mechanical checks ran against a path-skeleton built from the tree (existence-only).

Mechanical (`bin/audit.py`): readme-exists PASS · mentioned-paths-exist **FAIL**
(7 missing: `stack/services/llama-swap.ts`, `tools/llama-swap/README.md`,
`tools/llama-swap/config.yaml`, 4× `crates/language_models/src/provider/*.rs`) ·
relative-links PASS · external-links PASS · versions WARN (false positives on IPs) ·
quickstart-entrypoints WARN (one false positive).

## Claims

| Claim (README section) | Evidence | Verdict |
|---|---|---|
| Orchestration: mise + pitchfork (header) | `mise.toml`, `pitchfork.toml` in tree | VERIFIED |
| Ports SSOT: `config/ports.env` (header) | file present; all checked ports below vs it | VERIFIED |
| No Caddy, no landing; ops UI is rust-web only | zero `*caddy*`/`*landing*` paths in tree; `rust_algo_web/Cargo.toml` present | VERIFIED |
| Quickstart: `mise run up/health/status/down` | `mise/tasks/{up,health,status,down}` present | VERIFIED |
| Quickstart URL table: :25101, /ops/api/status | `RUST_WEB_PORT=25101` in SSOT; endpoints not in tree | UNVERIFIED |
| :25103 OpenFang UI, :25203 OpenFang API | `OPENFANG_PORT=25103`, `OPENFANG_API_PORT=25203` in SSOT | VERIFIED (ports) |
| :25106 HF downloader, :25110 Grafana, :25115 mesh-hub, :25120 MCP gateway /health | all match SSOT | VERIFIED (ports) |
| :25121 byte-vision, :25133 Qdrant, :25199 Redis | `BYTE_VISION_PORT=25121`, `QDRANT_PORT=25133`, `REDIS_PORT=25199` | VERIFIED (ports) |
| rust-web :25101 is Rust ops dashboard + watchdog | `rust_algo_web/` + Cargo.toml in tree | VERIFIED |
| openfang :25103 "Agent kernel — OpenFang OS, 206 models, 61 skills, Discord bridge" | port ✓ SSOT; model/skill counts nowhere in tree | UNVERIFIED (counts) |
| sovereign-router :25104, "5-strategy … (fifo_matrix, ast_race, sticky_affinity, weighted_elo, circuit_chain)" | **no 25104 in SSOT**; `tools/sovereign-router/sovereign-router-ts/router.ts` contains all 6 names incl. `hybrid` (46KB, 8–10 hits each) — README says 5 in one place, 6 in another | STALE (port) + internally inconsistent (count) |
| mcpproxy :25109 "MCP federation (43 MCPs → 1 endpoint)" | no 25109 in SSOT; SSOT has `MCPPROXY_GO_PORT=25127` | STALE (port moved to :25127) |
| byte-vision-proxy :25120 "Sovereign MCP Gateway" | port ✓ SSOT; but `tools/sovereign-router/sovereign-mcp-gateway/` **absent from tree** (whole gateway section's code path) | STALE (code gone) |
| itvx-telemetry :25198 (Docker) | no 25198 in SSOT | UNVERIFIED |
| itvx-browserless :25130 (Docker) | SSOT: `ZEDRA_HOST_PORT=25130`; Workspaces table claims QED :25130 for same port | STALE (port reassigned; double-claimed in README) |
| Backends `LLAMA_START_PORT`–`LLAMA_END_PORT` = 25001–25099 | SSOT has `BEELLAMA_PORT=25122`, `IK_LLAMA_PORT=25123`, `TURBO_PORT=25124`; no 25001–25099 vars | STALE |
| "Binary launcher: `stack/services/llama-swap.ts`" | file absent; `stack/services/llama-swap.sh` exists | WRONG (path is `.sh`, not `.ts`) |
| "MCP stdio wrapper: `src/mcp/llama_swap.ts`" | present in tree | VERIFIED |
| AST Matrix Go port at `~/projects/llama-swap-main/internal/astmatrix/` | external $HOME path, not in repo | UNVERIFIED |
| "6 strategies … 7 providers … 40+ model aliases" | 6 strategy names VERIFIED in `router.ts`; provider/alias counts not checked | PARTIAL (counts UNVERIFIED) |
| Sovereign Monitor: recursive-fallback / watchdog / repo-radar + coverage % | all three `.ts` + `.test.ts` present under `tools/sovereign-monitor/`; coverage numbers not derivable from tree | VERIFIED (existence) / UNVERIFIED (coverage %) |
| Quickshell screenshot integration (`~/.config/quickshell/…`) | external machine paths, not in repo | UNVERIFIED |
| "All public-facing services bind 0.0.0.0" | not derivable from tree listing | UNVERIFIED |
| Hot reload: rust-web via `stack/services/rust-web-hot.sh`; llama-swap via `mise run restart-llama` | both files/tasks present | VERIFIED |
| Config table: `tools/llama-swap/config.yaml` "Model matrix, macros, backends" | **`tools/llama-swap/` entirely absent from tree**; commit `1a7488f4` renamed config.yaml→config.yml, README still says `.yaml` | STALE (dir gone; name wrong) |
| Related forks: `tools/llama-swap/README.md` "Sovereign wiring only" | dir absent from tree | STALE |
| Project layout: `bin/llama-swap → fork binary (symlink)` | `bin/` has `hotfix`, `llama-gguf-hash{,-run}`, `nvidia-fan-curve.py` — no llama-swap | WRONG |
| Project layout: `backup/` "legacy — do not stage" | absent from tree | STALE |
| Zed "Custom Zed providers (in-tree)": `crates/language_models/src/provider/{nvidia,openai_mcpproxy,openai_mcpproxy_nvidia,opencode}.rs` | **no `crates/` dir in repo** (those live in the external `/home/toxic/projects/zed` fork) | WRONG |
| Workspaces table: OpenFang = "C++ inference engine fork" :25103 | contradicts README's own services table ("Rust (binary) Agent kernel — OpenFang OS"); OpenFang is RightNow-AI's Rust Agent OS | WRONG |
| Workspaces table: Mesh :25127, Tau :25192, Yote :25102, Herd :25100 | consistent with SSOT (`MCPPROXY_GO_PORT=25127`, `PI_WEB_DASHBOARD_PORT=25192`, `YOTE_PORT=25102`, `HERD_PORT=25100`) | VERIFIED (ports) |
| Build & Test: `bun test` / `test:cov` / `test:gateway:cov` / `test:best-models` | all four scripts in `package.json`; 19 `*.test.*` files in tree | VERIFIED (scripts exist) / UNVERIFIED ("131+ tests", "≥88%", "100%") |
| "Stack glue: MIT where marked" | license markers not audited | UNVERIFIED |

## Missing from README

Real changes in the last 20 commits with no README coverage:

- `4f5450a6` feat: maximal modular audit framework (+ `4cebdba0` AGENTS.md audit docs) — no mention
- `aaee2ff0`/`53c2e829` feat: `local-audit.ts` (`src/maximal-sovereign-agentic-audit/src/`) — no mention
- `7ff347f7` feat: maximal-sovereign-agentic-audit multi-repo; `eade5a5a` repo-audit skill (pyarrow parquet); `75b84a3e` repo_audit.py env-map loader — no mention
- `629c8ac9` (HEAD) hygiene: `projects.env` → `projects.map` rename (now at `skills/repo-audit/projects.map`) — not referenced
- `2193e396` race-borrow skill (concurrent provider racing) — not referenced
- `8ba69c31` "Update sovereign to reflect herd consolidation" — partially reflected (Workspaces table), but the :25100 double-claim (llama-swap row vs Herd row, `HERD_PORT=25100` == `LLAMA_SWAP_PORT`) is unexplained

## Quickstart check

- [x] Commands exist (`mise/tasks/{up,health,status,down,doctor}` all present)
- [ ] Ports/config keys match code — **no**: :25104, :25109, 25001–25099 range, :25130 double-claim, :25198 all diverge from `config/ports.env`
- [ ] A fresh user could follow it end to end — quickstart table sends users to :25109 (mcpproxy, moved to :25127) and :25104 (absent from SSOT)

## Action taken

- None — REPORT ONLY per task rules. No edits, commits, or pushes made.
- Suggested fix order if authorized: (1) re-sync every port against `config/ports.env` (scriptable); (2) delete or rewrite the `tools/llama-swap/` references (dir is gone); (3) fix Zed "in-tree providers" paths (external zed fork); (4) fix OpenFang workspaces-table row (Rust Agent OS, not C++ inference engine); (5) correct `stack/services/llama-swap.ts` → `.sh`; (6) add the audit-framework/local-audit/repo-audit features from recent commits.
