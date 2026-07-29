# Sovereign Stack — Audit & Fix Plan (2026-07-19)

## Session Update (2026-07-19)

### ✅ Completed: AGENTS.md update — Section 8: Tool Call Variants — desktop-commander

Added rule: **ALWAYS use `call_tool_destructive`** for ANY desktop-commander tool call. This applies to: `start_process`, `read_process_output`, `interact_with_process`, `execute_command`, `create_directory`, `move_file`, `read_multiple_files`, `get_file_info`, `set_config_value`, `list_sessions`, `list_processes`, `get_config`, `get_recent_tool_calls`, `list_searches`, `get_more_search_results`, `stop_search`.

### ✅ Completed: settings.json tools block

All 3 agent profiles (`main`, `sovereign-local-a`, `sovereign-local-b`) now have identical `tools` blocks with 11 native tools disabled:

- `copy_path`, `create_directory`, `delete_path`, `edit_file`, `write_file`, `find_path`, `list_directory`, `move_path`, `read_file`, `grep`, `terminal`

### ✅ Completed: llama-swap fork build

- Built new binary at `/home/toxic/projects/llama-swap-main/llama-swap` (21MB)
- Running via existing mise/process-compose at port 25200 (proxied to 25100)
- Config at `/home/toxic/sovereign/tools/llama-swap/config.yaml` with 30+ models

### ✅ Completed: AGENTS.md section renumbering

Sections 8-11 now correctly ordered after inserting new section 8.

## Current MCP Inventory (26 servers)

| MCP                      | Status | Notes                                          |
| ------------------------ | ------ | ---------------------------------------------- |
| mcpproxy-sovereign       | ✅     | Single entry at :25109/mcp                     |
| mcp-server-context7      | ✅     | Docs lookup via npx                            |
| ast-grep-nnunley         | ✅     | Binary: ~/.cargo/bin/ast-grep-mcp              |
| ast-grep-xray            | ✅     | Binary: ~/.local/bin/xray-mcp                  |
| ast-grep-official        | ✅     | uvx from git                                   |
| tree-sitter              | ✅     | uvx mcp-server-tree-sitter                     |
| codebase-memory          | ✅     | Binary: ~/.local/bin/codebase-memory-mcp       |
| project-rag              | ❌     | Missing: cargo install needed                  |
| memory-keeper            | ✅     | npx mcp-memory-keeper                          |
| reactive-memory          | ❌     | Missing: dotnet project                        |
| sqlite-mcp               | ✅     | uvx mcp-server-sqlite                          |
| qdrant-mcp               | ✅     | uvx qdrant-mcp-server                          |
| redis-mcp                | ✅     | uvx redis-mcp-server                           |
| ghas                     | ✅     | Binary: ~/.local/bin/ghas-mcp-stdio.sh         |
| markitdown               | ✅     | uvx markitdown-mcp@0.0.1a4                     |
| prometheus               | ✅     | uvx prometheus-mcp-server                      |
| sovereign-chrome-mcp     | ✅     | bunx @playwright/mcp                           |
| sovereign-firefox-mcp    | ✅     | bunx @playwright/mcp                           |
| llama-swap-test          | ✅     | Bun/TS MCP                                     |
| computer-use-linux       | ✅     | Binary: ~/.local/bin/computer-use-linux        |
| wcgw                     | ✅     | uvx wcgw_mcp                                   |
| desktop-commander        | ✅     | npx @wonderwhy-er/desktop-commander            |
| pty-mcp                  | ✅     | npx @iflow-mcp/so2liu-pty-mcp-server           |
| arxiv-mcp-advanced       | ✅     | uvx Ray0907/arXiv-mcp                          |
| arxiv-mcp-localstore     | ✅     | uvx arxiv-mcp-server[pdf]                      |
| alphaxiv-research-engine | ✅     | npx mcp-remote https://api.alphaxiv.org/mcp/v1 |

## Tool Status (post-compact)

