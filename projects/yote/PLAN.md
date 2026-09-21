# Yote Maximal Integration Plan

**Status**: Planning → Active → **BRUTEFORCE EXECUTION**
**Updated**: 2026-08-07
**Goal**: Make Yote work **MAXIMALLY** — not just a Telegram wrapper, but a **full sovereign Telegram gateway** that leverages OpenFang's agent ecosystem, Overlord MTProto, and the sovereign mesh. **Nightly self-updates, PR cherry-picking, agent swarms, self-improving agents.**

---

## 🎯 Current State — Sovereign Directory Overview

| Component | Status | Notes |
|-----------|--------|-------|
| **Yote Telegram Gateway** | Running on :25102 | Uses OpenFang external HTTP (bun) |
| **OpenFang Backend** | Running on :25196 (kernel) / :25103 (mesh-front) | 8 agents running |
| **Overlord (MTProto)** | Connected | Userbot via GramJS (bun) |
| **Yote → OpenFang Chat** | Working | `openfang:<agent>` model routing |
| **OpenFang Agents** | 20 agents | `coyote`, `coder-max`, `sage`, `planner`, etc. |
| **Overlord MTProto** | Connected | Userbot via GramJS (bun) |
| **Mesh Integration** | Partial | `/mesh` endpoint exists |
| **Health Monitoring** | Basic | `/health`, `/status`, `/health` commands |
| **Test Scaffold (Pup Trix)** | Configured | Second Telegram key for channel monitoring & direct Yote interaction in channels |
| **Pup Trix User (716302190)** | Configured | `YOTE_TARGET_USER=716302190` — Second Telegram key directly hooked to user "pup trix". Used for: channel monitoring, direct Yote interaction in channels, `YOTE_TELEGRAM_CHANNELS` defines monitored channels, saved test scaffolding directly to chat history |

### Sovereign Directory — Key Files
| File | Purpose | Priority |
|------|---------|----------|
| `/home/toxic/sovereign/README.md` | Full stack docs | HIGH |
| `/home/toxic/sovereign/pitchfork.toml` | Service orchestration | HIGH |
| `/home/toxic/sovereign/mise.toml` | Toolchain + tasks | HIGH |
| `/home/toxic/sovereign/config/ports.env` | Port SSOT | HIGH |
| `/home/toxic/sovereign/.envrc` | Direnv auto-load | MEDIUM |
| `/home/toxic/sovereign/.secrets.age` | Encrypted secrets | CRITICAL |
| `/home/toxic/sovereign/.gitignore` | Git hygiene | MEDIUM |
| `/home/toxic/sovereign/MASTER_PLAN.md` | Master execution plan | HIGH |

---

## 🚀 PHASE 0: OPENFANG MAXIMAL AUDIT & AGENT FIX (CRITICAL - BEFORE PHASE 1)

### 0.1 OpenFang Config Audit
- [x] Check OpenFang config.toml at `/home/toxic/.openfang/config.toml` (or wherever OpenFang config lives)
- [x] Verify `model` defaults for all agents are correct
- [x] Check `model_provider` mappings (llama, anthropic, etc.)
- [x] Verify `model_tier` and `mode` settings
- [x] Check `NVCF-POLL-SECONDS` header in NVIDIA models

