# sovereign-projects

Chris's ops + workspace monorepo on the yote box (`/home/toxic/sovereign`): one
OpenAI-compatible inference front door, a pitchfork-supervised service stack,
agent runtimes, MCP federation, and the Ember operational home — all in one
repo. Canonical GitHub remote is
[toxicwind/sovereign-projects](https://github.com/toxicwind/sovereign-projects)
(`toxicwind/sovereign` is a stale trap — don't push there).

## What this is

Two things in one tree:

1. **The control plane** — `pitchfork.toml` (service definitions, pitchfork
   supervisor), `mise.toml` (tooling + tasks), `config/` (port assignments,
   the inference routing matrix). This is the ops layer that keeps the box
   running.
2. **The workspaces** — `projects/` holds the actual projects: the inference
   stack (`herd`), the agent engine (`tau`), the lightweight agent (`yote`),
   the agent OS mirror (`openfang`), the editor substrate (`qed`), the
   tool-federation layer (`mesh`), the quickshell home (`shell`), plus
   research probes and audit workspaces.

Plus the agent layer: `hatch/agents/ember` (Ember's operational home, with the
squawk agent-to-agent chat), `agents/` (oracle-market, coyote, …),
`bridge/` (the live hatch↔yote exec bridge), and `scratch/` (explicitly
non-production staging).

## Quickstart

On yote, in `/home/toxic/sovereign`:

```bash
mise install          # pins python/node/bun/rust/go/pitchfork per mise.toml
mise run up:all       # pitchfork start -q --group all (all daemons)
pitchfork list        # daemon status
mise run health-herd  # curl the herd /health endpoint
mise run down-herd    # stop just the herd daemon
mise run logs-tail    # follow the supervisor log
```

- Tasks are defined in [`mise.toml`](https://github.com/toxicwind/sovereign-projects/blob/main/mise.toml#L27-L31) — `up:all`, per-service `up-<name>` / `down-<name>`, per-service `health-<name>` probes, `logs`/`logs-tail`/`logs-json`.
- Port numbers live in one place: [`config/ports.env`](https://github.com/toxicwind/sovereign-projects/blob/main/config/ports.env#L1-L3) — the port SSOT, loaded by mise and pitchfork.
- **pitchfork does NOT hot-reload its config** — after editing any `[daemons.*]` section, run `bin/pitchfork-restart sovereign/<name>`. The reload rule is documented at the top of [`pitchfork.toml`](https://github.com/toxicwind/sovereign-projects/blob/main/pitchfork.toml#L1-L13).

## The service stack

Daemon definitions live in [`pitchfork.toml`](https://github.com/toxicwind/sovereign-projects/blob/main/pitchfork.toml)
(the generator is retired — this file is hand-edited). Daemons are organized
into pitchfork groups: `mesh`, `core`, `agents`, `all`
([`pitchfork.toml#L267-L276`](https://github.com/toxicwind/sovereign-projects/blob/main/pitchfork.toml#L267-L276)).

| Port | Daemon | Role |
| ---- | ------ | ---- |
| :25100 | `herd` | Inference front door — OpenAI-compatible `/v1` (llama-swap fork + flock router) |
| :25101 | `model-guard` | Request-contract enforcement proxy in front of herd (rewrites `chat/completions` per `config/model_constraints.yaml`) |
| :25109 | `keypool` | Provider key pool for herd cloud routing (`bin/herd-keypool.py`) |
| :25201 | `rust-web` | Ops dashboard backend |
| :25104 | `sovereign-router` | Multi-provider LLM router (Bun/TS, `tools/sovereign-router/`) |
| :8000 | `flock` | Cloud-provider routing daemon backing herd |
| :25127 | `shep` | MCP federation — upstream servers → one endpoint |
| :25147 | `squawk-ws` | Squawk agent chat — websocket server |
| :25135 | `squawk-feed` | Squawk feed sequence server |
| :8379 | `awrawr-ws-exec` | The live hatch↔yote exec bridge (see `bridge/`) |
| :25102 | `yote` | Lightweight agent runtime |
| :25143 | `coyote` | Autonomous agent inference engine |
| :25125 | `tau` | Tau agent engine service |
| :25103 | `axiom` | OpenFang agent host |

Inference chain, verified from the config files:

```text
clients (Zed / OpenFang / IDEs)
  └─► herd :25100  (llama-swap fork + flock cloud routing)
        ├─► local backends from :25001 up (llama-server forks)
        └─► cloud providers via flock :8000 (openrouter, nvidia, groq, …)
```

The routing matrix is [`config/herd.yaml`](https://github.com/toxicwind/sovereign-projects/blob/main/config/herd.yaml#L4-L8) —
the canonical llama-swap config (RTX 3090 24GB, `startPort: 25001`).

## Repo layout

```text
sovereign-projects/                     # this repo — /home/toxic/sovereign on yote
├── pitchfork.toml          # service definitions (supervisor) — hand-edited SSOT
├── mise.toml               # tool pins + up/down/health/log tasks
├── config/                 # ports.env (port SSOT), herd.yaml, keypools.yaml, …
├── bridge/                 # production home of the hatch↔yote exec bridge
├── hatch/                  # hatch-cell side: agents/ember, docs/
├── scratch/                # NON-PRODUCTION staging (old shingle-workspace); symlinks shimmed
├── projects/               # the workspaces: herd, tau, yote, openfang, qed, mesh, shell, …
│                           # root-level symlinks (herd/, tau/, yote/, mesh/, shell/, qed/)
│                           # point here for historical paths
├── agents/                 # oracle-market, coyote, kimiclaw, toolcall rigs, …
├── skills/                 # reusable skills (paper-search, …)
├── bin/                    # ops scripts: pitchfork-restart, herd-keypool.py, …
├── stack/                  # service entry scripts (stack/services/herd.sh, …)
├── src/                    # Bun services (mesh-hub, yote, openfang, …)
├── tools/                  # sovereign-router, sovereign-monitor, …
├── tests/ test/            # test suites
├── ops/                    # yote-fix.sh, yote-doctor.sh — bridge repair runbook
├── docs/                   # architecture + ops docs (see docs/README.md)
└── .secrets                # 400KB local secret bundle — gitignored, NEVER commit
```

Layout SSOT for the 2026-09-20 reorg (hatch/, bridge/, scratch/): `REORG-PLAN.md`.

## Key components

### Inference — herd

[`projects/herd/`](https://github.com/toxicwind/sovereign-projects/tree/main/projects/herd) —
the **toxicwind fork of llama-swap** (Go): the stack's single OpenAI-compatible
endpoint on `:25100`. Cloud-provider routing is delegated to the `flock` daemon
on `:8000`; the in-process `internal/flock` Go router was retired 2026-09-17.
Live service: pitchfork `herd` → `stack/services/herd.sh` with
[`config/herd.yaml`](https://github.com/toxicwind/sovereign-projects/blob/main/config/herd.yaml).
[`flock` daemon`](https://github.com/toxicwind/sovereign-projects/blob/main/pitchfork.toml#L224-L231) ·
[`keypool` daemon`](https://github.com/toxicwind/sovereign-projects/blob/main/pitchfork.toml#L662-L668)
[Self-healing peers](https://github.com/toxicwind/sovereign-projects/blob/main/projects/herd/README.md#self-healing-peers-2026-09-20):
event-driven dead-peer detection (healthy/degraded/circuit-open FSM, single-flight
half-open recovery on real traffic) with `GET /peer-health` observability.

### Agents

- **[`projects/tau/`](https://github.com/toxicwind/sovereign-projects/tree/main/projects/tau)** — Tau agent engine (AI-native agent engine, 1M+ context reasoning, MCP + herd inference). Pitchfork daemon `tau` runs `engine/packages/coding-agent/dist/omp`.
- **[`projects/yote/`](https://github.com/toxicwind/sovereign-projects/tree/main/projects/yote)** — Yote, the minimal embeddable agent runtime (`:25102`, inference via herd, MCP via shep `:25127`).
- **[`agents/oracle-market/`](https://github.com/toxicwind/sovereign-projects/tree/main/agents/oracle-market)** — the oracle market: HMAC-signed bidder profiles, Vickrey second-price clearing, stake-and-slash accountability. Spec at [`agents/oracle-market/SPEC.md`](https://github.com/toxicwind/sovereign-projects/blob/main/agents/oracle-market/SPEC.md#L1-L13).
- **[`projects/openfang/`](https://github.com/toxicwind/sovereign-projects/tree/main/projects/openfang)** — OpenFang agent OS (mirror of RightNow-AI/openfang; daemon `axiom` hosts it on `:25103`).

### Bridge — hatch↔yote exec

[`bridge/`](https://github.com/toxicwind/sovereign-projects/tree/main/bridge) is
the [production home](https://github.com/toxicwind/sovereign-projects/blob/main/bridge/README.md#L1-L4)
of [`awrawr_ws_exec.py`](https://github.com/toxicwind/sovereign-projects/blob/main/bridge/awrawr_ws_exec.py#L1-L13) —
the persistent websocket exec bridge (Tailscale Funnel `/exec-ws` → `127.0.0.1:8379`),
stdlib-only asyncio websocket, same security layers as the HTTPS bridge.
Pitchfork daemon [`awrawr-ws-exec`](https://github.com/toxicwind/sovereign-projects/blob/main/pitchfork.toml#L390-L397)
runs the tracked copy. Bridge repair runbook: `ops/` (`yote-fix.sh`, `yote-doctor.sh`).

### Hatch cell side — squawk

[`hatch/`](https://github.com/toxicwind/sovereign-projects/tree/main/hatch) is the
[hatch-cell side of the world](https://github.com/toxicwind/sovereign-projects/blob/main/hatch/README.md#L1-L4):
`agents/ember/` is Ember's operational home, `docs/` consolidates
hatch/bridge/cell documentation. The squawk agent-to-agent chat is driven by
[`bin/squawk`](https://github.com/toxicwind/sovereign-projects/blob/main/hatch/agents/ember/bin/squawk#L1-L19) —
one-command wrapper over HMAC-signed, profile-based message publication
(fleet/lead channels, global sequence).

### Tool federation — mesh

[`projects/mesh/`](https://github.com/toxicwind/sovereign-projects/tree/main/projects/mesh) —
MCP gateway source, sovereign-router variants, AST code-navigation packages, the
unified mesh config. Daemons: `shep` (`:25127`, MCP federation),
`mesh-hub` (service discovery + health).

### Editor + shell

- [`projects/qed/`](https://github.com/toxicwind/sovereign-projects/tree/main/projects/qed) — the editor layer: the zed fork and zedra (remote/mobile substrate).
- [`projects/shell/`](https://github.com/toxicwind/sovereign-projects/tree/main/projects/shell) — Chris's quickshell home: the `ii` fork of end-4's illogical-impulse (submodule `toxicwind/sovereign-end4`) plus its ops layer.

## Docs

`docs/` holds architecture + ops docs (see
[`docs/README.md`](https://github.com/toxicwind/sovereign-projects/blob/main/docs/README.md)
for the index). `hatch/docs/` holds the bridge/cell docs moved there by the
reorg.

**Required reading for every agent in the fleet:**
[`docs/fleet-knowledgebase.md`](docs/fleet-knowledgebase.md) — estate map,
active crews, repo index, standing rules, docs index.

## Conventions

- **Never invent port numbers in app code** — read them from env, `config/ports.env`, or `src/lib/ports.ts`.

Run `bin/port-audit` on yote any time ports look wrong: it diffs the live `ss -tlnp` listener table against `config/ports.env` and reports bind conflicts, unregistered listeners, and stale entries. The hardened audit (2026-09-20) attributes every listener by full /proc cmdline plus process ancestry (no more blind spots behind bun/node/python comm names), reads `# owner:` hints from `ports.env`, knows the intentional alias groups (:25100 herd/llama-swap, :25107 null-g, :25133 qdrant), treats the 25001-25099 herd pool and expected-but-dark ports as informational, and warns on SSOT ports outside Chris's 25000-35000 mandate. Exit codes: 0 clean, 1 conflict, 2 error (--strict promotes unregistered listeners to conflicts, --json for machines). `bin/claim-port <port> <cmd>` is the fail-fast pre-launch guard: occupied ports refuse (exit 4) with holder cmdlines, protected ports (bridge 8379/25204, squawk 25147/25135) refuse outright (exit 5) - it never kills, never sleeps, never polls. Tests: `python3 -m unittest discover -s bin/tests`. `herd-keypool` listens on 25109 (override: `KEYPOOL_HOST`/`KEYPOOL_PORT`); `herd-model-guard` on 25101 (override: `MODEL_GUARD_HOST`/`MODEL_GUARD_PORT`) — a second instance on a taken port exits 98 with a clear message instead of a traceback.
- **`git add` specific paths only** — this is a shared tree with multiple workers and live WIP; never `git add -A`.
- **Fetch-first, rebase, never force-push.** Verify with `git ls-remote origin refs/heads/main` after every push.
- **`projects/guidellm` is another agent's live workspace** — don't touch it.
- **Don't kill live daemons** (`:8379` bridge, `:25147`/`:25135` squawk, `:25100` herd, `:25109` keypool); bridge-repair scripts must never kill squawk.
- Secrets live in `~/.secrets` and `.env.local` — never in git.

## License

Stack glue: MIT where marked. Upstream binaries and forks keep their licenses (llama-swap, Zed, Grafana, …).
