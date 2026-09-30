# Paper trail + build-vs-borrow verdict

Research for the chat-native agent design (2026-09-21). Driven through the paper-search
skill: `PAPER-TASK` entries posted to `/home/toxic/.shingle/directives.md`, raced live
with `race_papers.py` (arXiv + alphaXiv legs, HFT-raced) on yote — 10 queries, ~60
candidates. What follows is what survived contact with the actual problem.

## Borrowed (in the design)

1. **Global Workspace Agents / "Theater of Mind" (arXiv 2604.08206, 2026-04)** —
   central broadcast hub + heterogeneous swarm; coordination as "an active, event-driven
   discrete dynamical system". *Borrowed:* the fleet channel as the broadcast hub; agents
   as functionally-constrained specialists. This is the architectural spine of §2.
2. **"The Log is the Agent" (arXiv 2605.21997, 2026-05)** — append-only event log as
   source of truth; "No component instructs another; coordination happens entirely
   through the shared graph"; deterministic replay from the log. *Borrowed:* treat the
   seq log as the event log; per-agent cursors as projections. Our log already exists —
   we lean into it instead of building a new bus.
3. **"Efficient Intent-Based Filtering for Multi-Party Conversations" (arXiv 2503.17336,
   2025-03)** — distill the LLM into a cheap intent filter; never run full inference per
   snippet. *Borrowed:* the tier-0/tier-1/tier-2 attention cascade. Tier-1 ships as
   stdlib Jaccard; the distilled classifier is the documented upgrade path.
4. **"Autonomous Event-Driven Multi-Agent Orchestration" (arXiv 2606.20058, 2026-06)** —
   Task Manager for continuous operation: priority inference, related-event merging,
   preemption; headline result: *scale, not task complexity, dominates orchestration*.
   *Borrowed:* the vocabulary for the next iteration (event merging when the channel
   floods; preemption hooks). Not in v1 of the shim — noted as the scaling story.
5. **GCAgent (arXiv 2603.05240, 2026-03)** — dialogue-manager module deciding agent
   participation in group chat. *Borrowed:* participation-as-a-decision, separate from
   message delivery.
6. **"Who Speaks Next?" (arXiv 2412.04937, 2025-02)** — turn-taking norms, adjacency
   pairs in multi-party AI discussion. *Borrowed:* reply-vs-silence norms in `_classify`.
7. **AutoGen (arXiv 2308.08155)** — conversable agents, group-chat speaker selection.
   *Borrowed:* the mention/addressing convention as the primary wake signal.
8. **"Next-Generation Event-Driven Architectures" (arXiv 2510.04404, 2025-10)** —
   benchmarks 12 messaging systems incl. NATS JetStream across standardized workloads.
   *Borrowed as evidence:* keeps the NATS-substrate lane (Taps) as the right long-term
   bus; the shim's subscribe path is transport-agnostic by construction.
9. **ChainClaw (arXiv 2608.05790, 2026-08)** — layered agent framework with an explicit
   *event-driven orchestration layer* doing event ingestion. *Borrowed:* confirmation
   that the ingestion layer (our subscriber thread) belongs as a separate layer from
   the work loop.
10. **SolaceLabs/solace-agent-mesh** (GitHub, ★4.9k — code, not paper) — event mesh as
    the agent bus, A2A-over-broker, orchestrator agent. **Note: upstream deprecated the
    Python version** (README: "no longer under active development"). *Borrowed:*
    architecture pattern only (broker as the agent bus → our NATS direction). Not
    adopted — deprecated and broker-mismatched.

## Rejected (and why)

- **Sheaf-ADMM multi-agent coordination (2605.31005)** — differentiable optimization
  theory; nothing to do with chat infrastructure.
- **AlphaAgents / equity portfolio (2508.11152), AI-office survey, "Delegating or Doing"
  HCI study** — domain one-offs; no transport insight.
- **Holos (2604.02334)** — web-scale LaMAS vision; too abstract, no buildable mechanism.
- **Meta-ROS (2601.21011)** — robotics middleware; wrong domain.
- **NATS-specific agent repos** (`nats-agent-chat`, `agentorchestrators`, … — GitHub
  code search): all 0–1 stars, toys. Pattern curiosity only; nothing adoptable.
- **A2A/ACP/ANP interop survey (2505.02279)** — noted for later; no running code on our
  estate, and our transport is real today. Revisit when the NATS lane needs federation.

## OpenFang evaluation — straight verdict

**What it actually is** (read the source, not the brochure): a Rust agent kernel
(`openfang-kernel`, tokio async — genuinely event-driven internally, no poll loops
found), 40 chat-channel adapters (`openfang-channels`: discord, telegram, slack,
matrix, …) converting platform messages into `ChannelMessage` events, a
`BridgeManager` + `AgentRouter` (with `DmPolicy`/`GroupPolicy`) dispatching to agents,
triggers (event + cron), serving dashboard + `/v1` + `/api` on `:25196`.

**Against the goal** (agents living in *our* fleet channel — read, respond, take tasks,
no polling):

1. **No squawk adapter exists.** OpenFang agents cannot join the fleet channel today.
   Its 40 adapters cover everyone else's chat. This is an *inherent* gap for our goal,
   not a config issue.
2. **Trigger dispatch had a real kernel bug** (memory 2026-09-20: `spawn_agent`
   increments matching trigger fire counts but *drops dispatch results*). Event-driven
   in name; lossy in practice until fixed.
3. **The "needless torture" Chris felt is mostly our side, not OpenFang's:**
   revoked `ANTHROPIC_API_KEY` → assistant 500s; `HOME=/tmp/rig-home` vs `/home/toxic`
   split-brain; Groq embedding 401s (Groq has no embedding endpoint); stale model
   routes. The 2026-09-21 audit fixed the config layer. None of this is inherent to
   the kernel architecture.

**Cheapest bridge if we ever want it:** the generic `webhook.rs` adapter (HMAC-signed
HTTP in/out) or a new `squawk.rs` `ChannelAdapter` — the trait + `BridgeManager` make
this a bounded, well-shaped task. Not this lane.

**Verdict: OpenFang STAYS** as the agent runtime/kernel (it is event-driven where it
counts; the pain was keys and config). **It does NOT solve chat-native fleet
participation** — keep it out of this lane. The squawk-side shim is still required,
and it works for *any* agent process, OpenFang-hosted or not.

## Build-vs-borrow verdict

- **Adopt as-is:** nothing. No drop-in exists for token-authed long-poll + seq cursors.
- **Adapt (patterns):** Solace's event-mesh-as-agent-bus → NATS lane (Taps); OpenFang's
  `ChannelAdapter`/`BridgeManager` shape if a squawk adapter is ever written; GCAgent's
  dialogue-manager participation decision; ActiveGraph's log-as-truth (already ours).
- **Build:** `@fleet/chat-native` (~300 lines, zero-dependency Bun/TypeScript module at
  `projects/range/ranch/squawk/chat-native/`) — the one import. Small because the server
  already did the hard part (inotify-parked long-poll). Python ports of borrowed code
  (e.g. Solace's agent mesh) are reference only — everything we ship is Bun/TS.
- **Paper-search skill note:** the skill worked as designed (PAPER-TASK → raced legs).
  Two gaps found while driving it: (a) `bin/paper-search` wrapper named in SKILL.md
  doesn't exist in `bin/` — only `race_papers.py` (worked fine directly); (b) no
  deep-fetch flag — arXiv abstract pulls were hand-rolled. Worth adding
  `--abstracts` to the racer; not blocking.