### 0.2 Agent Model Fix (ALL AGENTS)
**Current agents have WRONG models:**
- `coyote` → `mradermacher/qwen3.5-9b-deepseek-v4-flash-i1-q4_k_m` (should be `thinkingmachines/inkling` for reasoning)
- `coder-max` → `beellama/qwen-flash-128k` (should use `thinkingmachines/inkling` for coding)
- `sage` → `mradermacher/qwen3.5-9b-deepseek-v4-flash-i1-q4_k_m`
- `planner` → `mradermacher/qwen3.5-9b-deepseek-v4-flash-i1-q4_k_m`
- `researcher` → `mradermacher/qwen3.5-9b-deepseek-v4-flash-i1-q4_k_m`
- `coder-max-recovery` → `beellama/qwen-flash-128k`
- `solidity-security-auditor` → `beellama/qwen-flash-128k`
- `predictor-hand` → `beellama/qwen-flash-64k`
- `arbitrage-monitor` → `beellama/qwen-flash-128k`
- `security-auditor-max` → `beellama/qwen-flash-128k`
- `browser-hand` → `beellama/qwen-flash-128k`
- `coder-max` → `beellama/qwen-flash-128k`
- `whisper` → `beellama/exaone-4-0-1-2b-iq4xs`
- `analyst` → `beellama/qwen-flash-256k`
- `sage` → `mradermacher/qwen3.5-9b-deepseek-v4-flash-i1-q4_k_m`
- `orchestrator-max` → `beellama/qwen-flash-128k`
- `writer` → `mradermacher/qwen3.5-9b-deepseek-v4-flash-i1-q4_k_m`
- `dealigner` → `beellama/exaone-4-0-1-2b-iq4xs`
- `test-engineer` → `beellama/qwen-flash-128k`
- `debugger` → `beellama/qwen-flash-128k`

**CORRECT MAPPINGS:**
- **Reasoning/Coding agents** (`coder-max`, `sage`, `planner`, `researcher`, `coyote`, `coder-max-recovery`, `security-auditor-max`, `test-engineer`, `debugger`) → `thinkingmachines/inkling` (via NVIDIA NIM)
- **Long context agents** (`analyst`, `arbitrage-monitor`, `orchestrator-max`) → `beellama/qwen-flash-256k` or `beellama/qwen-flash-128k`
- **Fast/Utility agents** (`whisper`, `dealigner`, `coyote`) → `beellama/exaone-4-0-1-2b-iq4xs` or `beellama/qwen-flash-64k`

- [x] Update each agent in OpenFang UI or via API
- [x] Verify `model_provider` is correct (`nvidia` for Inkling, `llama` for local)
- [x] Set `reasoning: true` for Inkling agents
- [x] Set `input: ["text", "image"]` for multimodal agents

### 0.3 OpenFang Config Maximal
- [x] Run `openfang doctor` or equivalent diagnostic
- [x] Check config.toml for:
  - Correct `api_key` for NVIDIA API
  - Correct `base_url` for NVIDIA (`https://integrate.api.nvidia.com/v1`)
  - `NVCF-POLL-SECONDS: "3600"` header for NVIDIA models
  - `reasoning: true` for Inkling
  - `input: ["text", "image"]` for multimodal
  - `compat.supportsReasoningEffort: true` for Inkling
  - `thinkingLevelMap` for Inkling effort mapping
  - `chatTemplateKwargs` for NVIDIA tml-renderers
- [x] Use pitchfork to manage OpenFang service
- [x] Run OpenFang health checks via pitchfork

### 0.4 Agent Verification via Pitchfork
- [x] Use pitchfork to list all OpenFang agents
- [x] Verify each agent's model matches its role
- [x] Run probe on each agent to verify they respond
- [x] Document each agent's correct model mapping

### 0.5 Pitchfork Integration
- [x] Add OpenFang to pitchfork.toml if not present
- [x] Define OpenFang service with proper health checks
- [x] Add OpenFang restart/health commands to pitchfork

### 0.5 Update Yote Integration
- [x] Update yote to use corrected agent models
- [x] Update yote's agent routing logic
- [x] Test each agent via yote `/agent` command

---

## 🚀 PHASE 1: CRITICAL INFRASTRUCTURE (IMMEDIATE)

### 1.1 Refresh Overlord Session
- [x] Run `bun run overlord:login` to generate fresh GramJS session
- [x] Update `.env` with new session string
- [x] Restart yote

### 1.2 Fix OpenFang URL Mismatch
- [x] Ensure OpenFang kernel is running on :25196 (single instance; :25203 retired 2026-09-21)
- [x] Verify :25103 is mesh-front proxying the :25196 kernel
- [x] Update yote to use `OPENFANG_URL` from env correctly

