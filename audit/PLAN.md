# Sovereign Integration Plan

## Active Architecture

### Core Stack
- **Pi-agent fork** (toxicwind) — coding agent with full MCP stack
- **llama-swap** (:25100) — LLM frontend with AST matrix auto-routing
- **mcpproxy** (:25109) — MCP federation layer (41 servers including GHAS)
- **GHAS** (:25112/25113/25114) — GitHub Advanced Search (API, MCP, Frontend)
- **LongCat 2.0** — primary model (free, 131K context)
- **OpenCode** — coding agent for audit/fix tasks

### Port SSOT (ports.env)
```
25100 llama-swap (AST matrix)
25109 mcpproxy (federation)
25112 ghas-api
25113 ghas-mcp
25114 ghas-frontend
25189 nim-queue
```

### Model Config
- **Primary**: LongCat 2.0 Free (`meituan/longcat-2.0`)
- **Coding agent**: OpenCode (`OPENCODE_API_KEY`)
- **Fallback**: thinkingmachines/inkling (via NIM queue)

## Integration Tasks (Priority Order)

### 1. Fix GHAS Integration
- [ ] Fix README ports (3516x → 2511x)
- [ ] Unify MCP transports (single server.ts handles stdio+HTTP)
- [ ] Restore full tool surface (23+ narrow tools)
- [ ] Connect API server to MCP server

### 2. Fix Pitchfork/Mise Integration
- [ ] Add missing daemons to mise.toml tasks (17 missing)
- [ ] Fix external dir references (4 daemons)
- [ ] Add dependency ordering to tasks
- [ ] Single source of truth for ports

### 3. Pi-Agent Fork Commits
- [ ] AST matrix mcpproxy awareness
- [ ] retrieve_tools shows ALL ghas narrow tools
- [ ] LongCat 2.0 as default model
- [ ] OpenCode integration

### 4. Audit & Cleanup
- [ ] Dedup 358 AGENTS.md files
- [ ] Symlink copies to canonical
- [ ] Document project-specific exceptions

## Tools Built

| Tool | Path | Purpose |
|------|------|---------|
| audit-runner | `audit/` | Bun project for audit scripts |
| inventory_agents_md.ts | `audit/scripts/` | AGENTS.md file inventory |
| audit_services.ts | `audit/scripts/` | Service health checks |
| repo_discovery.ts | `audit/scripts/` | Adaptive GitHub repo search |
| profile_manager.ts | `audit/scripts/` | Agent profile management |
| full_audit.ts | `audit/scripts/` | Orchestrate all audits |

## Files Generated

```
sovereign/
├── audit/
│   ├── scripts/           # Bun TS audit scripts
│   ├── package.json       # Bun project
│   ├── PLAN.md            # AGENTS.md audit plan
│   ├── GHAS_INTEGRATION_PLAN.md
│   ├── agents_md_inventory.json
│   └── agents_md_list.txt
├── profiles/
│   └── agents_profile.json  # LongCat + OpenCode config
├── agents/                  # Agent identities (empty)
├── MASTER_PLAN.md           # Updated with GHAS integration
└── AGENTS.md                # Rewritten (universal rules)
```
