# GHAS — Production Integration Plan

## Current Mess (What Previous Model Left Us)

### Ports (WRONG in README, correct everywhere else)
| Service | README LIES | ACTUAL | Config Source |
|---------|-------------|--------|---------------|
| Frontend | 35160 | **25114** | pitchfork.toml |
| API | 35161 | **25112** | pitchfork.toml |
| MCP HTTP | 35162 | **25113** | pitchfork.toml |
| mcpproxy | not mentioned | **25109** | mcp_config.json |

### Dual Running (BIZARRE)
- `ghas` in mcpproxy → runs `bun run server.ts --mode stdio` (stdio transport)
- `ghas-mcp` in pitchfork → runs `bun run server.ts --mode http` (HTTP on 25113)
- Same codebase, TWO transports, NO shared state

### Integration Gaps
1. README ports are wrong (35160-35162)
2. MCP server has `github_search` tool (singular) but also has narrow tools in tools.ts
3. mcpproxy `ghas` server ≠ pitchfork `ghas-mcp` daemon (duplicated)
4. API server (`apps/api`) is disconnected from MCP server
5. Frontend (`apps/frontend`) is a separate Next.js app, not integrated
6. Shell scripts should be `.ts` files runnable via `bun run`

## Target Architecture

```
                    ┌─────────────────────────────────────────────────┐
                    │              mcpproxy (:25109)                  │
                    │         (federation layer, 41 servers)          │
                    └───────────────────┬─────────────────────────────┘
                                        │ stdio
                    ┌───────────────────▼─────────────────────────────┐
                    │           GHAS MCP Server (Bun)                 │
                    │   apps/mcp/src/server.ts                        │
                    │   ─┬─ github_search (unified)                   │
                    │   ─┬─ github_search_code                        │
                    │   ─┬─ github_search_repositories                │
                    │   ─┬─ github_search_issues                     │
                    │   ─┬─ github_search_pull_requests              │
                    │   ─┬─ github_search_users                      │
                    │   ─┬─ github_compare                           │
                    │   ─┬─ github_get_repository                    │
                    │   ─┴─ github_get_file_contents                 │
                    └───────────────────┬─────────────────────────────┘
                                        │ internal
                    ┌───────────────────▼─────────────────────────────┐
                    │       github-client + ranking engine            │
                    │   packages/github-client/                      │
                    │   ─┬─ index.ts (search, retry, cache)          │
                    │   ─┬─ engine.ts (query expansion)              │
                    │   ─┬─ blackbird.ts (rate limit)                │
                    │   ─┴─ ranking/ (bm25, tokenize, weights)       │
                    └─────────────────────────────────────────────────┘
```

## Integration Steps

### 1. Fix README Ports ✅
- Update all 3516x → 2511x
- Add mcpproxy to architecture diagram

### 2. Unify MCP Transports
- Single server.ts that handles BOTH stdio AND HTTP
- Use `--mode stdio` for mcpproxy
- Use `--mode http` for direct HTTP access (pitchfork)
- Both modes share the same tool definitions

### 3. Fix Tool Surface
- Current: only `github_search` + `github_compare`
- Target: full narrow tool set from tools.ts
- All tools registered in server.ts tool list

### 4. Bun-First Scripts
- Convert shell scripts to `.ts` files
- Run via `bun run scripts/<name>.ts`
- Use Bun.spawn(), Bun.file(), Bun.write()

### 5. API Server Integration
- apps/api should be the HTTP control plane
- MCP server and API share the same github-client
- Frontend talks to API, API talks to github-client

### 6. Single Source of Truth
- All ports in pitchfork.toml
- README mirrors pitchfork.toml
- No hardcoded values anywhere

## Critical: What NOT to Do
- Don't convert shell scripts that are just Docker entrypoints
- Don't rewrite the ranking engine (it's already Bun/TS)
- Don't split into more microservices
- Don't add new ports
