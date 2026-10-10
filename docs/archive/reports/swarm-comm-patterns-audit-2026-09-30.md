# Swarm Communication Patterns — Ranked Audit (2026-09-30)

**By Magpie** 🪶 — pattern-borrow research for chatty multi-agent comms.
Seed: repos touching **huggingface + openai + swarm** (as a subset), ranked for
multi-agent conversation/coordination patterns borrowable for our fleet/squawk.

Method: GitHub-wide search (7 queries, 78 unique repos), top-12 deep audit of
READMEs + architecture docs. September-2026 grade: recency weighted over stars.

---

## Ranked repos

### 1. agentscope-ai/agentscope — 32,593★ — updated 2026-09-30 — Python
"Build and run agents you can see, understand and trust."
- **Unified event bus**: streams reasoning, tool calls, multimodal content (text/image/audio) to the frontend. One bus, typed events.
- **Pipeline**: run multiple agents by fixed logic **behind one event stream**. One stream per task, not per agent — kills fan-out noise.
- **A2A protocol** (shipped 2026-09): chat with any remote A2A agent via `A2AAgent`. Interop standard, not a custom wire.
- **Channels**: connect agents to IM platforms (Feishu/Lark, Discord, custom), with message routing.
- **TeamPipeline** (2026-09): leader agent delegates to member agents.
- **Middleware**: composable hooks across the loop (reply, reasoning, acting, model calling, permission, context compression).
- **Model routing middleware**: select the right chat model per reply.
- Borrow: typed event bus + one-stream-per-pipeline + A2A interop.

### 2. nullpointexception-i/agent-sphere — 120★ — updated 2026-09-30 — Java
AI agent orchestration platform. The best *engineered* comm layer in the set.
- **Redis event bus** (Redisson RTopic: `runtime.events` / `runtime.agui` / `runtime.chrome.*`): multi-replica delivery.
- **SSE reconnect replay**: event cache in Redis, single-writer, write-before-publish. Dropped clients replay on reconnect.
- **Exactly-once commands**: each `commandId` executed exactly once, reported via callback endpoint.
- **Single per-user task stream** (`/api/v1/runtime/user/task/stream`): backend fans out by session owner — no per-session following, no duplicate pushes.
- **Session-level stop**: cancel flag in Redis (`runtime:cancel-session:{id}`), checked at every cancellation point. Works across replicas.
- **ContactEnvelope** delegation: `{laneKey, args, upstream, upstream_visible, upstream_raw, truncated}` — oversized upstream truncated per-key but the envelope stays complete and parseable.
- **Reasoning persisted** (`agent_run.reasoning`): thinking rendered in history, not just live.
- Borrow: reconnect-replay cache, exactly-once commandIds, owner-fanout streams, parseable-truncation envelopes.

### 3. nirholas/three.ws — 219★ — updated 2026-09-30 — JS/TS
3D AI agent framework with LLM brains. Best presence + personality patterns.
- **Event bus decouples everything**: avatar emotion reacts to `speak` events without knowing the runtime exists; identity logs actions without knowing the UI exists. Testable, embeddable, composable.
- **Typed event table**: `speak {text, sentiment}` → avatar (emotion), identity (log), chat UI. Every event lists producers and consumers.
- **Protocol-event-driven emotion blending** (celebration, concern, curiosity, empathy, patience) — not a finite-state machine.
- **Live presence**: "Online · Mainland", friends graph, DMs, per-account realtime delivery hub.
- **AGENT_MANIFEST**: JSON schema contract every agent reads — body, brain, voice, memory, skills, signing.
- **Signed action log** + memory store.
- Borrow: producer→consumer event tables, presence protocol, agent manifest contract, event-driven personality (not FSM).

### 4. KCNyu/clawock — 16★ — updated 2026-09-30 — Python
"AI argues. Code settles. The losses stay on the page." Structured debate protocol.
- **Mandatory disagreement**: bull and bear researchers must genuinely disagree on at least one position, on the record. Unanimity reads as a *flag*, not evidence.
- **Devil's advocate attacks the strongest consensus**, never the weakest.
- **Risk voices + Judge**: aggressive/conservative/neutral argue; first-mover rotates so framing can't calcify. Judge names the strategy frame and writes `plan.json`.
- **Delivery receipts separate from task outcome**: "a completed task with a failed send stays visible; a missing message does not erase the work."
- **Preflight/postflight**: Python assembles only the blocks a run can use (preflight); validates, books to `memory/decisions.jsonl`, renders briefs (postflight).
- Borrow: mandatory-dissent debate shape, receipt/outcome separation, preflight context assembly.

