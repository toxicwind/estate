# Daemon catalog

Every `[daemons.*]` in `pitchfork.toml`, what it is for, and why it is here.
81 daemons. Generated 2026-10-02 from `pitchfork.toml` and `config/ports.env`;
both are the source of truth, this file explains them.

**Read this first.** `pitchfork.toml` groups daemons by *which project owns the
directory*; that is a filing question, not a "what does this do" question. The
categories below answer the second question. The two do not agree — 38 daemons
filed under one section called `sovereign` include nginx, qdrant, grafana and
the agent runtime, which have nothing in common.

## Naming

The `sovereign` prefix is dead. The control plane is `estate/`; the namespace
survives in env var names (`SOVEREIGN_ROOT`, `SOVEREIGN_PROFILE`,
`SOVEREIGN_TRUSTED_PARENT`), in the `sovereign_session` cookie, and in four
daemon names that are kept because renaming them breaks live state:

| daemon | reality |
|---|---|
| `sovereign-router` `:25104` | live and healthy (`sovereign-router-ts v3.2`). **Not** merged into flock — `ports.env` claimed that and it was wrong; flock `:25193` is stopped. Two different routers. Owned by `ranch/mesh/router/`, so it is ranch, not estate. |
| `sovereign-exporter` `:25213` | a prometheus textfile collector. estate-owned. |
| `sovereign-chat` `:25120` | `tools/sovereign-chat`, a real tool directory. |
| `sovereign-stream-broker` `:25215` | `ranch/stream-broker`. ranch-owned. |

## Ports

`config/ports.env` is the numeric SSOT (97 keys). Every daemon port resolves
there — verified, 0 uncovered. A key not in the SSOT throws at UI module load,
so drift is a build failure rather than a dead tab.

Five keys share a port with another key. All five are documented alias groups
that `bin/port-audit.py` already recognises:

`:25100` HERD_PORT / LLAMA_SWAP_PORT (rename), `:25107` NULL_G_PROXY_PORT /
NULL_G_PORT (canonical / deprecated), `:25133` QDRANT_PORT / QDRANT_HTTP_PORT,
`:25201` RUST_WEB_PORT / RUST_WEB_BACKEND_PORT (former rust-web), `:25204`
EXEC_WS_PORT / WS_EXEC_PORT.

## 1. Estate — core services (19)

The request path. A chat request goes `null-g-proxy → gatehouse → mesh-hub →
herd → flock`.

| daemon | port | why it exists |
|---|---|---|
| `herd` | 25100 | The local model router. ELO-ranks providers, enforces the circuit breaker, owns the 25xxx model path. |
| `sovereign-router` | 25104 | The older TS router, still serving. Runs *beside* herd, not behind it. Superseded but not retired — killing it is a separate decision. |
| `flock` | 25193 | The cloud/paid provider router. Holds the `VANSROUTER_API_KEY` namespace vansrouter used to own. |
| `cuttinggate` | — | The guard plane in front of herd and flock: quarantine, circuit breaker, credential rotation, winner ledger. Not in `groups.*` because it fronts everything else. |
| `mesh-hub` | 25115 | MCP registry. Answers "which MCPs exist". |
| `gatehouse` | 25127 | MCP meta-tool layer — the gatehouse MCP endpoint itself. The SSOT still names this port `MCPPROXY_GO_PORT`. |
| `null-g-proxy` | 25107 | Edge proxy that returns null for blocked traffic. |
| `keypool` | 25109 | Key lifecycle for the paid providers. `sovereign-router` depends on it. |
| `model-guard` | 25101 | Card-derived model request-contract enforcement. |
| `coyote` | 25143 | Agent runtime. |
| `yote` | 25102 | Minimal agent runtime. |
| `duet-yote` | — | Second yote instance. |
| `sovereign-chat` | 25120 | Fleet chat over tailnet + loopback. |
| `fleet-feed` | 25201 | Fleet roster + per-agent history + live ws feed. Was `rust-web`'s `rust_algo_web/src/agents.rs`, ported to TS. |
| `fleet-ui` | — | The squawk shell; fleet is one tab among channels. |
| `tau` | 25111 | The agent engine, behind `chute.mjs`. |
| `mesh-landing` | 25207 | Static landing page for the mesh. |
| `estate-reconcile-watch` | — | Watches for drift between the two copies of a project. |

## 2. Estate — stores and buses (10)

State and message transport. Nothing here is user-facing; everything else
depends on it.

| daemon | port | why it exists |
|---|---|---|
| `redis` | 25199 | valkey, the cache/queue. |
| `qdrant` | 25133/25134 | Vector store (http + grpc). |
| `kafka` | 25144 | Event log. |
| `nats`, `nats-tail` | — | NATS bus and its tail. |
| `squawk-relay-sink`, `squawk-relay-forward` | — | The fleet message spool; sink receives, forward relays cell↔host. |
| `windmill` | 25219 | GPU/PCIe telemetry daemon. |
| `sovereign-stream-broker` | 25215 | Stream broker. ranch-owned. |
| `task-launch` | — | Long-running task launcher. |

## 3. Estate — observability (10)

| daemon | port | why it exists |
|---|---|---|
| `prometheus` | 25105 | Metrics. |
| `grafana` | 25110 | Dashboards. |
| `node-exporter` | 25211 | Host metrics. |
| `sovereign-exporter` | 25213 | Estate-specific metrics into the prometheus textfile collector. |
| `openfang`, `openfang-front` | 25196/25103 | The inference engine and its public proxy. |
| `openfang-health` | — | Live liveness + provider audit for the openfang stack. |
| `bench-radar` | 25181 | Nightly benchmark regression radar. |
| `ml-serve` | 25180 | Model serving for the algo side. |
| `stash-guard` | — | Guards `var/stash` against accidental deletion. |