| Tool                          | Status | Notes                                    |
| ----------------------------- | ------ | ---------------------------------------- |
| convert_to_markdown           | ✅     | file: URI works                          |
| find_code / find_code_by_rule | ✅     | Code search                              |
| explore_repo                  | ✅     | Directory structure                      |
| edit_file / write_file        | ❌     | Disabled — use desktop-commander         |
| ghas_*                        | ✅     | All 25 GitHub tools                      |
| activate_window               | ❌     | JSON parse error (framework bug)         |
| click / get_app_state         | ❌     | JSON parse error                         |
| terminal                      | ❌     | Disabled — use pty-mcp/desktop-commander |
| grep                          | ❌     | Disabled — use ast-grep/ghas             |
| read_file                     | ❌     | Disabled — use convert_to_markdown       |

## Missing Binaries / Services

| Component       | Status | Action                                                             |
| --------------- | ------ | ------------------------------------------------------------------ |
| project-rag     | ❌     | `cargo install --git https://github.com/Brainwires/project-rag`    |
| reactive-memory | ❌     | Clone from github.com/toxicwind/reactive-memory, `dotnet run`      |
| redis-cli       | ❌     | `sudo pacman -S redis`                                             |
| qdrant          | ❌     | `docker run -p 25133:25133 qdrant/qdrant` or `sudo pacman -S qdrant` |
| prometheus      | ❌     | `sudo pacman -S prometheus`                                        |

## Remaining Work (Priority Order)

### 1. Install missing services

```bash
# Redis
sudo pacman -S redis
systemctl --user start redis

# Qdrant (Docker)
docker run -d -p 25133:25133 qdrant/qdrant

# Prometheus
sudo pacman -S prometheus
systemctl --user start prometheus
```

### 2. Build project-rag

```bash
cargo install --git https://github.com/Brainwires/project-rag
```

### 3. Clone & build reactive-memory

```bash
git clone https://github.com/toxicwind/reactive-memory
cd reactive-memory
dotnet run
```

### 4. Downloads archaeology — find "free" provider code

Search Downloads for archives from past 5 days containing:

- `llama*` / `nim*` / `opencode*` / `route*` patterns
- Look for `.zip`, `.tar.gz`, `.pdf` files that might be code archives
- Extract and explore for modular provider implementations

### 5. Free provider router modularization

- Port sovereign-router router patterns into llama-swap's Go router core
- Each provider (OpenRouter, NVIDIA NIM, Groq, Cerebras, Google, Mistral) as modular adapter
- SSOT ports: LLAMA_SWAP=25100, SOVEREIGN_ROUTER=25104

### 6. NIM Inkling max_tokens verification

- Current: `nim-inkling` max_tokens: 8192
- Verify actual NVIDIA NIM API limits

### 7. Cerebras key validation

- Key in `~/.secrets` — all 403 errors
- Verify key validity, populate models if working

### 8. Zed restart

- New MCPs require Zed restart
- LSP settings already applied

## Provider Status

| Provider   | Key                | Models  | Status                 |
| ---------- | ------------------ | ------- | ---------------------- |
| OpenRouter | OPENROUTER_API_KEY | 10 free | Working                |
| NVIDIA NIM | NVIDIA_API_KEY     | 12      | Working (credit-based) |
| Groq       | GROQ_API_KEY       | 6       | Working (UA fix)       |
| Cerebras   | CEREBRAS_API_KEY   | 0       | 403 — key invalid?     |
| Google     | GOOGLE_API_KEY     | 4       | Working                |
| Mistral    | MISTRAL_API_KEY    | 4       | Working                |
| Opencode   | OPENCODER_API_KEY  | ?       | Free tier, Big Pickle  |

## Port Convention (SSOT)

| Service       | Port  |
| ------------- | ----- |
| llama-swap    | 25100 |
| rust-web      | 25101 |
| yote          | 25102 |
| openfang      | 25103 |
| sovereign-router    | 25104 |
| prometheus    | 25105 |
| hf-downloader | 25106 |
| watchdog      | 25111 |

## Key Files

- Router: `sovereign/tools/sovereign-router/sovereign-router/router.py`
- Mise: `sovereign/mise.toml`
- Tasks: `sovereign/mise/tasks/{up,_lib.sh,build-compose,...}`
- Settings: `~/.config/zed/settings.json`
- Secrets: `~/.secrets`
- llama-swap fork: `~/projects/llama-swap-main/`
- AGENTS.md: `sovereign/AGENTS.md`
