# Portainer Replacement — Ranked Shortlist (agentic-first control plane)

**Researcher:** Ripple (Ember's crew) — 2026-09-30
**Bar:** "agentic completions mcp we use with agent openfang" — candidates must be drivable
by OpenFang agents via MCP + completions. NOT another click-ops dashboard.
**Context:** Portainer audit found no live instance — a ghost (dead webhook 6+ months, stale
docs). The replacement doesn't migrate stacks; it replaces dashboard-driven container
management with agent-driven infrastructure.
**Estate:** yote (16c/62GB, Arch, docker) runs dagger-engine v0.21.9. OpenFang :25196
(`/v1/chat/completions`). MCP gateway :25127 (shep).

## Method

- `scripts/pattern-borrow.ts` × 4 pattern sets (weights tuned to recency+stars:
  `newest=0.35,stars=0.3,nRepos=0.15,forks=0.1,testFrac=0.1`), raw outputs in
  `docs/audits/pattern-borrow-*-20260930.txt`.
- paper-search (`paper-poller/bin/race_papers.py`, arXiv+alphaXiv+HF+OpenAlex legs):
  3 queries × 10 papers — summary below.
- Web recon + `gh` repo verification (stars + pushed_at pulled live 2026-09-30).

**Pattern-level signals (GitHub-wide):** "agentic devops" 19,634★/8 repos (richest space,
mostly awesome-lists/workshops — signal, not candidates); "portainer alternative"
15,810★/8 repos (Coolify/Dokploy/Dockge/Komodo cluster); "docker mcp tools" 231★/8 repos
(nascent but real); "dagger mcp" 2,990★/7 repos (thin — community experiments only).

**2026 landscape note:** Portainer 3.0 dropped the Community Edition (2.45 CE is LTS-only;
3.x free tier is Kubernetes-first, Docker second-class). The Docker-first world has moved to
Coolify / Dokploy / Dockge / Komodo / Arcane. Docker Inc. itself now ships an official MCP
registry (`docker/mcp-registry`, hub.docker.com/mcp), `docker/mcp-gateway` (1,589★), and
catalog servers (`mcp/docker` ops, `mcp/github`, …).

## How an OpenFang agent drives a deploy (the estate pattern)

1. The candidate's MCP server is registered in the MCP gateway (:25127, shep
   `mcp_config.json`) — stdio wrapped or Streamable HTTP.
2. OpenFang agents (:25196 `/v1/chat/completions`) get the tools via completions
   `tool_calls`; the agent reasons, calls tools, reads results, iterates.
3. Destructive tools gated per-server (read-only / no-destructive modes where offered).

---

## Ranked candidates

