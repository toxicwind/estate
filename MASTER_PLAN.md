# Sovereign Pi Fork — Master Execution Plan

> **Generated**: 2026-07-28 | **Updated**: 2026-08-06 | **Context**: Full session replay across pi fork, llama-swap, GHAS MCP, mcpproxy, dashboards

---

## 🎯 ULTIMATE GOAL

```
User runs "pi" 
    → pi-agent (fork) uses llama-swap :25100 (AST matrix auto-routing)
    → AST matrix understands mcpproxy FIRST CLASS (via our pi-agent fork commits)
    → retrieve_tools shows ALL GitHub Advanced Search MCP endpoints
    → ghas narrow tools (ghas_search_code, ghas_search_repositories, etc.) accessible
    → User can say "search github for X" and it just works
```

---

## 📊 CURRENT STATE

| Domain | Status | Owner |
|--------|--------|-------|
| **Pi fork** (`toxicwind/pi`) | 4/9 critical PRs cherry-picked, 2 blocked on conflicts | Current |
| **llama-swap astmatrix** | Rate limiter rewritten (Go, full jitter) | Need to build+test |
| **GHAS MCP** | REFACTORED — needs full integration | In Progress |
| **sovereign-router** | STOPPED (:25104) | Need restart |
| **Inkling e2e** | Config fixed, not tested through full stack | Need test |
| **Dashboard SPA** | Done (JSON-driven, hash-routed) | ✅ |
| **AGENTS.md audit** | 358 files found, need dedup | In Progress |
| **mcpproxy+ghas integration** | DISCONNECTED — needs unification | In Progress |
| **pi-agent fork commits** | AST matrix mcpproxy awareness NOT YET DONE | BLOCKED |

---

## 🚨 CRITICAL: GHAS Integration

### Problem
- README has WRONG ports (35160-35162), actual are 25112-25114
- mcpproxy `ghas` server ≠ pitchfork `ghas-mcp` daemon (duplicated running)
- Tool surface reduced from 23+ to just `github_search` + `github_compare`
- pi-agent fork doesn't yet have AST matrix mcpproxy awareness

### Fix Plan
1. Fix README ports → 25112/25113/25114
2. Unify MCP transports (single server.ts handles stdio+HTTP)
3. Restore full tool surface (all narrow tools from tools.ts)
4. Add AST matrix mcpproxy awareness to pi-agent fork
5. Ensure retrieve_tools shows ALL ghas endpoints

See: `/home/toxic/sovereign/audit/GHAS_INTEGRATION_PLAN.md`

---

## 📋 PHASE 1: Fix Services (NOW)

```bash
1. mise run restart sovereign-router  # :25104 is stopped
2. mise run health                     # verify all green
3. cd /home/toxic/projects/github-advanced-search-mcp && bun build    # GHAS MCP streamable-http
```

## 📋 PHASE 2: GHAS Integration (CRITICAL)

```bash
# Fix README ports
cd /home/toxic/projects/github-advanced-search-mcp
# Update README to show 25112/25113/25114

# Restore full tool surface
# Add all narrow tools from tools.ts to server.ts tool list

# Unify transports
# Single server.ts handles both stdio (mcpproxy) and HTTP (pitchfork)
```

## 📋 PHASE 3: Pi-Agent Fork AST Matrix MCPproxy Awareness

```bash
cd /home/toxic/projects/pi-agent
# Add commits that make AST matrix mcpproxy-aware
# retrieve_tools should show ALL ghas narrow tools
# Test: pi → retrieve_tools → see ghas_search_code, ghas_search_repositories, etc.
```

## 📋 PHASE 4: Cherry-Pick Remaining PRs

| PR | Priority | Status | Action |
|----|----------|--------|--------|
| #6967 — Session metadata in bash | HIGH | **BLOCKED** (conflicts) | Manual merge: accept theirs, then fix our changes |
| #6285 — Fail truncated tool calls | HIGH | **BLOCKED** (merge commit) | Manual merge: `-m 1` then accept theirs |
| #6534 — Developer message role | MEDIUM | Pending | Fetch and cherry-pick |
| #6427 — Prompt cache miss tracking | MEDIUM | Pending | Fetch and cherry-pick |

## 📋 PHASE 5: Test Inkling Full Stack

```bash
curl -s -m 30 -X POST http://127.0.0.1:25100/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"thinkingmachines/inkling","messages":[{"role":"user","content":"say hi in 3 words"}],"reasoning_effort":"low","stream":false}'
```
Expected: `content` + optionally `reasoning_content`

## 📋 PHASE 6: llama-swap astmatrix Build + Verify

```bash
cd /home/toxic/projects/llama-swap-main
go build -o llama-swap .
go test ./internal/astmatrix/...
cd /home/toxic/sovereign && mise run restart llama-swap
```

## 📋 PHASE 7: Resume pi Session

```bash
cd /home/toxic/projects/pi-agent
echo "y" | pi --session 019fa9bc-ba3a-75f8-8db6-775027c8cbb7
```
