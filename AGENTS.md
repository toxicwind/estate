# AGENTS.md — Sovereign stack (`/home/toxic/sovereign`)

Inherits **`~/.grok/AGENTS.md`**. Local deltas only.

## Stack

| Piece | Path / port |
|-------|-------------|
| Orchestration | **mise + process-compose** (not pixi/devenv) |
| LLM front door | **llama-swap :25100** (Go binary — do **not** rewrite) |
| LLM **chat UI** | **llama-swap** `http://127.0.0.1:25100/ui/` — not the :25101 dashboard |
| Hot path web/watchdog | **Rust** `sovereign_web` (:25101 / :25104) |
| Glue / MCP / IDE deploy | **Bun** under `src/{mcp,deploy,services}` |
| Weird / legacy | **`backup/` only** — never delete; move junk here, never stage |

### Language policy (no thrash)

- **Keep llama-swap as-is** (upstream Go). Replacing it is pure thrash.
- **Rust** owns long-lived hot services (already `sovereign_web`).
- **Bun** owns MCP, settings JSON, IDE wiring, one-shot deploy tools — not the inference path.
- Do **not** rewrite Bun→Rust or shell→Rust wholesale unless a service is proven hot-path + broken.

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