### 1.3 Set OpenFang API Key
- [x] Generate/set API key in OpenFang config.toml
- [x] Add to `.env`

### 1.4 README.md Alignment
- [x] Update `/home/toxic/sovereign/README.md` to reflect:
  - Correct ports for all services
  - OpenFang agent model mappings
  - Yote → OpenFang integration details
  - Pitchfork/mise task descriptions
  - Mesh integration endpoints
- [x] Add OpenFang agent model mapping table
- [x] Document OpenFang reasoning_effort support

### 1.5 pitchfork.toml Maximal
- [x] Add OpenFang service (already present in pitchfork.toml)
- [x] Add OpenFang agent management commands
- [x] Add health check for OpenFang agents via pitchfork
- [x] Add OpenFang restart with model reload
- [x] Add pitchfork service for yote hot-reload
- [x] Add `pitchfork logs <service> --follow` support
- [x] Add `pitchfork exec <service> -- <cmd>` for debugging

### 1.6 mise.toml Maximal
- [x] Add tasks for:
  - `mise run openfang:health` — OpenFang health check
  - `mise run openfang:agents` — list all agents
  - `mise run openfang:probe` — probe all agents
  - `mise run openfang:doctor` — diagnostic
  - `mise run openfang:fix-agents` — auto-fix agent models
  - `mise run yote:hot-reload` — hot reload yote
  - `mise run overlord:refresh` — refresh Overlord session
  - `mise run mesh:health` — full mesh health
  - `mise run mesh:topology` — show mesh topology
  - `mise run nightly:update` — trigger nightly update
  - `mise run cherry-pick:scan` — scan for cherry-pickable PRs
  - `mise run cherry-pick:apply` — apply cherry-picks
- [x] Add `mise run test:all` for full test suite
- [x] Add `mise run lint` with biome
- [x] Add `mise run typecheck` with tsgo
- [x] Add `mise run build:all` for full build

### 1.7 ports.env SSOT
- [x] Verify all ports in `config/ports.env` match pitchfork.toml
- [x] Add missing ports (byte-vision, kami-audit-dash, etc.)
- [x] Document port allocation strategy (25xxx ranges)

---

## 🚀 PHASE 2: MAXIMAL AGENT INTEGRATION (CORE)

## 🚀 PHASE 2: MAXIMAL AGENT INTEGRATION (CORE)

### 2.1 Agent Routing & Commands (MAXIMAL)
- [x] `/agent` — list all agents with status/model/latency
- [x] `/agent <name>` — set default agent for this chat
- [x] `/agent <name> <prompt>` — one-shot with specific agent
- [x] `/agents` — detailed list with model/provider/latency/status ✅
- [x] `/probe` — run health check on all ready agents (parallel)
- [x] `/probe <agent>` — test specific agent with custom prompt
- [x] `/status` — full system health (llama-swap, openfang, GPU, overlord, mesh)
- [x] `/agent <name> @chat` — cross-chat agent invocation

### 2.2 Agent Personality & System Prompts (MAXIMAL)
- [x] **Agent Registry**: `/home/toxic/sovereign/yote/config/agents/*.yaml` — each agent has:
  - `system_prompt`: Role-specific system prompt
  - `model`: Exact model ID (e.g., `thinkingmachines/inkling`)
  - `provider`: `nvidia` | `llama` | `openrouter` | `groq`
  - `reasoning_effort`: `low` | `medium` | `high` | `max`
  - `tools`: `bash` | `read` | `write` | `edit` | `search` | `mcp`
  - `context_window`: Auto-calculated from model
  - `temperature` | `top_p` | `max_tokens`
- [x] **Per-Chat Agent Override**: `/agent <name>` persists to `yote_chats.json`
- [x] **Agent Swarms**: `/swarm <agent1>,<agent2>,<agent3> <task>` — parallel execution with synthesis

