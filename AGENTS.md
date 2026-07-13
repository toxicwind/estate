# AGENTS.md — Sovereign stack (`/home/toxic/sovereign`)

Inherits **`~/.grok/AGENTS.md`**. Local deltas only.

## Stack

| Piece | Path / port | Runtime |
|-------|-------------|---------|
| Orchestration | **mise + process-compose** | Shell |
| LLM front door | **llama-swap :25100** | Go (upstream — do NOT rewrite) |
| LLM **chat UI** | **llama-swap** `http://127.0.0.1:25100/ui/` | Go |
| Web dashboard + watchdog | **rust-web** (:25101 / :25104) | **Rust** |
| All app code | `src/{mcp,deploy,services}` | **Bun (primary)** |
| Edge proxy | **null-g-proxy** (:8787) | Bun |
| Agent kernel | **openfang** (:25103) | Bun |
| Telegram bot | **yote** (:25102) | Bun |
| HF downloader | **hf-downloader** (:25106) | Bun |
| Legacy | **`backup/` only** | — |

### Language hierarchy (enforced)

1. **Bun** — PRIMARY application language. All new services, MCP, deploy, glue, IDE wiring, e2e tests go here.
2. **Rust** — Hot-path long-lived services only (already `sovereign_web`). No new Rust without proven hot-path need.
3. **Go** — llama-swap is an untouchable upstream binary. Never patch, never fork for config changes.
4. **Shell** — Demoted to thin wrappers only: mise task scripts, service entry shims (`stack/services/*.sh`).
   - NO shell scripts for core logic.
   - NO sh in `bin/` except build artifacts.
   - All operational commands go through `mise run`.

## Mandatory tools (emergence)

1. **GHAS** — pattern/code/repo intel before inventing deploy, health, IDE, or provider wiring.
2. **ast-grep** — structural code/config search and edit (upgrade CLI if `toml` unsupported; Tombi for TOML format/lint).

## OpenFang

- Prefer `provider = "llama"` → `[provider_urls] llama = "http://127.0.0.1:25100/v1"`.
- Residual `vllm` **id** must map to the same URL — never start vLLM.

## IDE clients

`bun run src/deploy/ide_clients.ts` (or `mise run ide-clients`) wires Insiders oaicopilot, Grok, Antigravity env, `projects/ide-test/*` to `:25100`.

## Trajectory & Token Optimization

To prevent loop states, CLI timeouts, and extreme token waste (e.g. 1.7M token database traces):

1. **Strict Search Ignores**: When using grep/find/ast-grep tools, ALWAYS ignore virtual envs and node packages:
   - Exclude: `venv/`, `.venv/`, `node_modules/`, `dist/`, `.next/`, `build/`, `.git/`, `.cache/`
   - Example: `rg --glob '!node_modules' --glob '!venv' --glob '!.venv' ...`
2. **MCP Tool Verification**: Always check schemas before executing MCP/Lazy tools to prevent validation errors:
   - `find_code` requires `project_folder`.
   - `convert_to_markdown` requires `uri`.
   - Do not pass incomplete arguments.
3. **Clamped Ranges**: Limit file viewing range to 300-500 lines at a time. Truncate command outputs exceeding 50 lines.

