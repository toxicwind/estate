---
name: "awrawr_mcp"
description: "Run shell commands on the user's awrawr-pc through its MCP exec bridge (tailscale funnel). Use when asked to run something on awrawr-pc or to use the awrawr-mcp connector."
---

# Awrawr Mcp

## Purpose
Run shell commands on the user's awrawr-pc through its MCP exec bridge
(served over `tailscale funnel`, tool `exec`), using the user-connected
`custom.awrawr-mcp` credential.

## Tooling
`bin/exec.py "cmd" [workdir]` — runs the command on awrawr-pc, prints
stdout/stderr as it streams, exits with the remote exit code. Default
workdir `/home/toxic`, server-side timeout 90s (override: `--timeout N`,
cap 1800s), 200000-char output cap. `bin/exec.py --argv cmd arg...` sends
an argv array: shell-free exec, immune to quoting/backtick/`$()`
substitution on both ends; the server resolves `argv[0]` against a
sanitized remote PATH and fails fast with a clear message when the
executable is missing. `bin/exec.py --timeout 120 --argv ...` combines.
`--json` returns one structured result object instead of streaming:
`{"ok":bool,"code":int,"stdout":str,"stderr":str,"duration_ms":int,
"transport":"ws"|"https","truncated":bool,"error":str|null}` — stdout/stderr
properly separated (the daemon protocol tags streams), output capped at
200k chars with `truncated:true`. Prefer `--json` when an agent needs to
parse the result; the classic streaming form is unchanged.

`bin/agent.py submit [--name NAME] -- cmd [args...]` — first-class subagents
over the bridge: multiple parallel, backgrounded, queryable, detached
workers backed by `/home/toxic/fleet/jobs/bin/job` on awrawr-pc. Detached
setsid processes — cell death cannot touch them. `agent.py list|status <id>|
log <id> [--stderr] [--tail N]|result <id>|kill <id>` manage workers;
`agent.py roster` prints the C2 roster: every tracked subagent, its ledger
state merged with live status. Every lifecycle event (submit/status/kill)
is appended to `~/workspace/c2/agents.jsonl` — the command-and-control
record for all bridge subagents. Long work = `agent.py submit`; never hold
a 90s bridge call open and never `sleep`.

`bin/xfer.py put <local> <remote> | get <remote> <local>` — binary-safe,
resumable file transfer with no shell, no base64 dance, no 90s ceiling.
Native WS binary frames, server verifies size+sha256 and installs
atomically; interrupted uploads resume on retry. `--via auto|bridge|direct`:
from the cell it opens its own wss:// connection (parallel lane, separate
from the exec multiplex); from awrawr-pc itself (interactive shell
included) it uses ws://127.0.0.1:8379 with the local token file — no
proxy, no TLS, no vault. Remote paths must be inside /home/toxic or /tmp.
If the WS path is down, xfer falls back PERMANENTLY to a chunked base64
transfer through `exec.py`'s shell transport (30 KiB chunks, sha256
verified, atomic install) — slower, but the bytes still land. One clean
path switch, no retry loop.

Transport (2026-09-14): `exec.py` talks to a local `bin/ws_daemon.py` over a
Unix socket (`~/.cache/awrawr-ws-bridge.sock`); the daemon holds ONE
persistent `wss://github-mcp-host.tailc9ac71.ts.net/exec-ws` connection and
multiplexes commands over it (~0.2s warm, live streaming). The daemon
starts lazily on first use, re-fetches the auth surrogate on every
(re)connect, and reconnects with backoff. If the daemon is unavailable,
`exec.py` falls back to the legacy MCP streamable-HTTP path (cached
session id, ~0.6-1.1s, fully buffered); the HTTPS path parses the remote
`[exit=N]` wrapper so remote nonzero exits propagate there too;
`--argv` is translated losslessly
with shlex.join for that path, and a custom `--timeout` degrades to the
server ceiling with a warning instead of refusing. `AWRAWR_TRANSPORT=https`
forces the legacy path. `bin/race.py` benchmarks the two transports head to
head. Quiet long commands survive up to the requested command timeout
(ws_daemon per-doc ceiling derives from it).

Server side: `~/awrawr_ws_exec.py` on awrawr-pc, a stdlib-only asyncio
websocket server (handshake/framing borrowed from
`/home/toxic/squawk-ws/squawk_ws_server.py`). Managed by pitchfork as
`sovereign/awrawr-ws-exec`; funnel route `/exec-ws -> 127.0.0.1:8379/exec-ws`
(added surgically via LocalAPI, existing routes untouched). It reuses the
token, command policy, and audit log of `~/awrawr_mcp.py` — same auth
boundary, audit records carry `"transport": "ws"`. It runs under the
`.awrawr-mcp-venv` python (uvicorn lives there, not in system python);
if the pitchfork supervisor ever drops the daemon, a direct
`setsid nohup` start under that venv python restores port 8379 in ~2s
while the supervisor config is reconciled — additive, never a second
init system.

Command policy: the bridge denies catastrophic patterns (`rm -rf /` or `~`,
fork bombs, raw-disk writes, `shutdown`/`reboot`/etc.) with `POLICY DENIED`,
and logs every call to `~/.awrawr_mcp_audit.jsonl` on awrawr-pc. Prefix a
command with `#yolo ` to bypass the policy (still authenticated and audit-
flagged `yolo:true`) — use only when you really mean it.

Audit: JSONL at `~/.awrawr_mcp_audit.jsonl` on awrawr-pc;
`~/awrawr_mcp_audit_export.py` compacts it to `~/.awrawr_mcp_audit.parquet`
(pyarrow/snappy, typed schema), also on a daily systemd timer
(`awrawr-mcp-audit-export.timer`). Run the script with `--print` for a
quick tail.

Python CLIs must import `/opt/hatch/skills/skill-creator/bin/dynamic_credentials.py` and call `add_surrogate_to_request(...)`, `url_with_surrogate_query_param(...)`, or `url_with_surrogate_path_segment(...)` before authenticated requests, matching where the provider reads the key. If they use `urllib`, read JSON responses with `read_json_response(resp)` from the same helper instead of calling `resp.read()` directly. They must send only `hsurr:*` values, and only to the hosts below.

## Auth
The credential is already stored; nothing here collects one. Never ask the user to paste a raw key in chat, set a secret environment variable, pass a secret flag, or write an auth file.

A 401 or 403 is a question about the request before it is a question about the key. Check that the credential was attached at all: a request built without the helpers named under Tooling carries nothing, and that looks exactly like a wrong or under-scoped token. Only once a request that did carry the credential is still rejected, call `credentials.request_api_access` with `reconnect` to replace it. The connector is stored as `custom.awrawr-mcp`.

## Operating Rules
1. Use this skill when the user asks for Awrawr Mcp or this provider's API.
2. Restrict authenticated requests to: github-mcp-host.tailc9ac71.ts.net.
3. Do not print, log, or persist raw credentials.
4. If auth is missing or rejected, follow the Auth section rather than asking for a key.
