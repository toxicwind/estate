# Thresher MCP registration guide — shipping a fleet MCP surface

_How ANY estate service becomes first-class MCP tools for every agent on the
box. Written from the flotilla-mcp ship (2026-10-28), every command verified
live that day. Companion: `docs/mcp-protocol-transports.md` (tau-internal
protocol layer — this guide is the FLEET-side registration layer)._

## The one diagram

```
agent (tau/kappa/zed/…)                     phone bridge example
     │  POST :25127/mcp (sessioned)          flotilla/mcp/server.ts
     ▼                                              ▲
thresher :25127  ── retrieve_tools router ──▶  http://127.0.0.1:25245/mcp
     │                 (routing_mode)                ▲
     └── upstreams from mcp_config.json ─────────────┘
         (65+ servers: taas-telegram :25243, gemini-mcp :25227, flotilla :25245, …)
```

Agents never point at upstreams — ONLY at `:25127/mcp`. Upstreams are plain
HTTP loopback services that speak streamable-HTTP JSON-RPC.

## 1. Build the drop-in server

Copy the proven 80-line shape: `pens/ranch/android-fleet/flotilla/mcp/server.ts`
or `pens/ranch/arroyo/overlord/src/taas.ts`. Contract:

- `POST /mcp` — JSON-RPC 2.0: `initialize` → `notifications/initialized`
  (202) → `tools/list` → `tools/call`.
- `GET /health` — pitchfork readiness + fleet health checks.
- Bind **127.0.0.1** unless LAN clients genuinely need it (see firewall, §5).
- Port from `process.env.<NAME>_PORT` with the ports.env number as default.

## 2. Pin the port in the SSOT

`/home/toxic/estate/config/ports.env` (one line, owner comment):

```bash
FLOTILLA_MCP_PORT=25245  # owner: ranch/android-fleet/flotilla/mcp/server.ts (pixel MCP bridge via thresher)
```

Check the neighborhood first — ports are grouped by decade (25240s = village
services). Never squat a doorbell-owned port (anomaly #24).

## 3. Register the pitchfork daemon (monolith ONLY)

`/home/toxic/pens/estate/pitchfork.toml` is the **only live truth** (anomaly
#6: pitchfork.d fragments are dead; never resurrect generate.ts):

```toml
[daemons."flotilla-mcp"]
run = "exec /home/toxic/.bun/bin/bun /home/toxic/pens/ranch/android-fleet/flotilla/mcp/server.ts"
auto = ["start"]
retry = true
mise = true
port = 25245
ready_http = "http://127.0.0.1:25245/health"
dir = "/home/toxic/pens/ranch/android-fleet"

[daemons."flotilla-mcp".health_http]
url = "http://127.0.0.1:25245/health"
interval = "60s"
timeout = "5s"
```

No deprecated keys (`expected_port`/`auto_bump_port`) next to `port` — that
WARNs on every pitchfork call (morphe shipped that for weeks; purged 10-28).

## 4. Federate into thresher (LIVE config only)

Config SSOT map (skill `thresher-mcp-gateway-audit`):

| Path | Truth |
|---|---|
| `/home/toxic/estate/ranch/thresher/mcp_config.json` | **LIVE — daemon reads this** (verify via `/proc/<pid>/cmdline --config=`) |
| `pens/ranch/thresher/mcp_config.json` | stale diverged mirror — DO NOT EDIT |
| `~/.mcpproxy/mcp_config.json` | empty default, ignored |

Append to `mcpServers` (mirror of the taas-telegram entry):

```json
{
  "quarantined": false,
  "name": "flotilla",
  "url": "http://127.0.0.1:25245/mcp",
  "protocol": "http",
  "command": "",
  "args": [],
  "env": {},
  "oauth": null,
  "enabled": true
}
```

**Protocol string is `"http"`** — anomaly #21: one guessed enum
(`streamable_http`) crashed the estate's only MCP door for hours. Copy an
existing working entry verbatim; change name/url only.

Then: `pitchfork restart estate/thresher` → poll `:25127/health`.

## 5. If LAN clients must reach it: nft allowlist

Loopback-registered servers need nothing. For LAN (the phone hitting the box),
`/etc/nftables.conf` `inet awrawr_filter` input chain, LAN tcp set:

```
ip saddr 10.0.0.0/24 tcp dport { 22, 3000, 3001, 8503, 25100-25107, 25203, 25243 } accept
```

Lesson (2026-10-28, taas): **box-side `curl 10.0.0.218:port` succeeding proves
NOTHING** — that traffic never leaves the box and skips the LAN rule path.
Probe from the actual client (phone: `adb shell nc -z <box> <port>`) before
blaming the app. Symptom of a missing rule: client "Unable to connect" while
server-side everything is green.

## 6. VERIFY — the part people get wrong

The management API lies by omission: `GET /api/v1/servers` (even with the
config api_key as Bearer) can return `{"servers": []}` while everything works.
The gateway's `tools/list` shows only the **router surface** (~12 tools:
retrieve_tools/describe_tool/call_tool_*) because `routing_mode:
"retrieve_tools"` — an empty-looking federation is EXPECTED there too.

**The real proof is a routed retrieve through a sessioned gateway call:**

```bash
# 1. initialize → capture Mcp-Session-Id response header
curl -sD /tmp/h -X POST :25127/mcp -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"probe","version":"0"}}}'
# 2. tools/call retrieve_tools with the session header; responses come back SSE-framed
curl -s -X POST :25127/mcp -H 'Content-Type: application/json' \
  -H 'Mcp-Session-Id: <sid>' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"retrieve_tools","arguments":{"query":"pixel"}}}'
# 3. parse `data:` lines; expect your upstream's namespaced tools:
#    "flotilla:pixel_screenshot", "flotilla:pixel_tap", …
```

Verified end-state on ship day: `query=pixel` → all 10 flotilla tools
namespaced `flotilla:*`; screenshot tool returned a real 348 KB PNG of the
phone. Discovery is async (tool_discovery_interval 30s global / 2m per server)
— give a fresh upstream a minute before declaring failure.

## 7. Fleet surfaces registered this way

| Server | Port | Source |
|---|---|---|
| `taas-telegram` | 25243 | ranch/arroyo/overlord src/taas.ts |
| `gemini-mcp` | 25227 | barn/gemini-mcp server.py |
| `flotilla` | 25245 | ranch/android-fleet flotilla/mcp/server.ts |

## 8. Anomaly scars baked into this guide

- **#20** dead-mirror config: the daemon ran a path nobody edits → always
  `/proc`-verify which config the live process holds.
- **#21** enum guess: invalid protocol string crashed the whole gateway →
  copy working entries, never invent fields.
- **LAN-vs-loopback probe lie** (2026-10-28): server-side success on the LAN
  IP does not traverse the firewall; only client-side probes count.
- **Empty-federation mirage**: `tools/list` = router tools only; verify via
  routed `retrieve_tools`, not tool counts.
