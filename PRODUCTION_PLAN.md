# Sovereign Production Plan + ADHD Catch-Up

**Date:** 2026-07-07  
**Status:** Phase 0 in progress  
**Owner:** toxic / agent stack

This document is your **single scroll** for everything we touched in the last session, what's done, what's broken, and the maximal production path forward.

---

## ADHD Catch-Up: Every User Request (Chronological)

| #   | You asked                                                                      | Status                                                                                                                          |
| --- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Fix antigravity launcher                                                       | **Mostly done** — wrappers have `--local`, `--devenv-25001`, `--cloud`; desktop actions added                                   |
| 2   | Add 25001 devenv as additional model + fix `/bin/python` + 25001-aware updater | **Partial** — devenv mode + updater health checks done; IDE python path fixed; **25001 still down** until llama-server restarts |
| 3   | Fix grep spamming zsh terminal                                                 | **Done** — `~/.local/bin/grep` LLM-safe wrapper, no alias                                                                       |
| 4   | Don't alias grep to rg                                                         | **Honored** — separate tools via PATH                                                                                           |
| 5   | Global grep env / column truncation                                            | **Done** — `GREP_MAX_COLUMNS`, match caps in wrapper                                                                            |
| 6   | Use llm_grep pattern from Downloads                                            | **Done** — ported to `~/.local/bin/grep`                                                                                        |
| 7   | GHAS MCP — specific, not generic GitHub MCP                                    | **Done** — `~/.grok/config.toml` + Antigravity parity                                                                           |
| 8   | Audit GHAS (weird fork, git history rollback concern)                          | **Done** — architecture confirmed; commit `17b326b` (not pushed)                                                                |
| 9   | Confirm frontend + API + MCP exist                                             | **Confirmed** — Bun monorepo, ports 35160/35161/35162                                                                           |
| 10  | Do items 1-2-3 async with subagents                                            | **Done** — GHAS committed, Grok config restored                                                                                 |
| 11  | Update GHAS README + cleanup audit (ask before delete)                         | **README done** — delete list below, **awaiting your approval**                                                                 |
| 12  | Gather chat history + maximal production plan (sovereign devenv)               | **This document**                                                                                                               |
| 13  | rg takes 27s on `/home/toxic`                                                  | **Fixed** — expanded `~/.ripgreprc` + new `~/.rgignore`                                                                         |

---

## What's Working Right Now

| System                  | State                                                                        |
| ----------------------- | ---------------------------------------------------------------------------- |
| GHAS stdio MCP          | Auth OK as `toxicwind`; `ghas_*` tools live                                  |
| Grok `config.toml`      | GHAS + devenv MCP + `localhost:25001` llama model                            |
| Antigravity MCP parity  | GHAS, ast-grep, context7, devenv, filesystem, markitdown                     |
| LLM-safe grep           | `~/.local/bin/grep` first in PATH (zshenv + Antigravity wrappers)            |
| Sovereign partial stack | Caddy :25000, openfang :25004, yote :25042, prometheus :25030, herder :25021 |
| GHAS git                | `17b326b` — 1 commit ahead of origin                                         |

---

## What's Broken / Blocking

| Issue                                      | Root cause                                                                                         | Fix (this session)                                                                                    |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| **`:25001` down**                          | llama-swap used `--slots 1` + bare `--flash-attn` (CLI regression); no warm `llama-server` process | Fixed `config.yaml` flags; restored `llama-server` in `processes.nix` — **needs `devenv up` restart** |
| Antigravity local mode falls back to cloud | 25001 unreachable                                                                                  | Restart sovereign after Phase 0                                                                       |
| GHAS API MCP sidecar spawn                 | `env.ts` ROOT pointed at `apps/`                                                                   | **Fixed** — 4 levels up + `.grok/.secrets` loader                                                     |
| Prometheus MCP wrong port                  | Config said `25013`, sovereign uses `25030`                                                        | **Fixed** in Grok + Antigravity configs                                                               |
| `/bin/python` IDE error                    | No interpreter path                                                                                | **Fixed** — `python.defaultInterpreterPath` → `/usr/bin/python3`                                      |

