# Sovereign

Local multi-fork LLM stack on **25xxx ports**. Orchestration: **mise + process-compose**. Inference router: **llama-swap** only. **No vLLM.**

Root: `/home/toxic/sovereign`

---

## Port map (SSOT: `mise.toml` `[env]`)

| Port | Service | Notes |
|------|---------|--------|
| **25000** | Caddy edge (optional) | `/llm` → swap, `/hf` → downloader |
| **25001–25099** | llama-server backends | Spawned by llama-swap |
| **25100** | **llama-swap** | OpenAI `/v1/*` + **chat UI** `/ui/` |
| **25101** | rust-web (YOTE) | Ops dashboard + **Fleet Lab** `/fleet.html` (no embedded chat) |
| **25102** | yote | Bun / Telegram status (optional) |
| **25103** | openfang | Agent kernel |
| **25104** | watchdog | Embedded in rust-web |
| **25105** | prometheus | Metrics |
| **25106** | **hfdownloader** (bodaay) | Quant rank + download Web UI |

| Surface | URL |
|---------|-----|
| **Chat** | http://127.0.0.1:25100/ui/ |
| Dashboard | http://127.0.0.1:25101/ |
| Fleet Lab | http://127.0.0.1:25101/fleet.html |
| HFD | http://127.0.0.1:25106/ |
| API | `LLM_BASE_URL=http://127.0.0.1:25100/v1` |

IDE wire: `mise run ide-clients` / `code-insiders-deploy` → oaicopilot → `:25100`.

---

## Quick start

```bash
cd /home/toxic/sovereign
mise install          # process-compose, python, bun
mise run build-compose
mise run up           # or: up-core | up-full
mise run health
mise run status
```

Stop:

```bash
mise run down
```

---

## mise tasks

| Task | Purpose |
|------|---------|
| `build-compose` | Merge `stack/modules/*.yaml` → `process-compose.yaml` |
| `up-core` | llama-swap + openfang + prometheus + rust-web |
| `up` | core + yote + **hf-downloader** |
| `up-full` | all modules including **caddy** |
| `down` | stop process-compose |
| `health` | probe all health endpoints (correct paths) |
| `status` | process list |
| `models` | list llama-swap models on :25100 |
| `hf-ui` | ensure bodaay Web UI on :25106 |
| `hf-analyze` | `mise run hf-analyze -- org/repo` or `-- -i org/repo` |
| `restart-llama` | reload llama-swap only |
| `restart-rust-web` | cargo release + restart dashboard |
| `code-insiders-deploy` | sync Insiders chat models → :25100 |

---

## Model rankings = HuggingFaceModelDownloader (not DEVSTACK UI)

The old dashboard “DEVSTACK RANKINGS / criteria weights” idea is **gone**.