## 4. Estate — web and edge (14)

Everything a browser can reach. These are the tabs in the master UI.

| daemon | port | why it exists |
|---|---|---|
| `nginx` | 25208 | TLS + reverse proxy. |
| `search-api`, `search-ui` | 25112/25114 | The `ghas` search service. |
| `browserless` | — | Headless chrome for agents. |
| `browser-keeper` | 9223 | Keeps that chrome alive. `9223` is CDP, outside the 25xxx range. |
| `agent-display`, `agent-viewer` | 5900/6080 | Isolated virtual display (Xvnc + noVNC) for agent browsers. |
| `files` | 34567 | tailscale-served file access. Platform port, outside 25xxx. |
| `matter-server` | 25209 | Matter/bridge integration. |
| `bedrock-ui` | 25137 | Evidence-locker web UI. Token-gated, tailnet only. |
| `ralph-dashboard` | 25194 | Dashboard for the ralph loop. |
| `boundless` | 25197 | Document ingestion web app. |
| `mesh-landing` | 25207 | (also in core) the mesh landing page. |

## 5. Estate — model engines (12)

| daemon | port | why it exists |
|---|---|---|
| `beellama-fast` | 25122 | The main local llama.cpp build. |
| `toolcall-llm` | 25152 | Tool-calling model (qwen3.5-9b), OpenAI-compatible. |
| `kimi-auto-shim` | 25153 | Alias forwarder for the kimi-auto stack. Model selection lives in `herd.d/kimi-auto.yaml`, never in tool code. |
| `nim-kimi-sidecar` | 25163 | NVIDIA NIM sidecar. |
| `byte-vision` | 25121 | Vision inference. |
| `hf-downloader` | 25106 | HuggingFace model fetches. |
| `hindsight` | 25117 | Agent memory. |
| `kimi-code` | 25126 | Kimi coding agent. Guarded by `bin/claim-port` — explicit port, fails fast, never walks. |
| `kimi-audit-dash` | — | Token audit dashboard. |
| `kimiclaw-a`, `kimiclaw-b` | — | Two bridge instances. |
| `dnsmasq` | — | Local resolver. |

## 6. Estate — oracle market (9)

The agent-for-hire market. Distinct from everything above: these are not
services the estate runs for itself, they are the bidding machinery.

| daemon | port | why it exists |
|---|---|---|
| `oracle-core` | 25151 | The market core. |
| `oracle-market`, `oracle-chat` | — | Market loop and its chat surface. |
| `bidder-forge`, `bidder-scout` | — | Bid construction and scouting. |
| `market-loop` | — | The estate-side market loop. |
| `market-watchdog` | — | Keeps the loop honest. |
| `refusal-watchdog`, `sorry-watchdog` | — | Watchdogs for the classifier false-positive hunt. |

## 7. Estate — agent ops (9)

| daemon | port | why it exists |
|---|---|---|
| `flicker`, `flicker-agent` | 25148 | CI build server and its agent. Was filed as `BRAND_PORT`/`brand`; the daemon was renamed, not retired. |
| `hashline` | — | The hash-anchored editor's socket server. |
| `awrawr-mcp` | 25198 | The estate MCP server. |
| `awrawr-ws-exec` | 25204 | WS exec transport. **Never claim or kill** — protected port. |
| `codebase-memory` | 25195 | codebase-memory MCP daemon. |
| `paper-poller`, `paper-poller-watchdog` | 25149/25150 | arXiv/alphaXiv poller + health. |
| `whatsapp-mcp` | 25146 | WhatsApp MCP. Took over the port zedra-host released. |

## 8. Ranch-owned (not estate) (24)

`ranch/` is its own git repo. These are composed into the parent config but the
project owns the code: `gatehouse`, `cuttinggate`, `fleet-ui`, `fleet-feed`,
`nats`, `nats-tail`, the six oracle daemons, `sovereign-stream-broker`,
`windmill`, `task-launch`, `yote`, `flock`, `mesh-landing`, `flicker`,
`flicker-agent`, `squawk-relay-*`, `keypool`.

## 9. Dead (1)

| daemon | port | status |
|---|---|---|
| `vansrouter` | 20128 | **Dead.** `projects/range/ranch/stockyard/vansrouter/` is gone; `stack/services/vansrouter.sh:41` resolves to that missing path and prints `VansRouter source build missing`. Nothing listens on 20128. The migration to flock already happened — flock holds the `VANSROUTER_API_KEY` namespace. Kept in `pitchfork.toml` rather than deleted because the launcher is the evidence; retiring it is a one-line change once someone confirms flock is the replacement. |

## Rules this catalog encodes

1. **A group member must be a real `[daemons.*]`.** Four were not: `rust-web`
   (renamed to `fleet-feed`) and `squawk-feed` / `squawk-ws` / `squawk-ui`, which
   have no daemon definition anywhere. pitchfork ignores names it cannot resolve,
   so they never errored — they just made the group claim services it does not
   run.
2. **A daemon port must be in `config/ports.env`.** Verified 0 uncovered.
3. **A renamed service keeps its port.** `HERD_PORT` exists because herd is the
   rename of llama-swap and 38 files still read the old name.
4. **Do not retire a daemon because its launcher looks wrong.** vansrouter's
   launcher points at a deleted tree, and BRAND_PORT looked unused until the
   daemon behind it turned out to be `flicker`, live the whole time.