### 2.3 Multi-Agent Workflows (MAXIMAL)
- [x] `/orchestrate <task>` — orchestrator-max breaks down task → delegates to agents
- [x] `/delegate <agent> <task>` — delegate to specific agent with context
- [x] `/chain <agent1> → <agent2> → <agent3> <task>` — sequential pipeline
- [x] `/parallel <agent1>,<agent2>,<agent3> <task>` — parallel execution + synthesis
- [x] `/swarm <agent1>,<agent2>,<agent3> <task>` — agent swarm with consensus
- [x] `/debate <agent1> vs <agent2> <topic>` — structured debate with judge agent

---

## 🚀 PHASE 3: OVERLORD MTProto MAXIMAL (WEEK 2-3)

### 3.1 Overlord Capabilities (MAXIMAL)
- [ ] `/mtproto <target> <message>` — send via Overlord MTProto
- [ ] `/mtproto status` — check Overlord connection + session health
- [ ] `/mtproto dialogs [limit]` — list recent dialogs with unread counts
- [ ] `/mtproto resolve @username` — resolve username to entity
- [ ] `/mtproto contacts` — list contacts with online status
- [ ] `/mtproto channels` — list joined channels/groups
- [ ] Auto-reconnect on session expiry with exponential backoff
- [ ] Handle flood wait gracefully with queue + jitter

### 3.2 Overlord + OpenFang Bridge (MAXIMAL)
- [ ] **Bridge Mode**: Forward OpenFang responses via Overlord to target chats
- [ ] **Media Bridge**: Use Overlord for media/file uploads (Bot API limited to 50MB)
- [ ] **Channel Management**: Create/delete channels, invite users, set admin rights
- [ ] `/mtproto forward <from> <to> <msg_id>` — forward messages
- [ ] `/mtproto clone <from_chat> <to_chat>` — clone channel structure
- [ ] **MTProto + HTTP Hybrid**: Use MTProto for real-time, HTTP for reliability

### 3.3 Overlord Session Management (MAXIMAL)
- [ ] **Auto-Session Refresh**: Detect invalid session → auto-re-login via GramJS
- [ ] **Session Backup**: Export StringSession to encrypted config on change
- [ ] **Multi-Account Support**: Run multiple Overlord instances for different purposes

---

## 🚀 PHASE 4: MESH INTEGRATION MAXIMAL (WEEK 3-4)

### 4.1 GHAS MCP Integration (MAXIMAL)
- [ ] `/ghas search <query>` — search GitHub code via GHAS MCP (narrow tools)
- [ ] `/ghas repo <owner/repo> <query>` — search specific repo
- [ ] `/ghas pr <owner/repo> <number>` — fetch PR details + files changed
- [ ] `/ghas issue <owner/repo> <number>` — fetch issue + comments
- [ ] `/ghas repo <owner/repo> stats` — repo stats (stars, forks, contributors)
- [ ] Auto-register ALL GHAS narrow tools in mesh (not just `github_search`)
- [ ] **GHAS Tool Surface**: All 23+ narrow tools from `tools.ts` exposed via mesh

### 4.2 Mesh Features (MAXIMAL)
- [ ] `/mesh services` — list all mesh services with health/status
- [ ] `/mesh call <service> <method> <args>` — call mesh service directly
- [ ] `/mesh health` — check all mesh service health (parallel)
- [ ] `/mesh topology` — visualize service dependencies
- [ ] Register yote as mesh service with `/mesh` endpoint + health check
- [ ] **Mesh Service Registry**: Auto-discover services via Consul/etcd or static config

### 4.3 Mesh Security (MAXIMAL)
- [ ] mTLS between mesh services
- [ ] JWT auth for mesh calls
- [ ] Rate limiting per service
- [ ] Circuit breakers + retries with exponential backoff

---

## 🚀 PHASE 5: LLM INTEGRATION MAXIMAL (WEEK 4-5)