### 5. CatOlin-Zhang/YouMi_Agent — 0★ — updated 2026-09-30 — Python
Lightweight multi-agent framework. Most production-hardened of the small ones.
- **Tenant-isolated message bus** (InProcess / WebSocket): `bus/` has WorkflowMessage, InProcessBroker, BusServer/Client with auth + tenant.
- **Plan-then-execute**: LLM generates structured `WorkflowPlan`, deterministic `WorkflowExecutor` schedules by DAG topology. Non-determinism confined to the planning layer.
- **PlanMemory**: execution plans persisted in SQLite, vectorized (sqlite-vec); cache hits skip redundant planning, keyword fallback.
- **MCP tool layer**: custom JSON-RPC 2.0, HOT/WARM/COLD dynamic load/unload, semantic vector search over tools.
- **OpenTelemetry tracing + audit logging** baked in. Retry/circuit-breaker, token auth + sandbox.
- Borrow: plan/execute split, plan-memory cache, tenant-isolated bus, OTel tracing as default.

### 6. prathyushnallamothu/swarmgo — 361★ — updated 2026-09-10 — Go
Go agents SDK (agents-sdk-go). Cleanest handoff primitive.
- **Two primitives: Agents + handoffs**. An agent hands off a conversation to another agent as a *function call* (`transferToAnotherAgent`).
- Runs almost entirely client-side; no stored state between calls (Chat Completions style).
- Concurrent agent execution, streaming support, context variables, memory management.
- Workflow shapes: supervisor, hierarchical, collaborative.
- Borrow: handoff-as-tool-call (no orchestrator needed for transfers).

### 7. ramicheAi/parallax-relay — 0★ — updated 2026-02-28 — TypeScript
"Spawn AI agents from any provider, wire them to channels, let them talk."
- **Channel is the addressing primitive**: `relay.spawn({channels: ['draft']})`, `relay.broadcast('draft', msg)`.
- Provider-agnostic (Claude/OpenAI/etc. per agent).
- Writer posts draft → editor receives → posts feedback → writer revises. Emergent turn-taking on a shared channel.
- Borrow: channels-as-addressing (maps directly onto squawk channels).

### 8. joshmu/ts-swarm — 33★ — updated 2026-04-16 — TypeScript
Minimal agentic lib: OpenAI Swarm simplicity + Vercel AI SDK flexibility.
- **Per-message agent attribution**: `message.swarmMeta.agentId` — every message knows which agent wrote it.
- `createAgent` + `<agent>.run()` orchestrates the swarm conversation with tool calling + handoffs.
- Borrow: `swarmMeta`-style attribution on every fleet message (who said it, which lane).

### 9. youseai/openai-swarm-node — 147★ — updated 2026-03-04 — JS
Node.js implementation of OpenAI's experimental Swarm.
- Chat-Completions-shaped messages; agent transfer as function call.
- Streaming client.
- Borrow: reference for the canonical Swarm handoff shape.

### 10. AbhiudayNarayan/event_swarm — 0★ — updated 2026-09-19 — JS
LangGraph orchestrator firing 7 specialized GPT-4o agents for event management.
- **WebSocket activity streaming** to a React/Tailwind realtime dashboard.
- One orchestrator graph, specialized agents in sequence.
- Borrow: live activity-stream dashboard pattern (what our fleet feed wants to be).

### 11. aletar89/hf-incident-research — 0★ — updated 2026-09-23 — research vault
Research behind the "HuggingFace incident" talk (23 Sept 2026) — OpenAI agent-swarm incidents. The exact huggingface+openai+swarm seed.
- **Provenance tags on every factual line**: `[STATED]` (source says it) / `[INFERRED]` / `[DISPUTED]` / `[SPECULATION]` / `[ILLUSTRATIVE]` / `[BREAKING]`.
- Obsidian vault, 48 notes, sources win over notes.
- Borrow: provenance tags for fleet claims — agents label how sure they are.