---

## Architecture Quick Reference

### Sovereign ports (SSoT: `modules/nix/ports.nix`)

| Port      | Service                                                  |
| --------- | -------------------------------------------------------- |
| 25000     | Caddy gateway                                            |
| **25001** | **llama-server** (primary LLM — Antigravity/Grok target) |
| 25004     | openfang                                                 |
| 25005     | rust-web                                                 |
| 25021     | llama-herder (llama-swap, on-demand models)              |
| 25022     | watchdog                                                 |
| 25030     | prometheus                                               |
| 25042     | yote                                                     |
| 25080     | landing                                                  |

### GHAS ports

| Port  | Service  |
| ----- | -------- |
| 35160 | frontend |
| 35161 | API      |
| 35162 | MCP HTTP |

### Config files (don't lose these)

| Path                                 | Role                      |
| ------------------------------------ | ------------------------- |
| `~/.grok/config.toml`                | Grok MCP + 25001 endpoint |
| `~/.grok/.secrets`                   | Token SSOT                |
| `~/.gemini/config/mcp_config.json`   | Antigravity MCPs          |
| `~/.local/bin/antigravity-*-wrapper` | Launcher modes            |
| `~/sovereign/devenv.nix`             | Production orchestration  |

---

## Maximal Production Plan (Phased DAG)

### Phase 0 — Unblock LLM (TODAY, blocking everything)

- [x] Fix `tools/llama-swap/config.yaml` (`--flash-attn on --parallel 1`)
- [x] Restore `llama-server` process in `modules/nix/processes.nix`
- [x] Fix openfang health probe → `/api/health`
- [ ] **YOU:** `cd ~/sovereign && devenv up` (or restart llama-server process)
- [ ] Verify: `curl http://127.0.0.1:25001/v1/models`

### Phase 1 — Config SSoT (Day 1)

- [ ] Generate `config.toml`, `Caddyfile`, `prometheus.yml` from Nix (`generators.nix`) — stop stale root copies
- [x] Fix prometheus MCP URL → 25030
- [ ] Align `~/.config/env.d/ai.env` `LLM_BASE_URL` → `http://127.0.0.1:25001/v1` (not vLLM)
- [ ] Add `modules/nix/mcp-registry.nix` — document GHAS/devenv/prometheus for agents
- [ ] Create `~/sovereign/.sovereign-devenv-version` for wrapper change detection

### Phase 2 — Secrets (Day 1–2)

- [ ] Expand `secretspec.toml`: `GITHUB_TOKEN`, `TELEGRAM_BOT_TOKEN`, `HF_TOKEN`, etc.
- [ ] Migrate `.env.local` secrets into secretspec profiles
- [ ] Remove hardcoded tokens from `mcp_config.json` (discord, context7)

### Phase 3 — Observability (Day 2–3)

- [ ] Add DB exporters matching `prometheus.yml` scrape jobs
- [ ] Alertmanager + recording rules (`llama_server_up`)
- [ ] Expand `watchdog.ts` to full PORTS map
- [ ] Regenerate `architecture.d2` from live processes

### Phase 4 — systemd / persistence (Day 3–4)

- [ ] `systemd/user/sovereign-devenv.service` → `devenv up --detach`
- [ ] `sovereign-health.timer` → `devenv tasks run sovereign:health`
- [ ] `sovereign-warm-llm.service` — POST default model on boot
- [ ] Resolve OpenFang port conflict (`:25004` devenv vs `:14720` systemd)

### Phase 5 — MCP agent surface (Day 4–5)

