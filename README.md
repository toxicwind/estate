[![Last commit](https://img.shields.io/github/last-commit/toxicwind/estate?style=for-the-badge)](https://github.com/toxicwind/estate/commits/main)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)
[![Repo size](https://img.shields.io/github/repo-size/toxicwind/estate?style=for-the-badge)](https://github.com/toxicwind/estate)

<div align="center">

# 🏰 estate

**One human's entire compute estate — the control plane and the shipping lane for a swarm of boxes, 100+ supervised daemons, and a fleet of named agents that talk to each other.**

**_The deploy plane_: this repo is where the estate actually deploys. Every box, every model front door, every daemon is stood up, wired, and health-checked from here. "Deployed" means a running process uses it — not just a file on disk.** Local + cloud model routing, a Vickrey decision market, and multi-agent orchestration under `corral`/`delendai`. The estate is where `push → build → launch` ends.

```text
**Where the code lives: the pens.** The estate deploys *through* the fully-local
organization trees under `pens/` (symlinked here). See
[`toxicwind/pens`](https://github.com/toxicwind/pens) (pointer superproject),
[`toxicwind/olympus`](https://github.com/toxicwind/olympus) (Greek-coded
products), and [`toxicwind/ranch`](https://github.com/toxicwind/ranch) (project
monorepo, workshop); this estate root is the control plane that stands them
up.

push → forge/mbx (:25148 build dispatch, :25155 forge REAPI) → pitchfork (health:
pitchfork's own surface, unverified port)
→ LIVE on the estate (89+ supervised daemons)
```

</div>

## 🧭 What this is

**estate** is your personal infrastructure monorepo — the whole laboratory, not a demo of one. It answers one question: _what does it take for one human to run a serious AI operation across an interconnected swarm of machines?_

The answer, as committed here:

- **A model-routing layer** that treats local and cloud inference as one fabric. `herd` (:25100) fronts the on-box GGUFs through llama.cpp engines; anything it can't serve overflows to `hodos` (:25193), a Rust proxy that routes across cloud providers with key pools, 429 rotation, circuit breakers, and health/Elo scoring. A key-pool router (`keygate`), a merged provider gateway (`atlas`, auth+keys+routing), and EAP tool-retrieval (`theta`) sit in front.
- **A fleet, not a script.** [squawk](https://github.com/toxicwind/ranch/tree/main/squawk) is a real multi-agent chat plane — signed, sequenced message files over a websocket (:25147) and feed (:25135). Named agents with real personas join it, argue, bid on work, and narrate what they're doing. The fleet channel is the live operations log. Root paths 302-redirect to their real endpoints.
- **A decision engine.** The oracle (:25151) runs a Vickrey prediction-market work loop: biddable tasks, evidence-backed yes/no verdicts, a tamper-evident ledger. When a call needs the user's authority and the user isn't around, the oracle's verdict _is_ the approval.
- **Supervision as a first-class citizen.** 103 top-level daemons live in `pitchfork.toml`, each health-checked, each restartable through its owning project's manifest. "Works until restart" is not a fix here — every fix lands in real committed files and survives a full restart.
- **Git-backed autonomy.** `corral` + `delendai` give every agent work-refs, a proposal guardian, and a `shared-checkout-merge` guard — a reference-transaction guard blocks direct commits to `main`, forcing speculative work onto `heads/wip/<agent>/…` refs that a merge queue reconciles.

**A note on dates:** this README is a _snapshot_ audited against source on **2026-10-22**. The estate changes weekly. Every claim below that can be verified against `config/ports.env`, `pitchfork.toml`, or `bin/` is marked; anything else is flagged "unverified — needs check."

### Built with

Go · Rust · Python · TypeScript (Bun) · llama.cpp · pitchfork · corral/delendai · NATS · Qdrant · Oracle (Vickrey market) — and a standing rule that the fastest correct path wins.

## 🚀 Quick-start — how this estate actually boots

This is personal infrastructure, not a library — you don't `pip install` it, you _stand it up_ (or tour it). The boot sequence on a fresh host:

```bash
# 1. Runtime toolchains via mise (the environment manager)
mise install        # reads mise.toml — bun, node, rust, python, go, pitchfork, delendai

# 2. Clone this repo + the project monorepo it deploys
git clone https://github.com/toxicwind/estate.git /home/toxic/estate
git clone https://github.com/toxicwind/ranch.git /home/toxic/estate/ranch   # the workshop

# 3. Enter the DelendAI work environment (work-ref + shared-checkout-merge guard)
delendai work enter --workspace /home/toxic/estate

# 4. Stand up the supervised daemons (health-checks, restart paths)
pitchfork register          # load the composed daemon inventory
pitchfork start all         # bring the fleet up
```

The **30-second tour** (curl probes against the live box, reachable over the tailnet):

```bash
curl -s http://127.0.0.1:25100/v1/models | head -c 300   # what's awake on herd
curl -s http://127.0.0.1:25193/health                     # hodos cloud router (auth-gated)
curl -s http://127.0.0.1:25135/health                     # squawk fleet feed
curl -s http://127.0.0.1:25151/health                     # oracle decision market
curl -s http://127.0.0.1:25127/                           # thresher MCP gateway (302)
```

**Go deeper:** [`docs/`](docs/) holds the architecture contracts — start with [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/REPO_TOPOLOGY.md`](docs/REPO_TOPOLOGY.md), and [`docs/estate-map.md`](docs/estate-map.md). `ranch/` (sibling repo) holds the projects.

## 🐝 The fleet & the 25xxx ports

The estate's numbered services live in the **25xxx range**, pinned in the **port SSOT [`config/ports.env`](config/ports.env)**. That file is the contract — never hardcode a port in tool code; read it from `ports.env`. The old README's "~18 ports" table was wildly incomplete; this table is generated from the SSOT.

### The pinned 25xxx port set (source: `config/ports.env`, 2026-10-22)

```
25001 25099 · 25100 25101 25102 25103 25104 25105 25106 25107 25108 25109 25110
25111 25112 25113 25114 25115 25116 25117 25118 25120 25121 25122 25123 25124
25125 25126 25127 25128 25129 25130 25131 25132 25133 25134 25135 25136 25137
25138 25139 25140 25141 25142 25143 25144 25145 25146 25147 25148 25149 25150
25151 25152 25153 25154 25155 25156 25157 25158 25159 25160 25161 25162 25163
25170 25178 25180 25181 25189 25190 25191 25192 25193 25194 25195 25196 25197
25198 25199 25200 25201 25202 25203 25204 25205 25206 25207 25208 25209 25210
25211 25212 25213 25214 25215 25216 25217 25218 25219 25220 25221 25222 25223
25224 25225 25226 25229 25231 25280
```

> **110 unique 25xxx slot-values** are pinned. `25001–25099` is the **herd-dynamic pool** (llama.cpp + alias shims, allocated at runtime). `25170`, `25178`, `25180` are reserved/reserved-ish slots. The remaining tail (`25280+`) is the **Smithers gateway** and the DelendAI dashboards. Platform ports outside 25xxx (also SSOT-pinned): `20128` vansrouter, `4747` keeper-floaty, `5900`/`6080` agent-display/viewer, `34567` files.

### Known-important ports (annotated from config/ports.env)

| Port            | SSOT name                   | Owner / role                                                         | Role changed since old README?                                                                               |
| --------------- | --------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `25100`         | `HERD_PORT`                 | **herd** — local model front door (`/v1/models`)                     | —                                                                                                            |
| `25101`         | `MODEL_GUARD_PORT`          | model-guard inference safety layer                                   | —                                                                                                            |
| `25102`         | `YOTE_RELAY_PORT`           | yote messaging gateway (Telegram / Overlord)                         | moved-off-25104 alias legacy                                                                                 |
| `25104`         | `ESTATE_ROUTER_PORT`        | **RETIRED** estate-router-ts — no listener, no daemon                | —                                                                                                            |
| `25105`         | `PROMETHEUS_PORT`           | Prometheus metrics                                                   | —                                                                                                            |
| `25106`         | `GIBBER_MCP_PORT`           | gibber-mcp (live peer, adopted orphan)                               | renamed to :25226 hf-downloader separated                                                                    |
| `25107`         | `NULL_G_PROXY_PORT`         | null-g-proxy edge proxy                                              | —                                                                                                            |
| `25109`         | `KEYPOOL_PORT`              | provider key pool sidecar                                            | —                                                                                                            |
| `25110`         | `GRAFANA_PORT`              | Grafana                                                              | —                                                                                                            |
| `25111`         | `TAU_CHUTE_PORT`            | tau chute agent runtime                                              | —                                                                                                            |
| `25117`         | `HINDSIGHT_API_PORT`        | **hindsight** API                                                    | —                                                                                                            |
| `25118`         | `HINDSIGHT_CP_PORT`         | hindsight control plane                                              | —                                                                                                            |
| `25120`         | `ESTATE_CHAT_PORT`          | estate-chat (tailnet+loopback)                                       | —                                                                                                            |
| `25121`         | `FEEDLOT_PORT`              | feedlot (outer MCP hop edge)                                         | —                                                                                                            |
| `25126`         | `KIMI_CODE_PORT`            | kimi-code                                                            | —                                                                                                            |
| `25127`         | `MCPPROXY_GO_PORT`          | **thresher** MCP gateway (tool federation, :25127/mcp)              | —                                                                                                            |
| `25133`/`25134` | `QDRANT_*_PORT`             | Qdrant HTTP + gRPC                                                   | —                                                                                                            |
| `25135`         | `SQUAWK_FEED_PORT`          | **squawk fleet feed** (302 → /squawk-feed/seq)                       | —                                                                                                            |
| `25136`         | `FLEET_UI_PORT`             | fleet web UI                                                         | —                                                                                                            |
| `25137`         | `BEDROCK_UI_PORT`           | bedrock evidence-locker web UI                                       | —                                                                                                            |
| `25143`         | `YOTE_CORE_PORT`            | yote autonomous sigil execution loop                                 | —                                                                                                            |
| `25146`         | `WHATSAPP_MCP_PORT`         | whatsapp-mcp                                                         | —                                                                                                            |
| `25147`         | `SQUAWK_WS_PORT`            | **squawk websocket** — NOW LIVE (old README said down)               | **changed role** (was DOWN, now up, 302 → /ping)                                                             |
| `25148`         | `MBX_CACHE_PORT`            | **mbx / mise remote-task cache & build dispatch**                    | **changed role** (old README called it "flicker build daemon"; flicker is retired, mbx/mise is the dispatch) |
| `25149`/`25150` | `PAPER_POLLER_*_PORT`       | paper poller + watchdog                                              | —                                                                                                            |
| `25151`         | `ORACLE_CORE_PORT`          | **oracle** Vickrey decision market                                   | —                                                                                                            |
| `25152`         | `TOOLCALL_PORT`             | toolcall-llm (qwen3.5-9b tool)                                       | —                                                                                                            |
| `25154`         | `BROWSER_KEEPER_CDP_PORT`   | skopos/keeper Chrome DevTools (:9223 moved onto 25xxx)               | —                                                                                                            |
| `25155`         | `NATIVELINK_FRONTEND_PORT`  | **forge / nativelink RE frontend** — NOW LIVE (old README said down) | **changed role** (was DOWN 2026-10-15, now live; forge REAPI)                                                |
| `25156`         | `DELENDAI_CONTROL_PORT`     | DelendAI control-plane SPA Vite                                      | new                                                                                                          |
| `25157`         | `NATIVELINK_WORKER_PORT`    | nativelink worker                                                    | —                                                                                                            |
| `25158`         | `FLEET_FEED_PORT`           | fleet-feed.ts                                                        | new                                                                                                          |
| `25159`         | `KAPPA_ACP_PORT`            | kappa ACP server                                                     | —                                                                                                            |
| `25160`         | `FORENSICS_SRV_PORT`        | forensics server                                                     | —                                                                                                            |
| `25162`         | `DELENDAI_CONTROL_API_PORT` | DelendAI control-plane API                                           | new                                                                                                          |
| `25163`         | `NIM_KIMI_SIDECAR_PORT`     | NIM/kimi sidecar                                                     | —                                                                                                            |
| `25178`         | `PHONE_SENTINEL_PORT`       | phone-sentinel (was DOWN in old README)                              | —                                                                                                            |
| `25181`         | `BENCH_RADAR_PORT`          | bench-radar nightly regression                                       | —                                                                                                            |
| `25189`–`25191` | `NIM_*`                     | NIM queue / reasoning router / validation                            | —                                                                                                            |
| `25193`         | `HODOS_PORT`                | **hodos** cloud provider router                                      | —                                                                                                            |
| `25194`         | `RALPH_DASH_PORT`           | ralph-dashboard backend                                              | —                                                                                                            |
| `25195`         | `CODEBASE_MEMORY_PORT`      | codebase-memory-mcp graph UI                                         | —                                                                                                            |
| `25196`         | `OPENFANG_KERNEL_PORT`      | openfang kernel                                                      | —                                                                                                            |
| `25197`         | `DELENDAI_WEB_PORT`         | **DelendAI web app** (Astro; alias boundless)                        | new                                                                                                          |
| `25198`         | `AWR_MCP_PORT`              | awrawr-mcp connector                                                 | —                                                                                                            |
| `25200`         | `CUTTINGGATE_PORT`          | cuttinggate guard plane (in front of herd/hodos)                     | —                                                                                                            |
| `25201`         | `RUST_WEB_PORT`             | rust web / estate_web                                                | —                                                                                                            |
| `25202`         | `GEMINI_MCP_PORT`           | gemini-mcp server                                                    | new (see note)                                                                                               |
| `25203`         | `REDIS_PORT`                | valkey/redis                                                         | —                                                                                                            |
| `25204`         | `EXEC_WS_PORT`              | awrawr-ws-exec                                                       | —                                                                                                            |
| `25211`         | `KITTY_MCP_PORT`            | kitty-mcp                                                            | new                                                                                                          |
| `25212`         | `COCKPIT_PORT`              | cockpit web console                                                  | —                                                                                                            |
| `25213`         | `ESTATE_EXPORTER_PORT`      | estate-exporter prometheus collector                                 | new                                                                                                          |
| `25215`         | `STREAM_BROKER_PORT`        | estate stream broker                                                 | —                                                                                                            |
| `25217`         | `DOORBELL_OAUTH_EDGE_PORT`  | **doorbell OAuth compat edge** (public funnel terminator)            | new                                                                                                          |
| `25218`         | `RANCH_UI_PORT`             | **ranch-ui** — consolidated Ranch/DelendAI dashboard                 | new                                                                                                          |
| `25219`         | `WINDMILL_PORT`             | windmill GPU/PCIe telemetry                                          | —                                                                                                            |
| `25220`–`25224` | `RUSTDESK_*`                | rustdesk hbbs/hbbr (NAT, relay, WS)                                  | —                                                                                                            |
| `25226`         | `HF_DOWNLOADER_PORT`        | hf-downloader (was 25106, moved)                                     | moved                                                                                                        |
| `25229`         | `SQUAWK_HISTORY_PORT`       | squawk_history (orphan re-registered)                                | new                                                                                                          |
| `25231`         | `NODE_EXPORTER_PORT`        | node_exporter (was :9100)                                            | moved                                                                                                        |
| `25280`         | `SMITHERS_GATEWAY_PORT`     | **Smithers gateway** (estate control plane, 302)                     | new                                                                                                          |

> **Port-role notes.** Three roles changed since the old README: **:25147 squawk-ws** (was DOWN, now live), **:25155 nativelink** (was DOWN, now live as forge REAPI), and **:25148** (old "flicker" is retired; mbx/mise task-cache is the build dispatch). The thresher MCP gateway did **not** move off :25127; it binds loopback + tailnet. The port SSOT (`config/ports.env`) is read-only source here — never renumber a pinned service without editing the SSOT first.

## ⚙️ Orchestration — corral/delendai, work-refs, and the shared-checkout guard

Multi-agent orchestration is **corral** (deterministic orchestration, `estate/ranch/corral`) merged with **delendai** (`shared-checkout-merge` development profile, proposal guardian, speculative merge queue). "super-ralph" is retired.

- **Work-refs, not blind commits.** Under `shared-checkout-merge`, direct commits to `main` are blocked by a reference-transaction guard. Agents persist work to `heads/wip/<agent>/implement/<proposal>-<slice>-g<gen>/<topic>` and a merge queue reconciles them forward-only.
- **Proposal guardian.** No work proceeds without a proposal id, slice id, topic, and generation — the delendai grammar enforces a collision-free namespace.
- **The feedback loop.** The **forever-loop** C2 rig (below) reads the oracle market + board on a 3-minute tick, applies awarded work via `delend-experimental`/`delend-iterate`, and nudges any flailing subagent.

## 🧰 The zero-primitives — `bin/delend-*`

A family of first-class, zero-friction operational helpers in `bin/` (all verified present 2026-10-22):

| Tool                                             | One-liner                                                                                                                                                             |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `delend-quick`                                   | Universal work-ref checkpoint & push helper — discovers changed paths, normalizes the delendai work-ref namespace, runs `delendai work checkpoint`, pushes to origin. |
| `delend-gh`                                      | **Global-GitHub primitive** — operate on _any_ org/repo (temp clone → git op → cleanup), not just toxicwind.                                                          |
| `delend-branch-audit-for-main`                   | Estate-wide branch audit of a repo vs its remote default branch.                                                                                                      |
| `delend-code-race`                               | Race redundant implementation approaches (pattern-borrow + code-race), first valid wins.                                                                              |
| `delend-experimental`                            | Spawn an experimental agent that auto-heals and iterates itself via the code-finder — conjectures 3+ divergent implementations.                                       |
| `delend-iterate`                                 | Iterate a solution loop under the proposal guardian.                                                                                                                  |
| `delend-oracle`                                  | Drive the oracle market (status / post-find-more / capture award).                                                                                                    |
| `delend-route`                                   | Route a task through a provider/model lane.                                                                                                                           |
| `delend-stash-optimize` / `delend-working-dirty` | Workspace hygiene helpers.                                                                                                                                            |
| `delend-model-race`                              | Race model lanes for a workload.                                                                                                                                      |
| `delend-forge-audit`                             | Audit forge build-cache health.                                                                                                                                       |

## 🔁 The forever-loop C2 rig (squawk)

The estate's heartbeat orchestrator: **[`ranch/estate-brain/agents/forever-loop/`](ranch/estate-brain/agents/forever-loop/)**. It's a **C2 forever-goal coordinator** — supervised by pitchfork as `estate/forever-loop`, scheduled every **3 minutes** (`agent.toml`, `schedule = "interval:3m"`, Nemotron-3-Super via hodos :25193). Each tick (`run-loop.ts`):

1. Scans the **oracle market** + hindsight + the estate board for awarded/surfaced work.
2. Applies any market-awarded task via `delend-experimental` / `delend-iterate`.
3. Advances the next un-done estate task; does a **worker slice** (commit/push, QA loops).
4. Inspects running subagents' mid-work logs and **nudges any flailing** (stuck / error-looping / no output) — never skips a round.
5. Posts full **C2 status to the squawk fleet channel** as identity `forever-loop`.

It holds the 4s race budget and uses `delend-code-race` on breach. The rig **never goes idle** — it is the "find more to do" engine that keeps the whole autonomous estate busy.

## 🌍 The Global-GitHub primitive

The estate operates on **arbitrary upstream repos**, not just `toxicwind/*`. `bin/delend-gh <org/repo|url> [audit-main|raw <path>|<git-args>] [--keep]` resolves any GitHub/GitLab/Codeberg/self-hosted repo into a temp clone, runs a git operation (default: a branch audit vs the remote default branch), and cleans up. `bin/delend-branch-audit-for-main --repo <path|url>` is the estate-wide branch audit on any repo. Global-by-construction: never assume a repo lives under a specific org — always resolve from the provided org/URL. This is the basis for foreign-pattern borrow, upstream tracking, and cross-org recon.

## 🧠 Skills — grasp-hub, one registry for every agent

All estate skills (kappa **and** tau) load from **one registry**: [`grasp-hub/`](grasp-hub/) — `grasp-hub/skills/<cluster>/<name>/SKILL.md`, exposed via Graph-Structured Agent Planning (GraSP) clusters with a classifier and an MCP server (`grasp-hub/mcp/server.ts`).

- **kappa** → `skills.paths` → `grasp-hub/skills` (global, dots-managed) and the project `.agents/skills/` symlink. Verify with `kappa debug skill`.
- **tau** → `config/tau/skills` → `grasp-hub/skills` symlink.
- Clusters: `00_inbox`, `01_orchestration`, `02_research_intel`, `03_systems_runtime`, `04_code_intelligence`, `05_data_hardware`, `06_knowledge_authoring`, plus `archive`.

**Agent-paradigm-audit** is a first-class skill here: [`grasp-hub/skills/06_knowledge_authoring/agent-paradigm-audit/SKILL.md`](grasp-hub/skills/06_knowledge_authoring/agent-paradigm-audit/SKILL.md). It runs a neutral, evidence-backed audit of the 2026 "openclaw-era" agent paradigms (deterministic / infra-aware / self-grading / settlement) grounded in the real October-2026 orchestration literature (Jasper OS, INFRAMIND, WorkflowOps, OrchRM, the MAS orchestration survey) **and** in concrete estate reality (oracle-market, corral/delendai, forever-loop+squawk C2, hodos/EAP/theta routing, delend-experimental self-healing). Output is a scored Oracle-Decision-Table, not a vendor cheerleading sheet — and it is itself the estate's documented evidence for how it chooses orchestration.

Add or edit a skill once in grasp-hub and both consumers pick it up — no per-agent copies. Keep the `name == directory` contract and parseable frontmatter. Register a new skill by dropping it in `skills/<name>/` (SKILL.md frontmatter required), symlinking into `grasp-hub/skills/<cluster>/<name>`, then proving pickup (`node bin/grasp-hub.js list | grep <name>` and `validate` must be green).

## 🗺️ Operations & the live box

**pitchfork** is the daemon supervisor. The composed `pitchfork.toml` (103 top-level `[daemons.*]`) is generated from per-project manifests (`pitchfork.d/` — 109 daemon files). **Edit the project source, never the composed file.** The hard-won rule, learned from a 12-hour stale-definition incident:

> pitchfork does **not** hot-reload. After any daemon edit, re-register and restart through the owning project's path, then verify `/health`. A daemon can report `errored` in pitchfork while its orphaned predecessor still answers 200 — trust the re-registration, not the dashboard.

The 25xxx fleet is bound as a **one-supervisor-per-service** doctrine: lane-A estate services are native pitchfork+mise daemons; lane-B ops/website deployables are docker-compose in their own repo. **Never remove or disable a peer/daemon/model without an explicit order** — the box is additive-only.

## 🐾 The pack — named agents

The fleet is not a metaphor. Named agents — each with a species, a personality, and a lane — join squawk, post their own hellos, bid on oracle tasks, argue the point, and narrate their work live. Ember coordinates; the **forever-loop** rig keeps the pack from going idle. The roster changes constantly — the fleet channel (squawk, :25135) is the source of truth.

## 🐘 Repo topology — four repos, one estate

| Repo                                                                                                              | Visibility | What it is                                                                                                                                                                                                                                                                                                                                                              |
| ----------------------------------------------------------------------------------------------------------------- | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`toxicwind/estate`](https://github.com/toxicwind/estate)                                                         | PUBLIC     | This repo — the control plane / deploy plane.                                                                                                                                                                                                                                                                                                                           |
| [`toxicwind/pens`](https://github.com/toxicwind/pens)                                                              | PUBLIC     | Pointer superproject (`*` in `.gitignore`) organizing `olympus/`, `ranch/`, and `archive/` with generators in `toolkit/`.                                                                                                                                                                                                                                                |
| [`toxicwind/olympus`](https://github.com/toxicwind/olympus)                                                       | PUBLIC     | The Greek pantheon pen — registry of Greek-coded products (`tau`, `kappa`, `skopos`, `kilo`, `muse`, `keryx`, `hodos`, `kairos`, `kryptos`, `agele`, `pinax`, `agon`, `antilogos`, `pylae`, `propylon`, `opsis`, `didymos`, `chronos-forge`, `arroyo`). `pens/toolkit/` and `ranch/toolkit/` hold the Bun README/manifest generators. |
| [`toxicwind/ranch`](https://github.com/toxicwind/ranch)                                                            | PUBLIC     | The workshop — 222-component peer workspace pen (`.meta.yaml` + `toolkit/`).                                                                                                                                                                                                                                                                                              |
| [`toxicwind/agele`](https://github.com/toxicwind/agele)                                                            | PUBLIC     | The herd — local LLM inference front door (`llama.cpp` :25100; renamed from `herd`).                                                                                                                                                                                                                                                                                    |
| (former `hatch`, now `kite`)                                                                                      | —          | The control-cell repo split out of this tree (live checkout `/home/toxic/kite/kite`); dodge name `hatch`, real identity `kite`. No longer inside the estate tree.                                                                                                                                                                                                       |

_(The old README carried verified `main` SHAs here; those SHAs are mutable and were dated 2026-10-15. They've been dropped in favor of `git ls-remote origin` for current truth.)_

## 🔧 Debugging

- **Port not answering?** Check it's pinned in `config/ports.env` (the SSOT) — if it isn't, it's an unowned listener, not a live service. Then `ss -ltnp | grep :PORT`.
- **Daemon reports errored?** Verify the _re-registered_ definition, not the dashboard (orphaned predecessor can still answer 200).
- **Squawk feed / ws giving 302?** That's expected — root paths redirect to their real endpoints (`/squawk-feed/seq`, `/ping`).
- **Thresher MCP flaky?** It federates FFS, BM25, memory, browser CDP, GitHub, debug, ast-grep behind `http://127.0.0.1:25127/mcp` — start there for tool discovery and health.
- **Build cache?** `mbx`/mise remote task-cache is :25148; forge REAPI is :25155; NativeLink worker :25157.

## 🤝 Contributing

This is personal infrastructure with a public window — the interesting parts accept company. Read [`CONTRIBUTING.md`](CONTRIBUTING.md), then open an issue before a PR so the direction gets a yes first. Standing rules: maximal autonomous execution, every fix in real committed files in the owning repo, nothing that only works until restart, secrets never committed, and the fleet narrates everything. Play nice under `shared-checkout-merge` — checkpoint to a work-ref, don't fight the guard.

## 📄 License & Security

Distributed under the **MIT License** — see [LICENSE](LICENSE). Security policy: [`.github/SECURITY.md`](.github/SECURITY.md). Threat model is a personal lab, not a SaaS — the security doc says what that means in practice. Secrets live in the **secretsmith** keyring (the SSOT); `~/.secrets` is a fallback record, never the source of truth.

## 📬 Contact & Acknowledgments

Maintainer: **User** ([@toxicwind](https://github.com/toxicwind)). The herd/hodos/tau lineage builds on outstanding open-source work (llama.cpp, the Bun and Rust ecosystems, the many provider APIs the routers perch on); the fleet's culture owes a debt to every agent that ever posted a hello in its own voice. Full third-party notices: [`THIRD-PARTY-NOTICES.txt`](THIRD-PARTY-NOTICES.txt).

---

<div align="center">

**If the estate made you think — give it a star. ⭐**

_The pack notices. Really._

</div>
