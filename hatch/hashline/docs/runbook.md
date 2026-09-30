# hashline runbook

## Install / update (yote)

```bash
hashline --version                  # 0.9.19
hashline update --check             # compare only
hashline update                     # sha256-verified, atomic replace; restart MCP sessions after
HASHLINE_NO_UPDATE_CHECK=1 hashline read f   # silence the 24h notice (agents: export this)
```

Installer source: `curl -fsSL "https://raw.githubusercontent.com/quangdang46/hashline/main/install.sh" | bash`
→ `~/.local/bin/hashline`, auto-wires MCP entries into detected hosts.

## Health check (30 seconds)

```bash
mkdir -p /tmp/hl-health && printf 'one\ntwo\nthree\n' > /tmp/hl-health/t.txt
hashline read /tmp/hl-health/t.txt
# expect: [/tmp/hl-health/t.txt#HASH] + 1:hh|one …
A=$(hashline read --json /tmp/hl-health/t.txt | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['hash'])")
L=$(hashline read /tmp/hl-health/t.txt | sed -n '2p' | sed 's/|.*//')
hashline patch /tmp/hl-health/t.txt "$(printf '[/tmp/hl-health/t.txt#%s]\nSWAP %s:\n+TWO' "$A" "$L")"
# expect: OK /tmp/hl-health/t.txt#… edits=1 changed=1
grep -q '^TWO$' /tmp/hl-health/t.txt && echo HEALTHY
```

## MCP wiring

Stdio server: `hashline mcp`. **Newline-delimited JSON-RPC** (one object per line;
`Content-Length` framing is silently ignored). `initialize` →
`notifications/initialized` → `tools/list` (6 tools) / `tools/call`.
`initialize` returns `instructions` — MCP hosts auto-discover it.

Quick probe:

```bash
printf '%s\n' \
 '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"probe","version":"1"}}}' \
 '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
 '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
 | timeout 15 hashline mcp 2>/dev/null
```

## Troubleshooting

| Symptom | Cause | Fix |
| ------- | ----- | --- |
| `ERR STALE …` / exit 1 | file changed since `read` | re-`read`, re-anchor, retry — never force |
| `ERR EMPTY_PATCH` | patch string didn't arrive (quoting ate it) | check the patch reached the binary; prefer stdin `*** Begin Patch` form |
| `ERR INVALID_ANCHOR` | malformed anchor | `line:hash` (`4:b3`) or range `2:89..4:9c`; re-read for fresh hashes |
| MCP no response | sent `Content-Length` framing | use newline-delimited JSON |
| MCP `read` errors | arg named `path` | arg is **`file`** |
| non-UTF-8 / CRLF file | unsupported encoding | `dos2unix` first |
| crash mid-write risk | default fast write | `--safe` (atomic temp-file + fsync) |
| chained edits need fresh anchors | extra `read` round-trip | `--emit-anchors` (CLI) / `return_updated_anchors` (MCP) |

## Precedent

`/home/toxic/bin/tau-hashline-fix.sh` — the estate's first hashline surgery:
probe `patch --help` → `read` for anchors → verify anchors → backup →
`patch` → build → revert-on-failure (`trap`). Copy this shape for risky edits.

## Daemon supervision (pitchfork) + MCP proxy

pitchfork supervises the daemon; agents talk to the socket, MCP hosts proxy through it:

```toml
# pitchfork.toml
[daemons.hashline]
run = "exec /home/toxic/.local/bin/hashline serve --socket /home/toxic/.hashline/hashline.sock --pid-file /home/toxic/.hashline/hashline.pid"
dir = "/home/toxic"
env = { HASHLINE_NO_UPDATE_CHECK = "1" }
retry = true
ready_cmd = "ss -lx | grep -q /home/toxic/.hashline/hashline.sock"
auto = ["start"]
```

Client env (every agent/MCP host): HASHLINE_SOCKET=/home/toxic/.hashline/hashline.sock and HASHLINE_NO_UPDATE_CHECK=1. Daemon: hashline serve --socket ...
MCP hosts that cannot hold the socket: hashline mcp --proxy-to-daemon
(stdio, newline-delimited JSON-RPC - forwards tool calls to the daemon).
Verified 2026-09-30: pitchfork status hashline running (PID 591769),
socket LISTEN, initialize + tools/list (6 tools) + proxied read green.

Central MCP registry: gatehouse (/home/toxic/.mcpproxy/mcp_config.json,
served on 127.0.0.1:25127). Registered 2026-09-30 via
gatehouse upstream add-json hashline with command hashline,
args [mcp --proxy-to-daemon], env HASHLINE_SOCKET + HASHLINE_NO_UPDATE_CHECK=1.
New servers land quarantined; unquarantine with
POST /api/v1/servers/hashline/unquarantine (X-API-Key header).
All 6 tools (read/patch/write/find_block/remove_file/rename_file)
verified enabled+approved through the proxy.
