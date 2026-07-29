# Sovereign Pi Fork — Master Execution Plan

> **Generated**: 2026-07-28 | **Context**: Full session replay across pi fork, llama-swap, GHAS MCP, mcpproxy, dashboards

---

## 🎯 OVERVIEW

| Domain | Status | Owner |
|--------|--------|-------|
| **Pi fork** (`toxicwind/pi`) | 4/9 critical PRs cherry-picked, 2 blocked on conflicts | Current |
| **llama-swap astmatrix** | Rate limiter rewritten (Go, full jitter) | Need to build+test |
| **GHAS MCP** | server.ts rewritten with StreamableHTTP | Need build test |
| **sovereign-router** | STOPPED (:25104) | Need restart |
| **Inkling e2e** | Config fixed, not tested through full stack | Need test |
| **Dashboard SPA** | Done (JSON-driven, hash-routed) | ✅ |
| **pi session** | Resume `019fa9bc-ba3a-75f8-8db6-775027c8cbb7` | Final step |

---

## 📋 PHASE 1: Fix Services (NOW)

```bash
1. mise run restart sovereign-router  # :25104 is stopped
2. mise run health                     # verify all green
3. cd /home/toxic/projects/github-advanced-search-mcp && bun build    # GHAS MCP streamable-http
```

## 📋 PHASE 2: Cherry-Pick Remaining PRs

| PR | Priority | Status | Action |
|----|----------|--------|--------|
| #6967 — Session metadata in bash | HIGH | **BLOCKED** (conflicts) | Manual merge: accept theirs, then fix our changes |
| #6285 — Fail truncated tool calls | HIGH | **BLOCKED** (merge commit) | Manual merge: `-m 1` then accept theirs |
| #6534 — Developer message role | MEDIUM | Pending | Fetch and cherry-pick |
| #6427 — Prompt cache miss tracking | MEDIUM | Pending | Fetch and cherry-pick |

## 📋 PHASE 3: Test Inkling Full Stack

```bash
curl -s -m 30 -X POST http://127.0.0.1:25100/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"nim-inkling","messages":[{"role":"user","content":"say hi in 3 words"}],"reasoning_effort":"low","stream":false}'
```
Expected: `content` + optionally `reasoning_content`

## 📋 PHASE 4: llama-swap astmatrix Build + Verify

```bash
cd /home/toxic/projects/llama-swap-main
go build -o llama-swap .
# Test rate limiter
go test ./internal/astmatrix/...
# Restart llama-swap with new binary
cd /home/toxic/sovereign && mise run restart llama-swap
```

## 📋 PHASE 5: Resume pi Session

```bash
cd /home/toxic/projects/pi-agent
echo "y" | pi --session 019fa9bc-ba3a-75f8-8db6-775027c8cbb7
```