### 5.1 Multi-Provider Chat (MAXIMAL)
- [ ] `/model <provider/model>` — direct model selection with autocomplete
- [ ] `/llm <prompt>` — use llama-swap fallback (local)
- [ ] `/inkling <prompt>` — use NVIDIA NIM Inkling (reasoning)
- [ ] `/nemotron <prompt>` — use Nemotron 3 Ultra/Super/Nano
- [ ] `/gemini <prompt>` — use Google Gemini 2.5 Flash/Pro
- [ ] `/groq <prompt>` — use Groq Compound/Compound-Mini
- [ ] `/cerebras <prompt>` — use Cerebras GPT-OSS
- [ ] `/openrouter <prompt>` — use OpenRouter free models
- [ ] Show model in response metadata + latency + tokens + cost

### 5.2 Context & Memory (MAXIMAL)
- [ ] **Per-Chat Conversation History**: SQLite + Vector DB (LanceDB) for semantic search
- [ ] `/context` — show current context window usage + token count
- [ ] `/clear` — clear chat history (with confirmation)
- [ ] `/summarize` — summarize conversation with agent
- [ ] `/export` — export chat as markdown/json
- [ ] `/import <file>` — import chat history
- [ ] **Semantic Memory**: LanceDB embeddings for cross-chat recall
- [ ] **Agent Memory**: Each agent maintains own memory namespace

### 5.3 Reasoning & Thinking (MAXIMAL)
- [ ] `/think <prompt>` — force reasoning mode (high effort)
- [ ] `/reason <prompt>` — show reasoning trace + final answer
- [ ] `/debug <prompt>` — show raw model output + token counts
- [ ] **Reasoning Effort Presets**: `none|minimal|low|medium|high|max` per model
- [ ] **Thinking Budget**: Auto-adjust `max_tokens` based on effort level

---

## 🚀 PHASE 6: ADMIN & MONITORING MAXIMAL (WEEK 5-6)

### 6.1 Admin Commands (MAXIMAL)
- [ ] `/admin restart <service>` — restart yote|openfang|llama|mesh|overlord
- [ ] `/admin logs <service> [lines] [--follow]` — tail logs with grep
- [ ] `/admin config` — show current config (redacted secrets)
- [ ] `/admin users` — list allowed users + last activity
- [ ] `/admin agents` — list OpenFang agents + status + model
- [ ] `/admin mesh` — mesh service status + topology
- [ ] `/admin gpu` — GPU utilization (nvidia-smi) + VRAM per model
- [ ] `/admin vram` — VRAM usage per model + recommendations
- [ ] `/admin secrets` — list secrets (redacted) + rotation status
- [ ] `/admin backup` — backup configs + chats + sessions to encrypted archive
- [ ] `/admin restore <backup>` — restore from backup

### 6.2 Monitoring (MAXIMAL)
- [ ] `/metrics` — Prometheus-style metrics (HTTP, WebSocket)
- [ ] `/health detailed` — full system health check (parallel)
- [ ] `/gpu` — GPU utilization (nvidia-smi) + VRAM per model + temp/power
- [ ] `/vram` — VRAM usage per model + fragmentation + recommendations
- [ ] `/latency` — P50/P95/P99 latency per model + provider
- [ ] `/cost` — estimated cost per model + total daily/monthly
- [ ] **Alerting**: Telegram alerts on: service down, high latency, OOM, GPU temp

### 6.3 Observability Stack (MAXIMAL)
- [ ] **Prometheus + Grafana**: Metrics + dashboards
- [ ] **Loki + Promtail**: Log aggregation
- [ ] **Tempo**: Distributed tracing
- [ ] **Alertmanager**: Alert routing + deduplication

---

## 🚀 PHASE 7: AGENT SWARMS & SELF-IMPROVEMENT (WEEK 6-8)

### 7.1 Agent Swarms (MAXIMAL)
- [ ] **Swarm Coordinator Agent**: Orchestrates multi-agent tasks
- [ ] **Specialized Agents**: 
  - `coder-max` → coding tasks
  - `researcher` → web search + synthesis
  - `planner` → task decomposition
  - `critic` → code review + security audit
  - `test-engineer` → test generation + execution
  - `debugger` → bug reproduction + fix
  - `architect` → system design
  - `security-auditor-max` → security review
