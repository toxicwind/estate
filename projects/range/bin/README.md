# bin

Hand-written glue between [pitchfork](/home/toxic/sovereign/pitchfork.toml) and
the services it supervises. Six files; nothing here is a library.

> A pitchfork `run=` line wants a bare binary, and a bare binary cannot source
> `~/.secrets`, bootstrap a gitignored config, or fail loudly when a secret is
> missing. Every launcher in this directory exists to close that gap — and the
> launcher is the only place it gets closed.

---

## Contents

| File | Kind | Spawned by | Port |
| :--- | :--- | :--- | :---: |
| `gatehouse-serve.sh` | launcher | pitchfork `[daemons.gatehouse] run=` | `25127` |
| `landing.py` | HTTP service | pitchfork `[daemons.mesh-landing] run=` | `25207` |
| `openfang-mcp-shim.py` | stdio bridge | gatehouse `mcp_config.json`, *not* pitchfork | — |
| `openfang-mesh-probe.sh` | probe | a human, in a terminal | — |
| `gatehouse` | Go binary, current build | exec'd by `gatehouse-serve.sh` | — |
| `gatehouse-v0.51.0` | Go binary, pinned rollback | nothing | — |

The distinction that matters: a **launcher** is named by a pitchfork `run=`
line, a **bridge** is named by a config file, and a **probe** is named by a
person. Only the first two run unattended.

---

## The launcher pattern

`gatehouse-serve.sh` is the reference implementation and the only launcher here.
The unit is a bare `exec` of the script, with `dir` pointed at the service's own
working directory:

```toml
[daemons.gatehouse]
run  = "exec /home/toxic/sovereign/projects/range/bin/gatehouse-serve.sh"
dir  = "/home/toxic/sovereign/projects/range/ranch/barn/gatehouse"
port = 25127
```

What the script adds over running the binary directly, in order:

1. **Source secrets.** `. /home/toxic/.secrets`, if present. No value is ever
   read from the repo.
2. **Fail fast.** `: "${MCPPROXY_API_KEY:?...}"` — a missing secret exits
   non-zero with a named error instead of crash-looping. The pitchfork comment
   on the unit says it outright: *gatehouse direct-run crash-loops without it.*
3. **Conditional pass-through.** `EXA_API_KEY` is exported only if already set.
4. **Bootstrap config.** Copy the tracked `.dist` template to the live path and
   `chmod 600` it — only when the live file is missing, so a restart never
   clobbers accumulated state. This is what makes a fresh clone self-heal.
5. **`exec`.** The binary replaces the shell, so pitchfork's supervision,
   signal delivery and restart policy attach to the daemon rather than a wrapper.

New launchers follow the same five steps. A script that cannot do *source, fail
fast, bootstrap, exec* does not belong in a `run=` line.

---

## Secret hygiene

The gatehouse config is not read-only. Gatehouse writes the *effective* config
back to `mcp_config.json` on every start, re-materializing live credentials —
`api_key`, per-server `env` — into the file. That one behavior dictates the
layout:

| Path | Tracked | Contents |
| :--- | :---: | :--- |
| `barn/gatehouse/mcp_config.json` | no | live config, re-materialized secrets, `0600` |
| `barn/gatehouse/mcp_config.json.dist` | **yes** | same schema, `REDACTED` placeholders |
| `/home/toxic/.secrets` | no | the only origin of real values at runtime |

The `Tracked` column is the intended layout, and the ignore rules in
`ranch/.gitignore` do enforce it for new files. They cannot enforce it for
files already in the index: a tracked path is never ignored, which is exactly
how the key was committed in the first place. Verify with
`git ls-files | grep mcp_config` rather than trusting the rules alone.

Edit the `.dist` template to add an upstream server; the launcher copies it
forward on the next start where the live file is absent. Copying a live config
into the repo is precisely the failure this split exists to prevent.

---

## The bridge