### 1. Dokploy + `@dokploy/mcp` / `danbenba/dokploy-mcp`
- **Repo:** [Dokploy/dokploy](https://github.com/Dokploy/dokploy) — 37,586★, pushed 2026-09-29.
  MCP: [danbenba/dokploy-mcp](https://github.com/danbenba/dokploy-mcp) (1★, 2026-09-02,
  full-write, 5 playbooks); official npm `@dokploy/mcp` (stdio).
- **What:** Self-hosted PaaS (Apache-2.0): git-push deploys, compose stacks, databases
  (postgres/mysql/mongo/redis), Traefik + Let's Encrypt, backups, multi-server.
- **MCP surface:** OFFICIAL (`@dokploy/mcp`) + best-in-class community
  (`danbenba/dokploy-mcp`: projects/apps/compose/databases/domains/deployments/docker
  containers, `api_find` over all 554 endpoints, `dokploy_api` escape hatch, secret-redacting
  middleware in forks). Dokploy v0.29 also ships an **AI router** (`ai-*` MCP tools:
  `ai-analyzeLogs`, `ai-suggest` — LLM log triage wired server-side).
- **Agent/completions API:** REST API (API key) under everything; MCP is the agent-native
  layer on top.
- **OpenFang deploy flow:** register `@dokploy/mcp` in :25127 → agent calls
  `application-create` (git source + env) → `application-deploy` → `deployment-watch` /
  `application-one` for status → `ai-analyzeLogs` on failure. No dashboard touched.
- **Fit: HIGHEST.** The only candidate with official MCP + full-write community MCP +
  server-side AI hooks, on a PaaS that already does the whole deploy (build → domain →
  SSL). This is the "agent runs the PaaS" pick.

### 2. L337-org/docker-mcp (`docker-mcp-server`)
- **Repo:** [L337-org/docker-mcp](https://github.com/l337-org/docker-mcp) — 8★, pushed
  2026-09-28 (2 days ago). Young; featured on glama.ai / mcp-find.
- **What:** Full-surface MCP server for the Docker daemon: containers, images, networks,
  volumes, swarm services, secrets, configs, nodes, plugins. PyPI `docker-mcp-server`.
- **MCP surface:** NATIVE — 150+ typed tools, each marked read-only/destructive;
  read-only / no-destructive server modes; per-daemon read-only flags; multi-daemon
  (local socket + remote over TCP/TLS/SSH in one session); logs/stats as MCP resources;
  in-session Docker SDK reference resource ("documentation built for the agent");
  bounded output with `truncated` flags; lazy-tool-loading friendly.
- **Agent/completions API:** MCP only (stdio via `uvx`, containerized, or `.mcpb`).
- **OpenFang deploy flow:** register in :25127 (containerized, socket mounted read-write
  or scoped) → agent: `compose up` equivalent via container/image/network tools, or drive
  a compose file through create/start calls; `logs` resource for triage. Daemon-direct —
  the closest thing to "Portainer's job" as MCP tools.
- **Fit: HIGH.** The purest answer to "Portainer's *idea* as an agent API". Caveats:
  young (8★), Python ≥3.14 native requirement, no PaaS layer (no git deploys/SSL/DBs —
  pair with Dokploy/Coolify or compose files for that).

### 3. Coolify
- **Repo:** [coollabsio/coolify](https://github.com/coollabsio/coolify) — 62,420★, pushed
  2026-09-30 (today). The 800-lb gorilla of self-hosted PaaS.
- **What:** Self-hosted Heroku/Netlify alternative: git deploys, 280+ one-click services,
  databases, preview deployments, S3 backups, teams.
- **MCP surface:** NATIVE (built-in, v4.1+): instance-level MCP over HTTP, API-token auth,
  team-scoped — **currently read-only** (10 tools: list servers/apps, inspect, DB status…),
  writes planned. Community write-capable: [kof70/coolify-mcp-server](https://github.com/kof70/coolify-mcp-server)
  (29★, full API coverage), [lutzkind/coolify-mcp](https://github.com/lutzkind/coolify-mcp)
  (42 token-optimized tools, −85% tokens in v2), [clezcoding/awesome-coolify](https://github.com/clezcoding/awesome-coolify)
  (19 action-based tools: deploy/diagnose/CRUD, Zod-validated, secret-masking).
- **Agent/completions API:** Public REST API (documented) under all of it.
- **OpenFang deploy flow:** register `awesome-coolify-mcp` (or kof70) in :25127 →
  `application({action:"deploy", uuid})` → `deployment({action:"watch"})` →
  `diagnose({action:"scan"})` on failure. Native read-only MCP covers status queries.
- **Fit: HIGH.** Biggest ecosystem + official trajectory toward MCP. Docked one rank
  below Dokploy only because its *native* MCP is read-only today (writes depend on
  community servers).

### 4. ckreiling/mcp-server-docker
- **Repo:** [ckreiling/mcp-server-docker](https://github.com/ckreiling/mcp-server-docker) —
  746★, pushed 2026-08-07. The established community Docker MCP server.
- **What:** Docker daemon as MCP tools (the pre-L337 incumbent).
- **MCP surface:** NATIVE (stdio). narrower surface than L337; older, more battle-tested.
- **Agent/completions API:** MCP only.
- **OpenFang deploy flow:** same shape as #2 — register in :25127, drive containers/
  images/networks/volumes/compose via tools.
- **Fit: MEDIUM-HIGH.** Proven and starred; losing the freshness race to L337 (which has
  the better agent-UX design: typed destructive flags, resources, per-daemon scoping).
  Hyper-race #2 vs #4 head-to-head.

### 5. Dagger
- **Repo:** [dagger/dagger](https://github.com/dagger/dagger) — 16,310★, pushed 2026-09-30.
- **What:** Programmable CI/CD / automation engine: pipelines as code (Go/Python/TS),
  `dagger call`, Dagger Shell, GraphQL API. **Engine v0.21.9 already runs on yote.**
- **MCP surface:** COMMUNITY-ONLY, immature (`awdemos/dagger-mcp-server` 1★; pattern-borrow
  "dagger mcp" space = 2,990★/7 repos but all experiments).
- **Agent/completions API:** `dagger call` CLI + GraphQL API — already agent-scriptable
  today; an OpenFang agent can shell/API-drive pipelines without any MCP.
- **OpenFang deploy flow:** agent composes a Dagger pipeline (build → push → deploy to
  the estate's docker) and executes via `dagger call` through yote-conn exec, or via the
  engine's GraphQL API. Deterministic, replayable, cache-efficient.
- **Fit: MEDIUM-HIGH (different axis).** Not a control plane — it's the *pipeline*
  substrate. Best paired with #1/#2: Dagger builds, Dokploy/docker-mcp deploys. The
  hyper-race should test "agent writes a Dagger function that deploys via MCP tools".

### 6. ckanthony/openapi-mcp
- **Repo:** [ckanthony/openapi-mcp](https://github.com/ckanthony/openapi-mcp) — 197★,
  pushed 2026-03-21.
- **What:** Generic **OpenAPI → MCP proxy**: point it at any REST API, get MCP tools.
  Dockerized.
- **MCP surface:** NATIVE (it *is* the adapter).
- **Agent/completions API:** whatever the wrapped API offers.
- **OpenFang deploy flow:** wrap Komodo's / Portainer's / Dockge's REST API → instant MCP
  server in :25127. The force-multiplier that makes every API-first dashboard below
  agent-drivable without waiting for native MCP.
- **Fit: MEDIUM (enabler, not a plane).** Include in the estate regardless of which
  control plane wins — it backfills MCP for anything with a REST API. (Directly
  supported by the literature: "From REST to MCP: An Empirical Study of API Wrapping
  and Automated Server Generation", arXiv 2507.16044.)

### 7. Komodo
- **Repo:** [moghtech/komodo](https://github.com/moghtech/komodo) — 12,557★, pushed
  2026-09-21. Rust. (Not `mbround18/komodo` — that namespace 404s.)
- **What:** Build/deploy/monitor across many servers: Core (API+UI :9120) + Periphery
  agents (:8120) on each host, MongoDB state, compose stacks, image builds, procedures
  (multi-step automation), GitOps resource syncs, full audit trail.
- **MCP surface:** NONE native. But: documented REST + WebSocket API, first-class CLI,
  Rust/NPM client libs — the most API-complete of the Portainer successors.
- **Agent/completions API:** REST/WS API + CLI.
- **OpenFang deploy flow:** today: agent drives the REST API / CLI via completions
  tool_calls (or yote-conn exec). With #6: wrap the API in openapi-mcp → native-feeling
  MCP tools in :25127.
- **Fit: MEDIUM.** The honest "Portainer done right" (GitOps-native, agent-friendly
  architecture) but MCP is DIY. Loses to #1/#3 on the agentic bar as it stands.

### 8. kagent
- **Repo:** [kagent-dev/kagent](https://github.com/kagent-dev/kagent) — 3,892★, pushed
  2026-09-30. CNCF Sandbox, Apache-2.0, Solo.io.
- **What:** Kubernetes-native agentic AI framework: agents as CRDs (`Agent`,
  `ModelConfig`, `RemoteMCPServer`), native MCP + A2A (every A2A agent auto-exposed as
  MCP on `:8083/mcp`), bundled MCP tool servers (k8s, Istio, Helm, Argo, Prometheus,
  Grafana), OTel tracing, BYO model/framework, HITL, memory.
- **MCP surface:** NATIVE and deepest — but for Kubernetes objects, not Docker.
- **Agent/completions API:** CRDs via kubectl/GitOps; A2A; OpenAI-compatible endpoints.
- **OpenFang deploy flow:** N/A on this estate — no Kubernetes here. Would require
  standing up k3s/k8s on yote first.
- **Fit: LOW for this estate, HIGH as a pattern.** The reference architecture for
  "agentic control plane done right" (declarative agents + MCP federation + policy).
  Include as the north-star / the pick if the estate ever grows a k8s substrate.

## Also considered (not ranked)

- **Dockge** (louislam/dockge, 24,486★, pushed 2026-04-25 — quiet 5 months): best
  compose-file UX, but dashboard-first, no MCP, thin API. Fails the agentic bar.
- **Mooring** (daboss2003/mooring, 2★): "control plane, not a dashboard" rhetoric is
  right, but 2 stars and no MCP/API story yet. Watch, don't adopt.
- **Portainer itself** (2.45 CE LTS / 3.x): has a REST API; CE is feature-frozen and
  Docker is second-class in 3.x. Wrapping its API via #6 is possible but it's the
  past, not the future.
- **Docker official surface** (`docker/mcp-gateway` 1,589★, `docker/mcp-registry`,
  catalog `mcp/docker` ops server, `docker/hub-mcp`): vendor-sanctioned, signed
  images, container-isolated servers. Worth registering `mcp/docker` in :25127 as a
  complement; not a control plane by itself.
- **Yacht / CapRover / Arcane / doco-pilot**: dashboards or SaaS-control-planes;
  fail the self-hosted agentic bar.

## Recommendation to the hyper-race worker

Race these lanes, not just repos:
1. **PaaS-agent lane:** Dokploy (`@dokploy/mcp` + `danbenba/dokploy-mcp`) vs Coolify
   (`awesome-coolify-mcp`) — full deploy-via-MCP E2E on yote.
2. **Daemon-direct lane:** L337 `docker-mcp-server` vs `ckreiling/mcp-server-docker` —
   container lifecycle + compose + triage via MCP tools.
3. **Adapter lane:** `openapi-mcp` wrapping Komodo's API — measures how cheaply the
   API-first runners-up become agent-drivable.
4. **Pipeline lane:** Dagger function that deploys through the winning MCP lane —
   tests the composition story (Dagger builds, MCP deploys).

## Paper-search summary (10 lines)

1. "From REST to MCP" (arXiv 2507.16044, 2026-04): first empirical study of wrapping
   REST APIs as MCP servers — directly justifies the openapi-mcp adapter lane (#6).
2. "A survey of agent interoperability protocols: MCP, A2A…" (2505.02279, 2025-05):
   MCP/A2A/ACP compared — MCP is the tool-invocation standard, A2A the delegation one;
   kagent (#8) implements both natively.
3. "Building AI Agents for Autonomous Clouds" (arXiv 2407.12165, 2024): the high-impact
   agent use case is *operational resilience of services*, not codegen — the thesis
   behind replacing Portainer's dashboard with agents.
4. "Securing MCP" (2511.20920, 2025-11): MCP's dynamic tool invocation escapes existing
   AI-governance frameworks — read before exposing destructive infra tools; L337's
   read-only/destructive flags (#2) are the practical answer.
5. "Authorization Architectures for Tool-Using AI Agents" (2609.15906, 2026-09): the
   auth model for agents acting on humans' behalf is still underdeveloped — scope
   tokens per-team (Coolify does this) and gate destructive tools.
6. "EngiAI" (2605.19743, 2026-08): capability-based eval for tool-connected engineering
   agents — use its framing (workflow execution vs parameter selection) to score the
   hyper-race, not vibes.
7. "Intent Engine" (2608.20388, 2026-06): NL intent → orchestration SLOs is still
   unreliable when generated directly — agents need typed tools (the MCP lane), not
   raw YAML generation.
8. "A Review of Generative AI and DevOps Pipelines" (2025): GenAI+CI/CD/MLOps survey —
   confirms the industry direction: agents operating pipelines, which is Dagger's (#5)
   lane.
9. "Agentic Autoscaling through Worker-Pool Orchestration" (2609.14898, 2026-09):
   agents driving orchestration decisions (autoscaling) — precedent for agents as
   *controllers*, not just chat.
10. "Codified Context: Infrastructure for AI Agents in a Complex Codebase"
    (2602.20478, 2026-02): agents need purpose-built infrastructure context —
    L337's in-session SDK-reference resource (#2) is this idea applied to Docker.