**Replacement:** [bodaay/HuggingFaceModelDownloader](https://github.com/bodaay/HuggingFaceModelDownloader) v3.2+

| Surface | URL / command |
|---------|----------------|
| Web UI | http://127.0.0.1:25106/ |
| Health | http://127.0.0.1:25106/api/health |
| Quant ranking CLI | `hfdownloader analyze -i TheBloke/Mistral-7B-Instruct-v0.2-GGUF` |
| Download | `hfdownloader download org/repo -F q4_k_m` |
| Wrapper | `src/hf_downloader.ts` (installs binary, serves, `--local-dir models`) |

Binary: `~/.local/bin/hfdownloader` (official installer `https://g.bodaay.io/hfd`).

---

## Stack layout

```text
sovereign/
  mise.toml              # tools + env ports + tasks
  mise/tasks/            # thin task scripts
  process-compose.yaml   # GENERATED — do not hand-edit
  stack/
    base.yaml
    modules/*.yaml       # one process each
    services/            # llama-swap.sh, rust-web.sh, …
    build-compose.sh
    up.sh down.sh health.sh
  src/
    hf_downloader.ts     # bodaay serve
    openfang.ts
  rust_algo_web/         # Axum dashboard :25101
  tools/llama-swap/      # config.yaml (forks/models)
  Caddyfile              # optional edge :25000
  models -> ~/models
  yote/                  # Telegram / status agent
  backup/                # moved junk (see cleanup_*)
  architecture.html      # fork intelligence static page
```

### process-compose modules

`caddy`, `llama-swap`, `openfang`, `prometheus`, `yote`, `rust-web`, `hf-downloader`

Watchdog is **not** a separate module — runs inside rust-web on `WATCHDOG_PORT`.

---

## Inference notes

- Router: **llama-swap** only. Prefer `beellama/qwen-flash-64k` (9B, VRAM-safe).
- Large 27B + huge ctx can OOM → empty `choices` in VS Code (“Response contained no choices”).
- Utility model should be `customendpoint/beellama/qwen-flash-64k` on `:25100`.

```bash
curl -s http://127.0.0.1:25100/v1/models | head
curl -s http://127.0.0.1:25100/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"beellama/qwen-flash-64k","messages":[{"role":"user","content":"hi"}],"max_tokens":8}'
```

---

## Dashboard (rust-web)

- URL: http://127.0.0.1:25101/
- **Fleet Lab:** http://127.0.0.1:25101/fleet.html — llama-swap + HFD + 4-fork bench status
- APIs: `/landing/api/status`, `/models`, `/telemetry`, `/architecture`, `/integrations`, `/fleet/last`
- **No chat proxy** — use llama-swap `/ui/`
- Architecture: `/architecture.html`
- Quant UI: **:25106** (HFD), not reinvented on the dashboard

```bash
mise run restart-rust-web
```

---

## Four llama-server forks + fleet

Bins and **`LD_LIBRARY_PATH`** are SSOT in `tools/llama-swap/config.yaml` macros:

| Macro | Role |
|-------|------|
| `beellama_bin` / `beellama_ld` | beellama.cpp |
| `turbo_bin` / `turbo_ld` | llama-cpp-turboquant |
| `ik_bin` / `ik_ld` | ik_llama.cpp-main |
| `ik_tq_bin` / `ik_tq_ld` | ik_turboquant |

```bash
bun run tools/fleet/extract_forks.ts   # → tools/fleet/forks.json
bash tools/fleet/bench-forks.sh        # short llama-bench, small GGUF only
# graduated ctx ranker (default probes 4k…64k — not 27B@max first)
MODEL_URL=http://127.0.0.1:25100 bun run tools/fleet/fleet_ranker.ts
```

**Context policy:** start small and step up. 27B at huge ctx OOMs the 3090 and yields empty `choices` in IDEs.

Sources promoted from Downloads/sovereignbak: `tools/fleet/fleet_ranker.ts`, `fleet_universal_maximal_corrected.ts`.

---

## Grok local models

Grok TUI config (`~/.grok/config.toml`) lists:

- Cloud: `grok-4.5` (default), `grok-composer-2.5-fast` (fork secondary)
- Local: all llama-swap IDs + alias `sov-25100` → `beellama/qwen-flash-64k` @ `:25100`

Agent type: `sovereign-25100` (local-only specialist).

---

## Cleanup / backup

Weird / duplicate / empty trees were moved (not deleted) to:

```text
backup/cleanup_2026-07-11/
```

Includes: old `dashboard/`, `llama-swap-maximal-v5.1`, `hw_dump_*`, empty `data/docs/logs`, `hf-downloader.py` stub, `ports.env.bak`, etc. See `MANIFEST.txt` inside.

---

## Hard rules

1. **Never vLLM** / `vllm-venv` / `sovereign-vllm`.
2. **Canonical tree:** `/home/toxic/sovereign` only for stack.
3. **Ports:** only via `mise.toml` `[env]` — no silent 28080 leftovers.
4. **HF rankings:** bodaay UI/CLI — not reinvented in YOTE.

---

## Related

- Architecture diagram: `architecture.html`, `architecture.d2`
- Token waste analysis (Antigravity): `/home/toxic/projects/antigravity-conversations-analysis/`
- AGENTS global: `~/.grok/AGENTS.md`