- [ ] **Swarm Patterns**:
  - `/swarm code <task>` → coder-max + test-engineer + critic
  - `/swarm research <topic>` → researcher + analyst + writer
  - `/swarm debug <error>` → debugger + coder-max + test-engineer
  - `/swarm audit <code>` → security-auditor-max + coder-max + critic

### 7.2 Self-Improving Agents (MAXIMAL)
- [ ] **Agent Feedback Loop**: 
  - Collect user feedback (👍/👎) per response
  - Store in LanceDB with embedding
  - Weekly fine-tuning via LoRA on feedback data
- [ ] **Auto-Prompt Optimization**:
  - Track which prompts succeed/fail
  - Genetic algorithm to evolve system prompts
  - A/B test prompt variants per agent
- [ ] **Model Selection Learning**:
  - Track latency/cost/quality per model per task type
  - Auto-route to best model for task type
- [ ] **Agent Evolution**:
  - Agents that consistently fail → auto-disable + alert
  - New agents auto-generated from task patterns

### 7.3 Nightly Agent Evolution (MAXIMAL)
- [ ] **Nightly Benchmark Suite**: Run benchmark prompts against all agents
- [ ] **Regression Detection**: Alert if agent quality drops >5%
- [ ] **Auto-Rollback**: Revert agent config if regression detected
- [ ] **Weekly Report**: Agent performance + cost + user satisfaction

---

## 🚀 PHASE 8: NIGHTLY UPDATES & PR CHERRY-PICKING (CONTINUOUS)

### 8.1 Nightly Update Pipeline (MAXIMAL)
```yaml
# .github/workflows/nightly-update.yml
name: Nightly Update
on:
  schedule:
    - cron: '0 3 * * *'  # 3 AM UTC
  workflow_dispatch:
jobs:
  update:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4
      - name: Fetch upstream
        run: git fetch upstream main
      - name: Check for changes
        run: |
          CHANGES=$(git log HEAD..upstream/main --oneline | wc -l)
          echo "changes=$CHANGES" >> $GITHUB_OUTPUT
      - name: Run tests
        if: ${{ steps.check.outputs.changes > 0 }}
        run: bun test
      - name: Build
        if: ${{ steps.check.outputs.changes > 0 }}
        run: bun run build
      - name: Health check
        if: ${{ steps.check.outputs.changes > 0 }}
        run: |
          curl -f http://localhost:25100/health
          curl -f http://localhost:25103/api/health
      - name: Deploy
        if: ${{ steps.check.outputs.changes > 0 && success() }}
        run: |
          git merge upstream/main
          bun run build
          systemctl reload yote
      - name: Rollback on failure
        if: failure()
        run: |
          git reset --hard HEAD~1
          systemctl reload yote
          gh issue create --title "Nightly update failed" --body "Auto-rollback triggered"
```

### 8.2 PR Cherry-Pick Automation (MAXIMAL)
```typescript
// scripts/cherry-pick.ts
// Daily scan of toxicwind/pi-agent PRs
// Auto-apply if: CI passes, no conflicts, tests pass
// Manual queue for: breaking changes, config, schema
// Labels: "cherry-pick-ready", "cherry-pick-blocked", "cherry-pick-done"
```

### 8.3 Dependency Update Bot (MAXIMAL)
- [ ] **Renovate/Dependabot Config**: Auto-update deps with tests
- [ ] **Pinning Policy**: Pin major versions, auto-update minor/patch
- [ ] **Security Updates**: Immediate PR for CVE fixes

---

## 🚀 PHASE 9: CUTTING-EDGE FEATURES (WEEK 8-12)

### 9.1 Real-Time Collaboration (MAXIMAL)
- [ ] **Shared Sessions**: Multiple users in same chat session
- [ ] **Live Editing**: Collaborative code editing via Yote
- [ ] **Pair Programming**: Two users + one agent = trio coding