`openfang-mcp-shim.py` is a different shape: gatehouse spawns it as a stdio MCP
server, named in `barn/gatehouse/mcp_config.json.dist` and nowhere else.

```json
{
  "command": "/usr/bin/python3",
  "args": ["/home/toxic/sovereign/projects/range/bin/openfang-mcp-shim.py"],
  "name": "openfang",
  "protocol": "stdio"
}
```

`openfang mcp` speaks LSP-style `Content-Length` framing on stdio; the gateway
and most MCP clients speak newline-delimited JSON. The shim translates in both
directions so the openfang agent tools can sit behind the mesh gateway. Child
binary comes from `OPENFANG_BIN`, default `/home/toxic/.local/bin/openfang`.
It handles no secrets — the child inherits the gateway's environment.

---

## The probe

```sh
bin/openfang-mesh-probe.sh
```

Exits 0 only if the full chain works: gatehouse reports `openfang` as
`Connected` with ≥1 tool discovered, and a live `call tool-write` to
`openfang:openfang_agent_coyote` returns the exact string `MESH-PROBE-OK`.
Anything short of that prints `PROBE-FAIL: <reason>` and exits 1.

Run it after touching the shim, the openfang entry in `mcp_config.json`, or
gatehouse itself. It is the cheapest way to tell "the daemon is up" from "the
chain works" — pitchfork's `health_http` only proves the former.

---

## landing.py

A stdlib-only status page for the mesh funnel. `ThreadingHTTPServer` on
`127.0.0.1:25207`, three routes:

| Route | Response |
| :--- | :--- |
| `/` | HTML table — alive/dead dot, HTTP code, latency, public funnel path |
| `/api/status` | the same rows as JSON |
| `/health` | `{"status": "ok"}` — for pitchfork `ready_http` |

It probes ten localhost backends concurrently, caches for 10 s, and treats
*any* HTTP response — including 401, 404, 426 — as proof the backend is alive,
because a socket that answers at all is the thing being asserted. Routes with
no public funnel path are rendered as `tailnet` rather than linked. The page
carries a 30 s `<meta refresh>`.

Port overrides read from env: `MESH_LANDING_PORT`, `AWR_MCP_PORT`,
`BRIDGE_EXEC_PORT`, `GEMINI_MCP_PORT`. The rest are literals in `BACKENDS`.

---

## The binaries

`gatehouse` is the current build. `gatehouse-v0.51.0` is a pinned copy of the
previous release, kept so a bad build rolls back without a rebuild. Neither is
tracked: both are build products, ignored by `projects/range/.gitignore`, and
**not** LFS. At ~70 MB and ~48 MB they would dominate the repository. Roll back
by copying the pinned file over `gatehouse` — `git checkout` cannot restore it,
because it was never committed.

Upstream is [smart-mcp-proxy/mcpproxy-go](https://github.com/smart-mcp-proxy/mcpproxy-go)
(`cmd/mcpproxy`), unmodified.

---

## Naming: `shep` no longer means the gateway

This directory went `mcpproxy` → `shep` → `gatehouse` on 2026-09-26. `shep` now
refers to the unrelated [shep-ai/shep](https://github.com/shep-ai/shep) agent
orchestrator. Two consequences:

- `MCPPROXY_API_KEY` keeps its upstream name. That is upstream's spelling, not
  a rename that was missed here.
- `landing.py` renders the `:25127` gateway under `"gatehouse MCP"` /
  `"gatehouse health"` / `"gatehouse metrics"` labels in its `BACKENDS` table
  (fixed 2026-09-29; was the last `"shep …"` string in code).

---

## See also

- [`pitchfork.toml`](/home/toxic/sovereign/pitchfork.toml) — daemon definitions
- [`barn/gatehouse/`](../ranch/barn/gatehouse/) — the gateway this directory launches
- [`../ranch/stockyard/herd/docs/flock/`](../ranch/stockyard/herd/docs/flock/) — the other side of the mesh