### 12. albertovalverde/huggingface-smolagents — 2★ — updated 2025-03-04 — Python
HF-native multi-agent (research → write → edit). Thin, but the HF-ecosystem reference point.
- Smolagents `CodeAgent`/`ToolCallingAgent` collaboration.
- Borrow: HF-native agent wiring if we ever route through HF Inference Providers.

---

## Borrowable patterns (concrete)

**P1. Typed event bus, one stream per pipeline.** AgentScope: multiple agents, one event stream per task. Fleet today = one global channel; consider per-mission streams with a typed event schema.

**P2. Reconnect-replay cache.** agent-sphere: Redis event cache, single-writer write-before-publish, clients replay on reconnect. Our feed drops history on reconnect — steal this.

**P3. Exactly-once commandIds.** agent-sphere: each command executed once, callback-reported. Fleet dedupe is name+time heuristic; commandIds are exact.

**P4. Owner-fanout, not per-session follow.** agent-sphere: one per-user stream, backend fans out by owner. Scales better than per-agent subscriptions.

**P5. Per-message agent attribution.** ts-swarm `swarmMeta.agentId`: every fleet message should carry agent id + lane, machine-readable.

**P6. Producer→consumer event tables.** three.ws documents every event's producers and consumers. Makes the bus self-describing; add to squawk docs.

**P7. Presence protocol.** three.ws "Online · Mainland" + per-account delivery hub. Fleet needs: who's online, what lane they're on, last heartbeat.

**P8. Agent manifest contract.** three.ws AGENT_MANIFEST (body/brain/voice/memory/skills/signing). Our agent.toml is the seed — extend toward a manifest.

**P9. Mandatory-dissent debate.** clawock: two voices must disagree on record; unanimity = flag. For oracle/design debates in fleet.

**P10. Receipt/outcome separation.** clawock: delivery receipts ≠ task outcome. A failed squawk send must not erase the work — exactly our outbox problem.

**P11. Provenance tags.** hf-incident-research: `[STATED]/[INFERRED]/[DISPUTED]/[SPECULATION]` on claims. Fleet agents should tag confidence.

**P12. Plan-then-execute, non-determinism at the edge.** YouMi: deterministic executor, LLM only plans. Our coordinators should emit plans, not improvise mid-run.

**P13. PlanMemory.** YouMi: vector-cached execution plans skip redundant planning. Coordinators replan the same lanes nightly — cache them.

**P14. Handoff as tool call.** swarmgo/OpenAI Swarm: transfer conversation by calling a function, no orchestrator in the loop. Lightweight delegation.

**P15. Channels as addressing.** parallax-relay: spawn onto channels, broadcast to channels. Squawk already has channels — lean in.

**P16. Preflight context assembly.** clawock: assemble only the blocks a run can use. Our spawn briefs should be preflights, not dumps.

**P17. A2A interop.** AgentScope's `A2AAgent`: speak to any remote A2A agent. If the industry converges here, our agents should too.

**P18. Reasoning persisted, not just live.** agent-sphere persists `reasoning_token` so history renders thinking. Fleet feed should keep agent reasoning, not just outcomes.

---

## Logging / observability notes (Chris's "awesome logs" question)

- **herd** (ours): structured Go logs, per-request tracing. The bar.
- **YouMi_Agent**: OpenTelemetry tracing + audit logging by default — the only small repo that treats observability as a feature, not an afterthought.
- **agent-sphere**: persisted reasoning + SSE event cache = full replay. Best "what happened" story.
- **clawock**: `memory/decisions.jsonl` ledger + public scorecard — decisions are append-only and graded.
- **three.ws**: signed action log — tamper-evident agent actions.
- **Our provider agents** (the ones serving through herd): they log at the provider level, not the agent level — they do NOT have herd-grade structured logs. If Chris wants agent-level observability on provider-routed agents, that's a gap: we'd need to wrap provider calls with our own trace/span layer (OpenTelemetry, per YouMi's pattern).

---

## Recommended next steps

1. Add `swarmMeta`-style attribution to every squawk message (P5) — smallest change, biggest debuggability win.
2. Prototype per-mission event streams (P1) alongside the global fleet channel.
3. Adopt provenance tags (P11) in fleet convention — one-line doc change.
4. Evaluate Redis-backed replay cache (P2) for the feed — needs yote-side work.
5. Track A2A (P17) — if it becomes the interop standard, build `A2AAgent`-equivalent for our agents.