### 9.2 Voice + Multimodal (MAXIMAL)
- [ ] **Voice Messages**: OpenFang audio input → Whisper → agent → TTS response
- [ ] **Image Analysis**: Send photo → agent analyzes + responds
- [ ] **Screen Share**: Overlord captures screen → agent analyzes

### 9.3 Agent Marketplace (MAXIMAL)
- [ ] **Agent Registry**: Community agents installable via `/agent install <name>`
- [ ] **Agent Templates**: Cookiecutter for new agent types
- [ ] **Agent Versioning**: Semantic versioning + changelog per agent

### 9.4 Sovereign Mesh Expansion (MAXIMAL)
- [ ] **Multi-Node Mesh**: Yote + OpenFang + llama-swap on separate nodes
- [ ] **Geo-Distributed**: Run mesh nodes in different regions
- [ ] **Mesh Federation**: Connect multiple sovereign meshes

---

## 📋 TASK TRACKING — BRUTEFORCE EXECUTION ORDER

### WEEK 1 (IMMEDIATE - BRUTEFORCE)
- [ ] **Day 1**: Phase 0 (OpenFang Audit + Agent Fix) + Phase 1.1-1.3
- [ ] **Day 2**: Phase 1.4-1.7 (README, pitchfork, mise, ports)
- [ ] **Day 3**: Phase 2.1 (Agent Commands Maximal)
- [ ] **Day 4**: Phase 2.2 (Agent Registry YAML) + 2.3 (Swarm Patterns)
- [ ] **Day 5**: Phase 3.1-3.3 (Overlord Maximal)
- [ ] **Day 6**: Phase 4.1-4.3 (Mesh Maximal)
- [ ] **Day 7**: Integration testing + Nightly pipeline deploy

### WEEK 2 (AGENT SWARMS + SELF-IMPROVEMENT)
- [ ] Phase 5.1-5.3 (LLM Maximal + Reasoning)
- [ ] Phase 6.1-6.3 (Admin + Monitoring + Observability)
- [ ] Phase 7.1-7.3 (Agent Swarms + Self-Improvement + Nightly Evolution)

### WEEK 3 (CUTTING EDGE)
- [ ] Phase 8.1-8.3 (Nightly Pipeline + PR Cherry-Pick + Dep Updates)
- [ ] Phase 9.1-9.4 (Real-time + Voice + Marketplace + Federation)

---

## 🔧 CONFIGURATION FILES — SINGLE SOURCE OF TRUTH

| File | Purpose | Priority | Managed By |
|------|---------|----------|------------|
| `/home/toxic/sovereign/yote/.env.age` | Secrets (encrypted) | CRITICAL | `age` + `sops` |
| `/home/toxic/sovereign/yote/config/agents/*.yaml` | Agent Registry | HIGH | Git |
| `/home/toxic/sovereign/yote/src/yote.ts` | Main Logic | HIGH | Git |
| `/home/toxic/sovereign/yote/src/lib/openfang-client.ts` | OpenFang Client | HIGH | Git |
| `/home/toxic/sovereign/yote/src/lib/overlord.ts` | MTProto Userbot | HIGH | Git |
| `/home/toxic/sovereign/config/ports.env` | Port SSOT | HIGH | Git |
| `/home/toxic/sovereign/.secrets.age` | Shared Secrets | CRITICAL | `age` + `sops` |
| `/home/toxic/sovereign/config/ports.env` | Port SSOT | HIGH | Git |
| `/home/toxic/sovereign/pitchfork.toml` | Service Definitions | HIGH | Git |
| `/home/toxic/sovereign/mise.toml` | Toolchain + Tasks | HIGH | Git |
| `/home/toxic/sovereign/README.md` | Documentation | HIGH | Git |
| `/home/toxic/sovereign/.envrc` | Direnv Config | MEDIUM | Git |
| `/home/toxic/sovereign/.secrets.age` | Shared Secrets | CRITICAL | `age` + `sops` |
| `/home/toxic/sovereign/.gitignore` | Git Hygiene | MEDIUM | Git |
| `/home/toxic/sovereign/MASTER_PLAN.md` | Master Plan | HIGH | Git |

