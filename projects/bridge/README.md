# bridge — hatch→yote bridge exec maximal layer

The bridge is the control plane between **hatch** (this cell) and **yote**
(the heavy box). This project holds the maximalized exec layer built by
**bridge-max** (2026-09-20): multitask dispatch, detached background dispatch,
and the supporting docs.

## Layout

| Path | What |
|---|---|
| `bin/bg-run.py` | Yote-side detached background runner. Launched via `setsid nohup … &` with the exec workdir set to its state dir so `&` binds only to the runner. Writes `status.json` atomically + `stdout.log`/`stderr.log` under `/home/toxic/.cache/bridge-bg/<handle>/`. |
| `bin/bg-status.py` | Yote-side status probe: reads `status.json`, **reaps stale runners on read** (pid dead or reused → atomically rewritten to `"stale"`; pid verified via `/proc/<pid>/cmdline`), returns status + log tails as one JSON doc. Optional `[soff] [eoff]` byte offsets add incremental-attach chunks (`stdout_b64`/`stdout_soff`, `stderr_b64`/`stderr_eoff`; negative = last N bytes) — backs `yote-conn bg-tail`. |
| `bin/bg-kill.py` | Yote-side kill: verifies `/proc/<pid>/cmdline` is still our `bg-run.py` for the handle (a reused pid is never signaled), then SIGTERMs the whole process group. |
| `hatch/connector.py` | Canonical source of the cell-side yote-connector daemon (127.0.0.1:18301). v2.0 adds `POST /exec-multi`, `POST /exec-bg`, `GET /bg`, `GET /bg/<handle>`. v2.1 routes status through `bg-status.py` (reap-on-query) and adds `POST /bg/<handle>/kill`. v2.2 (lane-oracle-connector, 2026-09-20): `/exec-bg` honors `timeout_s` and forwards `workdir` to `bg-run.py` (both were silently dropped before); `GET /bg/<handle>?soff=N&eoff=M` incremental attach. |
| `hatch/yote-conn` | Canonical source of the CLI. Adds `multi`, `bg` (with `[workdir] [timeout_s]`), `bg-status`, `bg-tail <handle> [soff] [eoff]` (incremental attach; negative offset = last N bytes), `bg-list`, `bg-kill`. |
| `hatch/deploy-cell.py` | Canonical cell deploy script. Pulls `connector.py`, `yote-conn` (both from this dir) and `gear/awrawr-mcp/bin/exec.py` from the yote tree onto the cell, SHA-verifies, installs atomically, restarts the connector, health-checks. Cell copy: `~/workspace/bin/deploy-yote-connector` (kept in sync). |

The live copies on the hatch cell (`~/workspace/yote-connector/connector.py`,
`~/workspace/bin/yote-conn`) are deployed FROM this repo. Edit here, deploy,
never the reverse.

## API

### Multitask — one lane, N commands, concurrent

```bash
yote-conn multi cmds.json
# cmds.json: [{"cmd": "…", "workdir"?: "…", "timeout"?: 120, "tag"?: "…"}, …]
# or a plain ["cmd1", "cmd2"] string list
```

Runs up to 8 commands concurrently (tunable `max_workers`, cap 16, max 64
cmds/batch) through the WS lane with HTTPS fallback per command. Returns
tagged results: exit code, stdout, stderr, transport, per-command ms, total ms.

### Background — dispatch and forget, check later

```bash
handle=$(yote-conn bg "long-running-cmd")
yote-conn bg-status "$handle"
yote-conn bg-tail "$handle" 0 0        # incremental attach from byte 0
yote-conn bg-tail "$handle" -4000 -4000 # last 4000 bytes of each stream
yote-conn bg-list
yote-conn bg-kill "$handle"   # SIGTERM the job's process group
```

The command is launched fully detached on yote: new session (`setsid`),
stdin `/dev/null`, output redirected, PPID 1. Status truth is the yote-side
`status.json` — no polling loops, just `cat` it via `bg-status`.

Detachment proof: `ps -o pid,ppid,sid,cmd` on the runner shows PPID 1 and its
own SID, and it survives the launching exec session closing.

**Reaping (no zombies):** if a runner dies without writing its final status
(SigKILLed, box reboot mid-job), the next `bg-status` query detects the dead
pid (verified via `/proc/<pid>/cmdline`, so a reused pid can never
false-positive) and atomically rewrites the ledger entry to `"stale"`.
Reaping happens exactly on query — event-driven, never a timer. `bg-kill`
sends SIGTERM to the whole process group, then the same reap path marks it
`"stale"` on the next status read.

## MCP tools (awrawr-pc main MCP, `/home/toxic/awrawr_mcp.py`)

- `exec_multi(cmds, workdir, timeout)` — concurrent local exec, same policy/audit path as `exec`.
- `exec_bg(cmd, workdir)` — detached local launch (`start_new_session=True`), returns handle.
- `bg_status(handle)` — status + log tails from `/home/toxic/.cache/mcp-bg/<handle>/`.
- `bg_list()` — every exec_bg handle with state/exit/pid/cmd (mcp-smith).
- `bg_kill(handle)` — SIGTERM then SIGKILL a background handle's process group (mcp-smith).
- `fleet_send(channel, text, title, sender)` — publish to a squawk channel natively (mcp-smith).
- `fleet_read(channel, limit, since_seq)` — read a squawk channel natively (mcp-smith).
- `yote_load()` — load vs cores, memory, top CPU procs (mcp-smith).
- `port_map()` — listening TCP ports with owning process (mcp-smith).
- `pitchfork_daemon(name, action)` — list/status/restart pitchfork daemons; never the live bridge (mcp-smith).

## Canonical path policy

- **Operator path:** `yote-conn` (this repo's `hatch/yote-conn`) is the single
  canonical command for cell→yote exec, background dispatch, and service
  proxying. The legacy `awrawr-bridge/exec.py` direct path is the transport
  layer, not the operator interface: `bexec` is now a thin compatibility
  shim over `yote-conn exec`, and operational tooling (`fleet-classify`)
  calls `yote-conn`.
- **Deliberate exceptions:** the emergency circuit-breakers
  (`hatch/bin/swarm-eject`, `swarm-resume`, `swarm-watchdog`) keep raw
  `exec.py` on purpose — they must work when the 18301 connector daemon
  itself is down or the cell is overloaded. Their comments say so; do not
  "canonicalize" them.

## Durability

Everything here is committed source. It survives a full bridge restart and a
yote power-cycle: no in-memory state (the bg registry is a JSON file, status
truth lives in files on yote), no monkeypatching, no `/tmp` dependencies.

## See also

- `docs/fleet-knowledgebase.md` — estate map, services & ports, bridge tools.
- `~/workspace/awrawr-bridge/exec.py` — the WS/HTTPS lane implementation (hatch cell).
- `/home/toxic/sovereign/shingle-workspace/awrawr_ws_exec.py` — the yote-side WS exec server.