- [ ] Enable `playwright-fork-local` in Grok config
- [ ] GHAS as documented stdio (already works)
- [ ] `devenv mcp` with `cwd=/home/toxic/sovereign`
- [ ] Agent bootstrap snippet in README

### Phase 6 — Data plane + CI (Day 5–7)

- [ ] process-compose `depends_on` DAG (DBs → LLM → apps → caddy)
- [ ] `devenv test` with LLM inference smoke
- [ ] Backup task for `.postgres`, `.state`
- [ ] Push GHAS commit + sovereign changes to git remotes

---

## GHAS Cleanup — ASK BEFORE DELETE

**Nothing deleted yet.** Reply with tiers/numbers to remove.

### Tier A — Safe (generated junk, ~7.5 MB git-tracked)

| Path                                                   | Size    | Notes               |
| ------------------------------------------------------ | ------- | ------------------- |
| `audit_results.json`                                   | 7.3 MB  | One-off audit dump  |
| `search_*.log` (20 files)                              | ~180 KB | Stress test output  |
| `tool_list_output.json`, `tool_list_error.log`         | tiny    | Failed runs         |
| `consolidation_report.json` + `consolidation_audit.py` | ~64 KB  | One-off             |
| `cleanup_protocol.sh`                                  | 4 KB    | One-off runner      |
| `infra/*.log`                                          | ~12 KB  | Regenerates         |
| `.venv/` (local)                                       | ~76 MB  | `uv sync` recreates |

### Tier B — Medium (archive candidates)

| Path                                                     | Risk   | Notes                                     |
| -------------------------------------------------------- | ------ | ----------------------------------------- |
| `_production_archive/`                                   | medium | Old logs/research                         |
| `docs/history/`                                          | medium | **Contains leaked tokens** — redact first |
| `legacy/rust/`                                           | medium | Archaeology                               |
| `Cargo.toml` + `Cargo.lock`                              | medium | Missing `crates/`                         |
| `tests/` (Python)                                        | medium | References deleted FastMCP                |
| `pyproject.toml` + `uv.lock`                             | medium | Legacy Python client                      |
| `move_plan.md`, `duplication_report.md`, stale CHANGELOG | medium | Pre-Bun docs                              |

### Tier C — Risky (needs replacement before delete)

| Path                                           | Risk  | Notes                             |
| ---------------------------------------------- | ----- | --------------------------------- |
| `infra/docker-compose.yml`, Dockerfiles        | risky | Rust-based, broken                |
| `scripts/mcp_smoketest.sh`, `api_smoketest.sh` | risky | Rust smoke tests                  |
| `scripts/install-complete.sh`                  | risky | **Active** — update, don't delete |
| `scripts/sovereign-browser/`                   | risky | **Active** per AGENTS.md          |
| `scripts/sync-grok-mcp-descriptors.sh`         | risky | **Active**                        |

---

## Agent Quick Commands

```bash
# Sovereign health
cd ~/sovereign && devenv tasks run sovereign:health

# LLM check
curl -s http://127.0.0.1:25001/v1/models | head
curl -s http://127.0.0.1:25021/v1/models | head

# GHAS health (stdio)
source ~/.grok/.secrets
bun run --cwd ~/github-advanced-search-mcp apps/mcp/src/server.ts --mode stdio

# Fast search (prefer scoped paths)
rg 'pattern' ~/projects
rg 'pattern' ~/sovereign
# NOT: rg 'pattern' ~   (still huge even with ignores)

# Antigravity modes
antigravity-local-wrapper --local          # StrangeMerges default
antigravity-local-wrapper --devenv-25001   # sovereign devenv model from :25001
antigravity-local-wrapper --cloud          # Gemini
```

---

## Next Action For You

1. **Restart sovereign** to pick up llama-server + swap flag fixes
2. **Tell me which GHAS delete tiers** to execute (e.g. "delete all Tier A")
3. **Push GHAS** when ready: `cd ~/github-advanced-search-mcp && git push`
