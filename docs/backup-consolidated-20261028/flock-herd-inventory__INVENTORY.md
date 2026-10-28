# Flock/Herd Integration — Read-Only Inventory

**Date:** 2026-09-17 ~13:00 MDT
**Scope:** read-only recon on awrawr-pc. Nothing edited, restarted, pushed, or deleted.
**Purpose:** Step 1 of Chris's architecture decision — completion traffic stays through Herd's
main port; AstMatrix and nim-proxy are eliminated as live/operator-facing identities; ALL their
functionality is genuinely absorbed into the unified component **Flock** (generalized beyond
NVIDIA into the complete remote-API/completions subsystem behind Herd's main port).
No aliases, wrappers, or monkey patches.

**Legs:** 4 parallel inventory agents on awrawr-pc (Herd routing, AstMatrix refs, nim-proxy
refs+capability, Flock state). No secret values were read or reproduced (names/paths only).

---

## (a) Herd main-port routing map

### Port & process
- **Port :25100 VERIFIED.** `HERD_PORT=25100` in `/home/toxic/sovereign/config/ports.env:57`.
  `ss -ltnp` shows `127.0.0.1:25100` bound by PID **3736538** (`llama-swap` binary), loopback-only,
  running since ~04:00 Sep 17.
- **ORPHANED from its supervisor.** Pitchfork daemon `sovereign/herd` is defined in
  `/home/toxic/sovereign/pitchfork.toml:22-29` (`run = "exec /home/toxic/sovereign/stack/services/herd.sh"`,
  `ready_http = "http://127.0.0.1:25100/health"`, `depends = ["shep"]`, `auto = ["start"]`)
  but current `pitchfork list` contains NO herd line; `pitchfork status sovereign/herd` →
  `Error: Daemon sovereign/herd not found`. The supervisor log shows pitchfork spawned herd
  (pid 478012, ready 200) and later explicitly **stopped** it. The live PID's cmdline matches
  `herd.sh`'s launch line exactly — launched outside the supervisor. **Treat herd as unmanaged.**

### Source tree
- Canonical: `/home/toxic/projects/herd` (git origin `toxicwind/herd`, HEAD `ea54484`
  "Consolidate herd/llama-swap/mesh..."). Fork of upstream `mostageek/llama-swap` plus
  `internal/astmatrix/` routing layer. Rename history already done at file level:
  `llama-swap.sh` → `herd.sh`, `llama-swap.yaml` → `herd.yaml`.
- Running binary: `/home/toxic/projects/sovereign-projects/sovereign-swap/build/llama-swap`
  (Sep 12 12:27 build).
- Launcher: `/home/toxic/sovereign/stack/services/herd.sh` → Go binary
  `--config herd.yaml --config-dir /home/toxic/kimi-auto/herd.d --watch-config --listen 127.0.0.1:25100`.
  Port/env validation via `/home/toxic/sovereign/stack/lib-ports.sh`.

### Routes served (from `/home/toxic/projects/herd/internal/server/server.go`)
- Model-dispatched POST JSON (`modelPostJSONRoutes`, server.go:92-121):
  `/v1/chat/completions`, `/v1/responses`, `/v1/completions`, `/v1/messages`,
  `/v1/messages/count_tokens`, `/v1/embeddings`, `/reranking`, `/rerank`, `/v1/rerank`,
  `/v1/reranking`, `/infill`, `/completion`, `/v1/audio/speech`, `/v1/audio/voices`,
  `/v1/images/generations`, `/sdapi/v1/txt2img`, `/sdapi/v1/img2img`, plus `/v/` versionless
  variants (prefix stripped, server.go:305-312).
- POST form (server.go:124-127): `/v1/audio/transcriptions`, `/v1/images/edits`.
- Model-dispatched GET (server.go:131-135): `/v1/audio/voices`, `/sdapi/v1/loras`, `/props`.
- llama-swap/custom endpoints (server.go:344-387): `GET /v1/models`, `GET /models/sse`,
  `GET /logs`, `GET /logs/stream`, `GET /logs/stream/{logMonitorID...}`, `GET /health`,
  `GET /wol-health`, `GET /{$}`, `GET /ui/`, `GET /favicon.ico`, `GET /metrics`,
  `GET /unload`, `GET /running`, `GET /upstream`, `/upstream/{upstreamPath...}`,
  `POST /api/models/unload`, `POST /api/models/unload/{model...}`, `GET /api/profiles`,
  `PUT /api/profiles/active`, `POST /api/inflight/{id}/cancel`, `GET /api/events`,
  `GET /api/metrics/activity`, `GET /api/metrics/stats`, `GET /api/performance`,
  `GET /api/version`, `GET /api/captures/{id}`.
- Live-verified (read-only GET): `/health` → `OK`; `/v1/models` → **102 entries**
  (models + aliases; `includeAliasesInList: true` in herd.yaml).

### Routing chain — model id → backend
Dispatch `localPeerHandler`, `/home/toxic/projects/herd/internal/server/server.go:281-303`,
evaluated in this order:
1. **Local** — `s.local.Handles(modelID)` → spawns/uses local `llama-server` subprocesses
   (one per `models:` entry; `startPort: 25001` in herd.yaml; engines at
   `/home/toxic/projects/sovereign-projects/herd/engines/`, GGUFs at `/home/toxic/models`).
2. **Peer** — `s.peer.Handles(modelID)` → reverse-proxy to `peers:` in
   `/home/toxic/sovereign/config/herd.yaml` (via `PeerDictionaryConfig`,
   `internal/config/config.go:188`):
   - `pollinations-free` → `https://gen.pollinations.ai` (dummy Bearer injected;
     models: openai, gemma-4-31b, gpt-oss, qwen3.8-27b, muse-glimmer, muse-spark-1.2,
     kimi-k3, nemotron-3.5-lightning)
   - `hf-free` → `https://router.huggingface.co` (apiKey `${env.HF_TOKEN}`;
     models: moonshotai/Kimi-K3)
   - `openrouter-kimi` → `https://openrouter.ai/api` (apiKey `${env.OPENROUTER_API_KEY}`;
     moonshotai/kimi-k3, k2.5, k2-0905, k2.6, k2-thinking, k2.7-code, k2 + `:free` variants)
   - `openrouter-ling` → `https://openrouter.ai/api` (`${env.OPENROUTER_API_KEY}`;
     inclusionai/ling-3.0-flash-vl/fin/sante `:free`)
3. **AstMatrix cloud** — `s.cloud.Handles(modelID)` → `astmatrix.Router`, built at
   server.go:188-211 from the `astMatrix:` section (`herd.yaml:31-46`; enabled=true,
   strategy `hybrid`, maxParallel 4, db `/home/toxic/sovereign/data/ast_matrix.db`,
   stickyTtl 1800, fifoMax 64):
   - provider `openrouter`: `https://openrouter.ai/api/v1`, keyEnv `OPENROUTER_API_KEY`
   - provider `nvidia`: **`http://127.0.0.1:8000/v1`** (flock's address), keyEnv
     **`NIM_PROXY_API_KEY`**, modelMap `kimi-k2`→`moonshotai/kimi-k2.6`,
     `kimi-k3-nim`→`moonshotai/kimi-k3`. Bearer handling in
     `internal/astmatrix/router.go:213, 372, 446`.
4. Default: error (no silent fallback).
- Config fragment `/home/toxic/kimi-auto/herd.d/kimi-auto.yaml` (hot-reloaded via
  `--config-dir --watch-config`) defines virtual model `kimi-auto` → shim
  `python3 /home/toxic/kimi-auto/shim.py --port ${PORT}`.

### Env vars / secrets / configs (names only)
- `HERD_PORT` (ports.env, validated by lib-ports.sh); `HOME`; `${env.OPENROUTER_API_KEY}`,
  `${env.HF_TOKEN}` in herd.yaml (`${env.CLOUDFLARE_API_TOKEN}` commented out);
  astMatrix keyEnvs: `OPENROUTER_API_KEY`, `NIM_PROXY_API_KEY`; per-model:
  `LD_LIBRARY_PATH`, `CUDA_VISIBLE_DEVICES`, `GGML_CUDA`, `GGML_CUDA_GRAPHS`,
  `GGML_CUDA_FA_ALL_QUANTS`, `LLAMA_API_KEY` (explicitly empty).
- `herd.sh` sources `/home/toxic/.secrets` ("Canonical secrets for provider keyEnvs
  (NIM_PROXY_API_KEY, OPENROUTER_API_KEY, ...)").
- Secret paths: `/home/toxic/.secrets`, `/home/toxic/.config/pitchfork-secrets`,
  `/home/toxic/.local/share/llama-swap/store.db`, `/home/toxic/sovereign/data/ast_matrix.db`,
  `/home/toxic/sovereign/data/herd-events.log`.
- Config paths: `/home/toxic/sovereign/config/herd.yaml` (936 lines, hand-maintained);
  `config/llama-swap.yaml` is a symlink → `herd.yaml`;
  `/home/toxic/kimi-auto/herd.d/kimi-auto.yaml`; `pitchfork.toml:22-29` daemon def,
  `env_file = "config/ports.env"`; `stack/services/herd.sh`; `stack/lib-ports.sh`.
- Consumer pointer: `pitchfork.toml:260` `KIMI_AUTO_HERD = "http://127.0.0.1:25100"`.
- Bonus: `pitchfork.toml:215-221` `[daemons.flock]`:
  `run = "exec env HOST=127.0.0.1 PORT=8000 DATA_DIR=/home/toxic/.flock-data /home/toxic/.flock/flock"`,
  `ready_cmd = "ss -ltn 'sport = :8000' | grep -q LISTEN"` — currently **stopped** in
  `pitchfork list`. This is the :8000 target of herd's astMatrix `nvidia` provider.

### Identity references in the herd tree
- `herd.yaml:31` `astMatrix:` block (enabled, hybrid); `herd.yaml:40-46` nvidia provider
  (`baseUrl: http://127.0.0.1:8000/v1`, `keyEnv: NIM_PROXY_API_KEY`, modelMap) — the
  **nim-proxy identity survives as env-var name + address** (:8000 is now flock's port).
- `herd.sh` comment names NIM_PROXY_API_KEY.
- `internal/astmatrix/*.go` (circuit.go, coalescer.go, config.go, healthdb.go, matrix.go,
  providers.go, ratelimit.go, router.go) — the AstMatrix routing implementation itself.
  No literal `nim-proxy`/`flock` strings in herd's Go sources — the rename is complete at
  code level; identities persist only in herd.yaml (`NIM_PROXY_API_KEY`, `:8000`) and
  flock's own daemon stanza.

---

## (b) AstMatrix reference list

**~200 live files** box-wide (working tree; `.git` objects excluded). Headline: **flock is NOT
clean on disk** — commit e09a4890 ("drop last astmatrix reference") touched only a research
doc; `/home/toxic/projects/flock/README.md:21-23` **still says** "herd's AstMatrix" and
"**AstMatrix owns the canonical provider definitions**".

### Live/operator-facing
- **Go implementation** — `/home/toxic/projects/herd/internal/astmatrix/`:
  router.go, providers.go, circuit.go, healthdb.go, metrics.go, ratelimit.go, coalescer.go,
  config.go, matrix.go, ui.go, router_live_test.go, ratelimit_test.go (16 files in projects/herd).
- **Gateway hook** — `/home/toxic/projects/herd/mesh/gateway/astmatrix.go`.
- **Install patches** — `/home/toxic/projects/herd/patches/astmatrix-v2/`.
- **Config** — `/home/toxic/sovereign/config/herd.yaml:31-44`
  (`astMatrix: enabled: true, strategy: hybrid, maxParallel: 4,
  dbPath: /home/toxic/sovereign/data/ast_matrix.db, stickyTtl: 1800, fifoMax: 64`
  + 13-provider block); `/home/toxic/sovereign/config/llama-swap.yaml:31-37` (same block).
- **Env** — `/home/toxic/sovereign/.env.local:60`
  `SOVEREIGN_DB=/home/toxic/sovereign/data/ast_matrix.db` (live);
  `AST_MATRIX_PORT` (default 25104, called "Port SSOT"); `SOVEREIGN_PORT`,
  `SOVEREIGN_STRATEGY`; `ASTMATRIX_PORT` in extended-tests portKey.
- **Data** — `/home/toxic/sovereign/data/ast_matrix.db` (persistent health/circuit state).
- **Router source** — `/home/toxic/sovereign/tools/sovereign-router/sovereign-router-ts/sovereign-router-ts/router_config.ts:59`
  UA string `SovereignASTMatrix/3.1`.
- **Tests** — `/home/toxic/sovereign/test/services/extended-tests.ts:121-187`
  (`service: "astmatrix"`, portKey `ASTMATRIX_PORT`, stale path
  `/home/toxic/projects/llama-swap-main/internal/astmatrix/` which doesn't exist);
  health endpoints `/`, `/api/health`, `/mesh/` on **25115**.
- **UI strings** — `/home/toxic/sovereign/rust_algo_web/static/portal.html:213`
  (`{ id: "ast-matrix", port: 25104, path: "/health" }`);
  `/home/toxic/sovereign/projects/mesh/ui/src/routes/+layout.svelte:1`
  (nav `<a href="/ast-matrix">AST Matrix</a>`, "Mesh Control Plane").
- **Docs** — `/home/toxic/sovereign/docs/UNIVERSAL_ARCHITECTURE.md:25,82,181`
  ("use for: llama-swap, astmatrix, sovereign-router"; metric
  `sovereign_astmatrix_latency_seconds`);
  `/home/toxic/sovereign/README.md:83-87` (dual-implementation section);
  `/home/toxic/sovereign/README.md:85` (points to `herd/README_ASTMATRIX_V2.md`);
  `/home/toxic/projects/herd/mesh/README.md:16` ("ast-matrix/ ← AST Matrix code extraction");
  `/home/toxic/sovereign/projects/mesh/README.md:14-16` (`sovereign-ast-router/`,
  `flock-pkg/` "(frozen, was ast-matrix/)").
- **Stale daemon ref** — `/home/toxic/sovereign/mise/tasks/doctor:24` hot-reload list
  includes `ast-matrix` (parses `[daemons.ast-matrix]`, which no longer exists).
- **Ports carrying astmatrix identity** — 25104 (router default; py + TS router; portal
  health check), 25115 (extended-tests astmatrix-api).

### Historical / staging-only (not live — decide archive vs absorb)
- `herd-readme.AX2EfW/` (39 files — scripts, patches, v2 README),
  `staging-20260914/` (9), `sovereign-merge-stash-20260914/` (5), `bench-wt-tau/`
  worktree (23), `masscommit-b1`, `stash-merge-20260914`.

### False positives (NOT the router)
- `gateb-*/dts-*/apk-recon` androidx `Contrast.java`/`AndroidComposeView` noise,
  `projects/Nagram` rlottie vector code, `projects/agent-workspace` scipy.

### Daemon status
- **None live.** No `[daemons.ast-matrix]`/`[daemons.astmatrix]` stanza in any
  pitchfork.toml on the box (`/home/toxic/sovereign/pitchfork.toml` clean;
  pitchfork.service exists, astmatrix not registered).

### Counts (live working-tree files matching)
- projects/herd **16** · sovereign/tools **2** · sovereign root tree **111** (incl. staging
  dirs & worktrees) · sovereign/projects **56** · sovereign/config **2** ·
  sovereign/rust_algo_web **1** · sovereign/test **1** · sovereign/shingle-workspace **14** ·
  sovereign/docs **1** · sovereign/mise **1** · projects/flock **1** (README leftover) ·
  projects/mesh area, portal-audit, emergent-august, grok-build, musubi-no-nawa **1 each** ·
  **~200 files total**, all on the rename target list.

---

## (c) nim-proxy reference list + capability summary

**TL;DR:** nim-proxy has been fully renamed to `flock` in source (commits 19919478 + 6723212a,
2026-09-17; repo `/home/toxic/projects/flock`, origin `toxicwind/flock` thru e09a4890).
There is **no live nim-proxy daemon** — the only listener on the old port is
`/home/toxic/.flock/flock` (the renamed Rust binary). Consumers split three ways: herd + tau
still point at `:8000` (port preserved, old env names kept); sovereign-router-ts bypasses it
with direct NVIDIA + absorbed key-rotation; super-ralph's NimProxy client was never wired live.

### Capability summary — what nim-proxy/flock does natively
Source: `/home/toxic/projects/flock/proxy` — Rust, ~15.7k lines `src/`. Derived from
[miztertea/nim-proxy](https://github.com/miztertea/nim-proxy) v0.6.5 (audit confirms the
deployed binary was v0.6.5, 5.8MB, cut over Docker → native).

- **Proxy core** — OpenAI-compatible forward proxy for NVIDIA NIM. `/v1/{*path}` wildcard
  (`src/routes.rs:46`, `V1_WILDCARD`) forwards `/v1/chat/completions`, `/v1/completions`,
  `/v1/embeddings`, `/v1/models` to `https://integrate.api.nvidia.com`
  (`src/config.rs:231`, `src/proxy.rs:116-119,187,525-561`). `/v1/models` responses cached
  locally so harness catalog polls cost zero rate budget (`src/proxy.rs:972`).
- **Key pool** (`src/pool.rs`) — one "lane" per upstream `nvapi-…` key; exact
  **sliding-window** rate limiter (N rpm per rolling **61s** = 60s + 1s jitter pad,
  load-tested against upstream 429s). Sticky-lane affinity with spillover to least-loaded
  ready lane (`reserve`, ~line 197). Lanes enter cooldown after upstream 429/5xx. Disabled
  keys stay as inactive *state carriers* so re-enable doesn't resurrect a fresh window.
  Live pool per 2026-09-15 audit: **4 keys × 40 rpm = 160 rpm aggregate**.
- **Dispatcher** (`src/dispatch.rs`) — global FIFO slot queue across all clients; 25ms
  `GRANT_GAP` between grants caps burst concurrency without capping throughput.
- **Model-pressure governor** (`src/governor.rs`) — handles NIM's per-model worker cap
  (`"ResourceExhausted: Worker local total request limit reached (32/32)"`), which is
  model-scoped and shared across keys (failover can't help). On exhaustion: cap engages at
  half observed in-flight + 2s drain gap; AIMD recovery +1 concurrency per stable minute;
  dissolves after 30 clean minutes; operator override pins a fixed cap. Metrics
  `flock_model_limit`, `flock_model_inflight`, `flock_worker_exhausted_total`.
- **Client auth** — `/v1/*` keyed by `npk_` client secrets (128-bit OS randomness,
  `src/settings.rs:385-390`). Live `NIM_PROXY_API_KEY` (36ch `npk_…`) in
  `/home/toxic/.secrets` (0600) — audit-verified SHA-256 match against proxy config.
- **Operator surface** — PBKDF2/HMAC session cookies (`flock_session`, 12h TTL,
  `src/auth.rs`), multi-user roles; routes `/health`, `/metrics` (Prometheus, auth-gated),
  `/login`, `/logout`, `/setup`, `/setup/validate-key`, `/dash`, `/api/dashboard`,
  `/api/dashboard/now`, `/api/config`, `/api/locale-bootstrap`,
  `/api/settings/{nim-keys,clients,upstream,limits,server,history,governor,users,account,locale,validate-key}`;
  embedded web UI (`src/web/`).
- **Persistence** — UI-managed `DATA_DIR/config.json` (config store incl. upstream keys,
  client_auth, limits, governor, users); request history in `DATA_DIR/history.jsonl`
  (`src/history.rs`, 3751 lines). Container env vars only `HOST/PORT/DATA_DIR/RUST_LOG`
  (`src/config.rs:1-4`).
- **Ports** — `:8000` only. `ss` shows no other nim-related listener.
- **Dead artifacts still on disk** — `/home/toxic/.nim-proxy/nim-proxy`,
  `/home/toxic/.nim-proxy-data/{config.json,history.jsonl}`,
  `/home/toxic/.docker-offload/nim-test/history.jsonl` (docker era).

### Where the old identity still lives
- `sovereign/config/herd.yaml:42-47` — herd nvidia provider
  (`baseUrl: http://127.0.0.1:8000/v1`, `keyEnv: NIM_PROXY_API_KEY`, modelMap);
  `herd.sh` sources `/home/toxic/.secrets` to inject it.
- `sovereign/mise.toml:145` — `health-nim-proxy` task.
- `sovereign/README.md:66` — port table `:8000 | nim-proxy`.
- `sovereign/migration/staged/sysd-migrate-daemons.toml:44` — stale Docker-based
  `[daemons.nim-proxy]` def (`ghcr.io/miztertea/nim-proxy:latest`); also
  `sovereign/pitchfork.toml.bak-flock-20260917` (pre-rename daemon def backup).
- `super-ralph/README.md:102-128` + `src/nimProxy.ts` — envs `NIM_PROXY_API_KEY`
  (comma-separated rotation), `NIM_PROXY_BASE_URL`, `NIM_PROXY_MODEL`,
  `NIM_PROXY_BYPASS=1`. **Discrepancy: code line 26
  `DEFAULT_PROXY_BASE_URL = "http://127.0.0.1:25104"` — code now defaults to
  sovereign-router, README still says `:8000`.**
- `projects/flock/flock-final.sh:212-217` — installer exports compat aliases
  `NIM_PROXY_URL`, `NIM_PROXY_API_KEY`, `NIM_BASE_URL`, `ANTHROPIC_BASE_URL` → all
  `http://127.0.0.1:8000/v1` (alongside new `FLOCK_URL`).
- `.github/workflows/release.yml:173-179` in projects/flock — still ships
  `nim-proxy-$version` tarballs.
- **Key-rotation absorption:** `NimProxyKeyPool` (super-ralph) → `FlockKeyPool` absorbed
  natively into flock-client: `client/src/keypool.ts` (+149), `client/python/flock_client/keypool.py`
  (+131) — 429/Retry-After rotation, opaque `key#N` stats; client package renamed
  `nim_client → flock_client` (commit 6723212a).

### New flock identity (already adopted)
- tau extension: `FLOCK_BASE_URL` (default `:8000`), `FLOCK_API_KEY` → `NVIDIA_API_KEY`
  → `NIM_PROXY_API_KEY` fallback (`flock.ts:77`).
- flock repo README/COMPARISON.md, `/home/toxic/.flock-data`.

### Consumers (current)
1. **herd** — `herd.yaml:43` nvidia provider → `127.0.0.1:8000/v1`, keyEnv
   `NIM_PROXY_API_KEY`. (Stale copy: `sovereign/mesh-bruteforce-20260914/config/herd.yaml:43`.)
2. **tau/omp flock extension** — `sovereign/projects/tau/extensions/flock/`:
   `src/flock.ts:26` `DEFAULT_BASE_URL = "http://127.0.0.1:8000"`; slash commands
   `/flock-status|models|chat` + LLM tools `flock_status/models/chat`;
   `scripts/smoke.sh:17` hits live `:8000`.
3. **super-ralph** — `super-ralph/src/nimProxy.ts` (27 hits) + `nimProxy.test.ts` (35):
   client-side `NimProxyKeyPool` rotation, intended-but-unwired ("nim-proxy as claude"
   never realized per 09-15 audit).
4. **flock-final.sh installer** — writes herd provider snippet
   `baseUrl: http://127.0.0.1:8000/v1` (line 281), exports all compat env names.
5. **free-claude-code** — `config/settings.py:163` `NVIDIA_NIM_PROXY` env (optional);
   defaults direct to upstream.
6. **claude-nim-shim.ts** — `NIM_BASE_URL` env (line 7), defaults direct.
- Related but separate: `gk-live-gear/nvidia-nim-loader/bin/nim_proxy.py` (57 lines) —
  ephemeral auth-injecting forward proxy for the Bun TS client (ephemeral localhost port →
  upstream; Secure Vault `custom.nvidia`/`access_token` surrogate; raw keys never touch
  env/disk). Not a consumer of :8000.
- mesh-hub (`:25115`): no `:8000`/nim-proxy references in `projects/herd/mesh` — not a consumer.
- **Bypassed/absorbed:** `sovereign-router-ts` — NVIDIA goes direct to
  `https://integrate.api.nvidia.com/v1` with in-process multi-key rotation; comments
  literally say "the :8000 key-proxy is retired — multi-key rotation … absorbed"
  (`router_config.ts:118-121,199`; `router_matrix.ts:49`; COMPARISON.md:73).

### Reference counts
`rg -i "nim[-_]?proxy|nimproxy"` → 4227 lines; `:8000|NIM_PROXY_API_KEY|integrate.api.nvidia.com`
→ 4945 lines (noise: vendored tau `models.json` catalogs, `.omp` session logs, tokenizer JSON).
After excluding session/log/dedupe noise: **3707 reference lines**. Top groups:
- `.nim-proxy-data/history.jsonl` 819 (dead) · `.flock-data/history.jsonl` 819 (live) ·
  `.docker-offload/nim-test/history.jsonl` 495 (dead docker era) ·
  `projects/flock/` 486 (Rust source 16 files ~15.7k lines, docs, knowledge/architecture,
  plans, release.yml, flock-final.sh, client/, dashboard/, tools/, benchmarks/) ·
  `.local/state/pitchfork/logs/pitchfork/pitchfork.log` 248 ·
  `sovereign/tau-audit-20260914/` 247 (events.csv 230 + config_events.csv 17) ·
  `.flock-data/history-v1.jsonl` 100 · `super-ralph/src/` 77 ·
  `sovereign/shingle-workspace/` 57 (cutover_edits.py, `NIM_PROXY_PORT="8000"`) ·
  `sovereign/bench-wt-tau/` 31 · `projects/test-ralph/` 27 (provider catalog entries) ·
  `sovereign/projects/` 26 (tau flock extension) ·
  `nim-proxy-audit-20260915/REPORT.md` 16 (definitive 09-15 state doc) ·
  `sovereign/kimi-audit-scratch-20260914/` 15 · `sovereign/migration/` 13 ·
  `.worktree-preserve-20260914/live-config-backup/` 10 · `nim-proxy-final.sh` 9 (09-14 installer) ·
  `super-ralph/README.md` 9 · `sovereign/pitchfork.toml.bak-flock-20260917` 5 ·
  `gk-live-gear/nvidia-nim-loader/` 6.

Env var names seen: `NIM_PROXY_API_KEY`, `NIM_PROXY_BASE_URL`, `NIM_PROXY_MODEL`,
`NIM_PROXY_BYPASS`, `NIM_PROXY_PORT`, `NIM_PROXY_URL`, `FLOCK_URL`, `FLOCK_API_KEY`,
`FLOCK_BASE_URL`, `FLOCK_PORT`, `NVIDIA_API_KEY`, `NVIDIA_NIM_API_KEY`,
`NVIDIA_NIM_PROXY`, `NIM_BASE_URL`, `NIM_MODEL`, plus proxy-internal
`HOST/PORT/DATA_DIR/RUST_LOG`.
Secrets (paths only): Secure Vault `custom.nvidia`/`access_token` (surrogate, nim_proxy.py);
`/home/toxic/.secrets` (0600, holds live `NIM_PROXY_API_KEY`);
`/home/toxic/.config/pitchfork-secrets` exists (not read).

---

## (d) Flock current capability inventory

### Git
- Repo `/home/toxic/projects/flock`, branch `main`, **clean** (`git status --short` empty).
- Origin `https://github.com/toxicwind/flock.git` (fetch+push), tip **`e09a4890`**
  ("docs: drop last astmatrix reference in research doc").
- Log: `e09a4890` ← `e0316217` (flock-final.sh rewrite: dry-run, no sleep, non-destructive,
  shellcheck-clean) ← `6723212a` (**absorption commit**) ← `22975761` (AGENTS.md rename;
  lockfile after crate rename) ← `19919478` (rename nim-proxy → flock in full).
- Absorbed in 6723212a (via `git show --stat`, excl. 1.8GB benchmark archive removal):
  `FlockKeyPool` TS+Python clients; dead-model guards (`listModels`/`probeModel`);
  zero active astmatrix/nim-proxy **product** naming (`flock_*` metrics prefix,
  `x-flock-deadline-ms` header, `flock_session` cookie, "Flock" web UI + OpenAPI);
  touched `proxy/src/api.rs` (232 chg), `history.rs`, `governor.rs`, `dispatch.rs`,
  `proxy.rs`, `dashboard.js` (168), `openapi.json`, tests. e2e 119 / lib 210 / openapi 8
  passing; `FEATURE_PARITY.md` maps seven stray NIM implementations → Flock.

### Rust core
- Crate `flock` v0.6.6 (`proxy/Cargo.toml`), edition 2021, rust 1.87.
- **Providers: NVIDIA NIM ONLY** (`https://integrate.api.nvidia.com` default `base_url`;
  overridable via `POST /settings/upstream`). **No multi-provider abstraction.**
- **Model discovery:** live passthrough `GET {base_url}/v1/models`
  (`proxy::fetch_models`, proxy.rs:975–1016), cached in `models_cache` with `models_ttl`;
  `/v1/models` special-cased in the wildcard proxy handler.
- **Auth:** keyed Bearer auth for `/v1` (`missing or invalid proxy API key` → 401);
  dashboard login + setup wizard — first dashboard visitor claims the proxy; `/v1` stays
  **closed until setup**. Keys/users managed via settings endpoints.
- **Persistence: JSON files only, no sqlite** — `config.json` (all state, under `$DATA_DIR`)
  + `history.jsonl` / `history-v1.jsonl` (30-day retention; `proxy/src/history/store.rs`).

### Endpoints (from `proxy/src/routes.rs` + `lib.rs` router)
| Method | Path | Behavior |
|---|---|---|
| GET | `/health` | lib.rs:698 → literal `"ok"` |
| GET | `/metrics` | lib.rs:682 → `metrics_text` (auth-gated) |
| GET | `/`, `/dash` | lib.rs:680-681 → `dash` web UI |
| GET/POST | `/login`, `/logout`, `/setup`, `/setup/validate-key` | auth / login / setup handlers |
| GET | `/locale-bootstrap`, `/dashboard`, `/dashboard/now`, `/config` | operator API |
| POST | `/settings/{nim-keys,clients,upstream,limits,server,history,governor,users,account,locale,validate-key}` | settings |
| GET | `/assets/public/*`, `/assets/operator/*` | embedded static assets + locale catalogs |
| ANY | `/v1/{*path}` | `proxy::handle` — full OpenAI-compatible proxy (chat/completions/embeddings/etc. + `/v1/models` intercept) |

### Binary & data
- `/home/toxic/.flock/flock` v0.6.6, 6.22MB, built 2026-09-17 10:24; no `--help`/`--version`
  (bare invocation starts the server; panicked `AddrInUse` on busy port, no state change).
  Prior build kept: `flock.prev-20260917` (6.13MB).
- Startup banner (DATA_DIR-relative): `data/config.json`, upstream integrate.api.nvidia.com,
  lanes 0 enabled keys / 0 rpm, "API auth: keyed (0 client key(s))", patience 900s/request.
- `/home/toxic/.flock-data`: `config.json` (600, Sep 12), `.env` (Sep 13),
  `history.jsonl` (4.9MB, Sep 17 04:52), `history-v1.jsonl` (765KB, written 12:59 — active).

### Daemon — **stale, manual launch**
- `sovereign/flock` IS in `/home/toxic/.local/state/pitchfork/state.toml` but
  **status=`stopped`** (stanza: `exec env HOST=127.0.0.1 PORT=8000 DATA_DIR=/home/toxic/.flock-data
  /home/toxic/.flock/flock`, cwd `/home/toxic/sovereign/.`,
  `ready_cmd = "ss -ltn 'sport = :8000'"`). This is why `pitchfork list` showed nothing —
  it ran with pitchfork not on PATH.
- Actual :8000 holder: **PID 662160 = `/home/toxic/.flock/flock`, started 10:24 today MANUALLY**:
  `sh -c "cd /home/toxic/sovereign && FLOCK_PORT=8000 PORT=8000 DATA_DIR=/home/toxic/.flock-data
  setsid nohup /home/toxic/.flock/flock >>/home/toxic/.flock/flock.log 2>&1 &"`.
  Launch env mirrors the pitchfork stanza, but pitchfork does not supervise it (detached setsid).
- Binary identity verified: `sha256(/proc/662160/exe) == sha256(/home/toxic/.flock/flock)`.
- **A crash leaves :8000 dead until manual restart; reboot brings nothing back.**

### Live probes (GET-only, no completions spent)
- `GET /health` → **200 `"ok"`**
- `GET /v1/models` → **401** `{"error":{"code":"unauthorized","message":"missing or invalid
  proxy API key (Authorization: Bearer …)","type":"proxy_error"}}` — auth gate working
- `GET /metrics` → **401**, 0 bytes — also auth-gated

### Operational state — **/v1 currently closed**
- **Zero client keys configured; "SETUP REQUIRED — /v1 stays closed until setup";
  0 enabled upstream keys.** The live server rejects ALL /v1 traffic with 401.
- Consequence: herd's astMatrix `nvidia` provider → `127.0.0.1:8000/v1` (keyEnv
  `NIM_PROXY_API_KEY`) has no working auth against flock today — **herd's nvidia path is
  effectively dead right now** (needs key alignment or setup completion).

---

## (e) GAP LIST — what AstMatrix/nim-proxy do that Flock does not yet natively do

Ranked by implementation-blocker severity for the absorb directive.

1. **Multi-provider routing (the big one).** AstMatrix routes 13 built-in providers
   (openrouter, nvidia, …) with hybrid strategy, provider records, sticky-TTL affinity,
   FIFO slots, circuit breakers, per-provider rate limits, persistent healthdb. Flock is
   **NVIDIA-only with no provider abstraction** (one `base_url`, overridable at runtime).
   Absorbing AstMatrix per Chris's directive means Flock becomes the multi-provider
   remote-API/completions subsystem — this is a provider-model redesign, not a config change.

2. **Persistent health/circuit state.** `ast_matrix.db` (sqlite, healthdb.go) persists
   provider/model health, strikes, circuit state across restarts. Flock: JSON files only;
   key-pool lane state, cooldowns, governor state are in-memory and lost on restart.

3. **Model-discovery breadth.** AstMatrix + sovereign-router build `/v1/models` from live
   provider records with metadata (provider, source, free, ELO, circuit, strikes — 779 IDs
   on sovereign-router's side; 102 on herd). Flock caches only its single upstream's
   `/v1/models` passthrough.

4. **Operator key alignment.** Herd's nvidia provider sends `NIM_PROXY_API_KEY` from
   `/home/toxic/.secrets` to `:8000`; Flock's `/v1` expects its own client-key store
   (**0 keys configured, setup unclaimed → all /v1 = 401**). The absorb must either seed
   flock's client auth with the operator key or complete setup — otherwise herd's nvidia
   path stays dead.

5. **Restart supervision.** `sovereign/flock` pitchfork daemon is **stopped**; live :8000 is a
   manual nohup. Herd :25100 is likewise orphaned from pitchfork (supervisor stopped its
   instance). Reboot = both dead. Absorb plan must re-establish supervised daemons with
   ready checks.

6. **Rate-limit semantics beyond per-key windows.** Flock key pool = per-key sliding-window
   61s + governor's per-model worker cap. AstMatrix ratelimit.go + coalescer add **request
   coalescing** and (per the remaining-work list) least-latency/round-robin forwarding —
   none of which exist in Flock.

7. **Canonical identity split.** sovereign-router-ts treats `:8000` as retired (direct
   NVIDIA, rotation absorbed in-process); herd treats `:8000` as its live nvidia provider;
   super-ralph code defaults to `:25104` while its README says `:8000`. The absorb must
   pick ONE canonical address/identity and update all consumers.

8. **Route/model parity.** Herd dispatches `/v1/responses`, `/v1/messages`, rerank, audio,
   images, sdapi, infill, `/completion` — Flock's wildcard covers `/v1/*` passthrough but
   only to NVIDIA; herd's modelMap names (`moonshotai/kimi-k2.6`) are NVIDIA-side. Non-NVIDIA
   models cannot flow through Flock today.

9. **Metrics unification.** `flock_*` Prometheus metrics exist but `/metrics` is auth-gated;
   herd exposes `sovereign_astmatrix_*` via `/metrics`. Operator dashboards (portal.html:213
   ast-matrix card) need a single namespace.

10. **Operator UI identity.** Flock has `/dash` + setup wizard; mesh UI has an `/ast-matrix`
    nav entry; portal.html has an ast-matrix health card. Absorb = one operator UI identity.

---

## (f) RENAME/ABSORB CHECKLIST — every identity artifact

### Source / package names
- `/home/toxic/projects/herd/internal/astmatrix/` — 12 Go files
  (router.go, providers.go, circuit.go, healthdb.go, metrics.go, ratelimit.go, coalescer.go,
  config.go, matrix.go, ui.go, router_live_test.go, ratelimit_test.go): absorb or retire on merge.
- `/home/toxic/projects/herd/mesh/gateway/astmatrix.go` — gateway hook.
- `/home/toxic/projects/herd/patches/astmatrix-v2/` — install patches.
- `/home/toxic/projects/flock/.github/workflows/release.yml:173-179` — ships
  `nim-proxy-$version` tarballs; rename artifacts.
- `super-ralph/src/nimProxy.ts` + `nimProxy.test.ts` — client; rename or retire.

### Runtime paths / data
- `/home/toxic/sovereign/data/ast_matrix.db` — migrate/absorb into Flock persistence.
- `/home/toxic/.nim-proxy/nim-proxy`, `/home/toxic/.nim-proxy-data/` — dead artifacts
  (flag per additive policy, do not silently delete).
- `/home/toxic/.docker-offload/nim-test/` — docker-era dead history.
- `/home/toxic/.flock/flock.prev-20260917` — previous build kept alongside live binary.
- `/home/toxic/.flock-data` — live flock data (keep; canonical).

### Ports
- `:25104` astmatrix identity — `portal.html:213` health card, `AST_MATRIX_PORT` default,
  `router_config.ts:59` UA `SovereignASTMatrix/3.1` (that port is now sovereign-router's).
- `:25115` — extended-tests `astmatrix-api` health endpoints (`/`, `/api/health`, `/mesh/`).
- `:8000` — nim-proxy-era port, now flock's; consumers assume it (herd, tau, mise task).

### Env vars
- `NIM_PROXY_API_KEY` — herd.yaml:44, herd.sh, `/home/toxic/.secrets`, super-ralph,
  tau fallback chain, flock-final.sh compat aliases.
- `NIM_PROXY_BASE_URL`, `NIM_PROXY_MODEL`, `NIM_PROXY_BYPASS`, `NIM_PROXY_PORT`,
  `NIM_PROXY_URL`, `NIM_BASE_URL`, `NIM_MODEL`, `NVIDIA_NIM_PROXY`.
- `AST_MATRIX_PORT`, `ASTMATRIX_PORT`, `SOVEREIGN_DB`, `SOVEREIGN_STRATEGY`, `SOVEREIGN_PORT`.
- New family already in use: `FLOCK_URL`, `FLOCK_API_KEY`, `FLOCK_BASE_URL`, `FLOCK_PORT`.

### Keyring / secret names
- Secure Vault `custom.nvidia` / `access_token` (surrogate, `gk-live-gear/nvidia-nim-loader/bin/nim_proxy.py`).
- `/home/toxic/.secrets` entries (`NIM_PROXY_API_KEY`, `OPENROUTER_API_KEY`, …).
- `/home/toxic/.config/pitchfork-secrets` (exists, unread).

### Daemon names
- `sovereign/flock` — defined (`pitchfork.toml:215-221`), **stopped**; re-enable with ready
  check on implementation.
- `[daemons.nim-proxy]` Docker def — `sovereign/migration/staged/sysd-migrate-daemons.toml:44`
  (stale, `ghcr.io/miztertea/nim-proxy:latest`); plus
  `sovereign/pitchfork.toml.bak-flock-20260917` (pre-rename backup — keep as provenance).
- No astmatrix daemon exists; only stale `mise/tasks/doctor:24` `[daemons.ast-matrix]` ref.

### Docs
- `/home/toxic/projects/flock/README.md:21-23` — **still references AstMatrix** (fix; the
  e09a4890 commit missed it).
- `/home/toxic/sovereign/README.md:66` — port table `:8000 | nim-proxy`; `:83-87`
  dual-implementation section; `:85` → `herd/README_ASTMATRIX_V2.md` pointer.
- `/home/toxic/sovereign/docs/UNIVERSAL_ARCHITECTURE.md:25,82,181`.
- `/home/toxic/projects/herd/mesh/README.md:16`; `/home/toxic/sovereign/projects/mesh/README.md:14-16`.
- `nim-proxy-audit-20260915/REPORT.md` — definitive 09-15 state doc (keep as provenance).
- `super-ralph/README.md:102-128`.

### UI strings
- `/home/toxic/sovereign/rust_algo_web/static/portal.html:213` — ast-matrix health card.
- `/home/toxic/sovereign/projects/mesh/ui/src/routes/+layout.svelte:1` — `/ast-matrix` nav.
- `router_config.ts:59` — UA `SovereignASTMatrix/3.1`.
- Already flock: `flock_*` metrics, `x-flock-deadline-ms` header, `flock_session` cookie,
  "Flock" web UI + OpenAPI (keep).

### Tools / tasks
- `sovereign/mise.toml:145` — `health-nim-proxy` task.
- `sovereign/mise/tasks/doctor:24` — stale `ast-matrix` hot-reload ref.
- `projects/flock/flock-final.sh:212-217,281` — compat aliases + herd provider snippet writer.
- `sovereign/shingle-workspace/cutover_edits.py` — docker→native cutover tasks.
- `nim-proxy-final.sh` — dead 09-14 installer (flag, don't silently delete).

### Configs
- `/home/toxic/sovereign/config/herd.yaml:31-46` — `astMatrix:` block + nvidia provider
  (`keyEnv: NIM_PROXY_API_KEY`, modelMap); `config/llama-swap.yaml` is a symlink (fine).
- `/home/toxic/sovereign/.env.local:60` — `SOVEREIGN_DB=…/ast_matrix.db`.
- `config/ports.env` — `AST_MATRIX_PORT` SSOT entry.
- `/home/toxic/sovereign/test/services/extended-tests.ts:121-187` — astmatrix service def.
- `/home/toxic/sovereign/mesh-bruteforce-20260914/config/herd.yaml:43` — stale copy of
  herd.yaml with the old nvidia provider block.

### Staging / historical (decide: archive vs absorb — additive default, flag for Chris)
- `herd-readme.AX2EfW/` (39 files), `staging-20260914/` (9),
  `sovereign-merge-stash-20260914/` (5), `bench-wt-tau/` worktree (23),
  `masscommit-b1`, `stash-merge-20260914`.

---

## Appendix — port/daemon reality check (2026-09-17 ~13:00 MDT)

| Port | Listener | Supervision | Status |
|---|---|---|---|
| :25100 | PID 3736538 `llama-swap` (herd) | pitchfork `sovereign/herd` defined but **not found/stopped** — process orphaned | serving, `/health` OK, `/v1/models` 102 entries |
| :8000 | PID 662160 `/home/toxic/.flock/flock` | pitchfork `sovereign/flock` defined but **stopped** — process is manual nohup | `/health` 200 `"ok"`; **all /v1 → 401** (no client keys, setup unclaimed) |
| :25104 | sovereign-router-ts (bun) | live | NVIDIA direct (bypasses :8000) |
| :25115 | mesh-hub | live | no :8000/nim-proxy refs |

**Bottom line for implementation:** the rename at source level is done (flock tree is
nim-proxy-absorbed and astmatrix-free in product naming), but the absorb is NOT done at
runtime level — flock is NVIDIA-only, unauthenticated for its consumers, unsupervised,
and herd's AstMatrix layer still carries the multi-provider routing that Flock must
natively replace. Both :25100 and :8000 run outside pitchfork; a reboot kills both.