---

## 🍒 PR CHERRY-PICK QUEUE (from toxicwind/pi-agent)

| PR | Priority | Status | Area | Action |
|----|----------|--------|------|--------|
| #6967 | HIGH | Blocked (conflicts) | Session metadata in bash | Manual merge |
| #6285 | HIGH | Blocked (merge commit) | Fail truncated tool calls | Manual merge |
| #6534 | MEDIUM | Pending | Developer message role | Cherry-pick |
| #6427 | MEDIUM | Pending | Prompt cache miss tracking | Cherry-pick |
| #6968 | LOW | Pending | Skip empty usage in Anthropic | Cherry-pick |
| #acda30456 | LOW | Pending | Truncated tool call fail fast | Cherry-pick |

**Cherry-Pick Command**: `bun run scripts/cherry-pick.ts --pr=<number> --auto`

---

## 📋 BRUTEFORCE EXECUTION CHECKLIST

### DAY 1 (TODAY)
- [ ] Phase 0: OpenFang Audit + Agent Fix
- [ ] Phase 1.1-1.3: Critical Infra
- [ ] Phase 1.4: README.md Alignment
- [ ] Phase 1.5: pitchfork.toml Maximal
- [ ] Phase 1.6: mise.toml Maximal
- [ ] Phase 1.7: ports.env SSOT

### DAY 2
- [ ] Phase 2.1: Agent Commands Maximal
- [ ] Phase 2.2: Agent Registry YAML
- [ ] Phase 2.3: Swarm Patterns

### DAY 3
- [ ] Phase 3.1-3.3: Overlord Maximal
- [ ] Phase 4.1-4.3: Mesh Maximal

### DAY 4
- [ ] Phase 5.1-5.3: LLM Maximal + Reasoning
- [ ] Phase 6.1-6.3: Admin + Monitoring + Observability

### DAY 5
- [ ] Phase 7.1-7.3: Agent Swarms + Self-Improvement
- [ ] Phase 8.1-8.3: Nightly Pipeline + PR Cherry-Pick + Dep Updates

### DAY 6-7
- [ ] Phase 9.1-9.4: Cutting Edge (Voice, Marketplace, Federation)
- [ ] Integration Testing + Nightly Pipeline Deploy
- [ ] Documentation + Runbooks

---

## 🎯 SUCCESS CRITERIA (DEFINITION OF DONE)

- [ ] **All 20 OpenFang agents** have correct models + verified via probe
- [ ] **Nightly updater** runs at 3 AM, auto-merges, auto-rolls back on failure
- [ ] **PR cherry-pick pipeline** auto-applies labeled PRs, queues blocked ones
- [ ] **Agent swarms** execute `/swarm` commands with measurable quality improvement
- [ ] **Self-improving agents** show measurable quality improvement week-over-week
- [ ] **Overlord MTProto** handles media, channels, flood wait gracefully
- [ ] **Mesh** exposes all 23+ GHAS tools + custom services
- [ ] **Observability** stack (Prometheus/Grafana/Loki/Tempo) fully deployed
- [ ] **Zero manual intervention** for 7 consecutive days

---

## 🔄 UPDATE LOG

| Date | Task | Status |
|------|------|--------|
| 2026-08-07 | Plan created | ✅ |
| 2026-08-07 | Phase 0-1 identified | 🔄 |
| 2026-08-07 | Cutting-edge goals added | ✅ |
| 2026-08-07 | PR cherry-pick queue added | ✅ |
| 2026-08-07 | Bruteforce execution order defined | ✅ |
| 2026-08-07 | README, pitchfork, mise, ports integrated | ✅ |
| 2026-08-07 | Sovereign directory structure mapped | ✅ |
| 2026-08-07 | OpenFang maximal control added | ✅ |

---

**NEXT ACTION**: Begin Phase 0 — OpenFang Audit + Agent Fix. Start with `openfang doctor` and agent model verification via pitchfork. Then proceed to Phase 1 (README, pitchfork, mise, ports alignment).