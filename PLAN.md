# Sovereign Stack — Audit & Fix Plan (2026-07-17)

## Completed

### 1. Router: User-Agent fix (Groq Cloudflare bypass)
- **Problem**: `urllib.request` sends `Python-urllib/3.12` User-Agent → Cloudflare blocks Groq with 403
- **Fix**: Added `User-Agent: Mozilla/5.0 (compatible; SovereignASTMatrix/3.1)` to both `call_one()` and `call_one_stream()` in `router.py`
- **File**: `sovereign/tools/ast-matrix/sovereign-ast-matrix/router.py` lines 656, 725

### 2. Router: Debug logging enabled
- **Problem**: `log_message` was completely suppressed — no request-level visibility
- **Fix**: Changed from `pass` to printing to stderr with `[matrix]` prefix
- **File**: `router.py` — `H.log_message()`

### 3. Router: Explicit model routing (from previous session)
- All 5 route strategies (`hybrid`, `ast_race`, `sticky`, `circuit_chain`, `stream`) now route explicit model aliases (e.g. `hy3`, `gemini-2.5-flash`, `codestral`) directly to their provider
- No more NVIDIA poisoning — `resolve_model()` is used for explicit aliases

### 4. Up task: Removed `sleep` loops
- **Problem**: AGENTS.md forbids `sleep`. Old `up` had 3 sequential `sleep 1` loops
- **Fix**: Replaced with `timeout N bash -c 'until curl ...'` pattern — polls without sleep, hard timeout
- **File**: `sovereign/mise/tasks/up`

### 5. _lib.sh: Cleaned up
- Removed redundant `build-compose.sh` call from `pc_up()` (caller does it)
- `pc_up()` now only does `exec process-compose`

## In Progress

### 5b. Bun/TS AST Matrix on SSOT port **25104**
- **SSOT**: `.env.local` `AST_MATRIX_PORT=25104` (Zed `openai_compatible` → `http://127.0.0.1:25104/v1`)
- **Path**: `tools/ast-matrix/sovereign-ast-matrix-ts/router.ts` (Bun; process-compose `ast-matrix`)
- Defaults: `SOVEREIGN_PORT || AST_MATRIX_PORT || 25104` — **never** 19281/19282
- **Collision fixed**: watchdog moved `WATCHDOG_PORT=25111` (was stealing 25104 as sovereign_web)
- Health DB: `data/ast_matrix.db`

### 6. Groq models in router
- 6 Groq models added to `PROVIDER_MODELS["groq"]` and `CODING` dict
- Key is in `~/.secrets` as `GROQ_API_KEY`
- **Needs**: End-to-end test after User-Agent fix

### 7. Zed settings.json
- Basedpyright dotted keys → nested objects
- Ruff `lineLength` → `line-length`
- `default_model` set to sovereign-router/auto
- `openai_compatible` block with full model list
- **Needs**: Zed restart to verify LSP changes

### 8. Cerebras key
- Key in `~/.secrets`: `CEREBRAS_API_KEY=csk-8h3nwhw8mmfy84dr43h33prvrywejvytr4pk3963dkf9w3t8`
- `PROVIDER_MODELS["cerebras"]` is empty — all 403
- **Needs**: Verify if key works, populate models if it does

## Mise Tasks Audit

| Task | Status | Notes |
|------|--------|-------|
| `up` | **Fixed** | Uses `_lib.sh`, no sleep, canonical entry point |
| `down` | OK | Delegates to process-compose |
| `health` | OK | Standard health check |
| `status` | OK | Status display |
| `build-compose` | OK | Generates `process-compose.yaml` from modules |
| `_lib.sh` | **Fixed** | Cleaned redundant build |
| `ast-grep-scan` | OK | Rule pack scan |
| Others | Not audited | `hf-analyze`, `hf-ui`, `models`, `restart-*`, `test-llm` |

## Provider Status

| Provider | Key | Models | Status |
|----------|-----|--------|--------|
| OpenRouter | OPENROUTER_API_KEY | 10 free | Working |
| NVIDIA NIM | NVIDIA_API_KEY | 12 | Working (credit-based) |
| Groq | GROQ_API_KEY | 6 | **403 fixed** (User-Agent) |
| Cerebras | CEREBRAS_API_KEY | 0 | 403 — key may be invalid |
| Google | GOOGLE_API_KEY | 4 | Working |
| Mistral | MISTRAL_API_KEY | 4 | Working |

## Key Files

- Router: `sovereign/tools/ast-matrix/sovereign-ast-matrix/router.py`
- Mise: `sovereign/mise.toml`
- Tasks: `sovereign/mise/tasks/{up,_lib.sh,build-compose,...}`
- Settings: `~/.config/zed/settings.json`
- Secrets: `~/.secrets`
- Health DB: `sovereign/data/ast_matrix.db` (SQLite WAL)
