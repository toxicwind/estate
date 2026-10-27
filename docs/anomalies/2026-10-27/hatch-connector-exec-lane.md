# Hatch connector exec-lane diagnosis — 2026-10-27

Incident: hatch cell reports `connector health at 127.0.0.1:18301` →
`exec_probe: all lanes down: Remote end closed connection without response`
(ms 4250, code 1), `ws_lane_claim: false`, `https_lane_claim: true`.

## Topology (verified live)

```
hatch cell                      awrawr-pc (estate)
────────────────────            ──────────────────────────────────────
progress-watchdog               127.0.0.1:25204  awrawr-ws-exec
  └→ POST 127.0.0.1:18301/exec     (bridge/awrawr_ws_exec.py, WS_PATH=/exec-ws)
      └→ yote-connector :18301   127.0.0.1:25217  doorbell oauth-edge
          └→ lane race:             (WS fast-lane /exec-ws passthrough,
             ws lane | https lane    x-mcp-token required)
             https → funnel
             github-mcp-host.tailc9ac71.ts.net/exec-ws
               └→ tailscale serve --set-path=/exec-ws http://127.0.0.1:25204
```

## What the pcap actually showed (the "bizarre" connections)

`sudo tcpdump -i lo -n "tcp port 25204"` during a 25s window:

```
11:09:36.378983 IP 127.0.0.1.35384 > 127.0.0.1.25204: Flags [S]
11:09:36.378991 IP 127.0.0.1.25204  > ...35384:  Flags [S.]
11:09:36.379002 IP 127.0.0.1.35384 > 127.0.0.1.25204: Flags [.]
11:09:36.379016 IP 127.0.0.1.35384 > 127.0.0.1.25204: Flags [F.]   ← FIN
11:09:36.379249 IP 127.0.0.1.25204  > ...35384:  Flags [F.]
```

Connect → **0 payload bytes** → FIN within 0.04 ms.

Follow-up 60s capture (11:13:06–11:13:54) confirmed the cadence live:
zero-length FIN probes at :06/:21/:36/:51 — the 15s and 30s marks
(pitchfork port checks + the connector's TCP lane). Zero HTTP payload
in the entire window. The server is a WebSocket endpoint; these are
TCP-connectivity probes doing exactly their job. That is a
TCP-connectivity probe (pitchfork's `expected_port = [25204]` check and
the connector's TCP lane), not a failed exec. ws-exec's log confirmed the
same population: ~17,949 `client ... disconnected` lines, one every 30s
on the :22/:52 marks, all zero-byte connects. **TCP lane: healthy.**

The client-visible "Remote end closed connection without response"
comes from the two *real* probe classes below.

## Root causes (both verified with live handshakes)

### 1. HTTPS lane — funnel is HTTP/2, Upgrade cannot pass

`curl --http2 https://github-mcp-host.tailc9ac71.ts.net/exec-ws` with a
WS Upgrade header → `HTTP/2 401` with
`www-authenticate: Bearer resource_metadata=.../.well-known/oauth-protected-resource`.

The funnel terminates HTTP/2; a WebSocket upgrade is HTTP/1.1-only, and
tailscale serve does not tunnel the `Upgrade`/`Connection` hop-by-hop
headers over h2. `x-mcp-token` alone is also not accepted by the
gateway's OAuth bearer wall. **This lane cannot work as configured** —
it needs either (a) an OAuth bearer token from the doorbell issuer, or
(b) the raw tailnet route (below).

### 2. WS lane — works, but hatch's copy must send the token

Direct HTTP/1.1 against the oauth-edge fast lane:

```
curl --http1.1 -H "Connection: Upgrade" -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: ..." \
     -H "x-mcp-token: $(cat ~/.yote_connector_token)" \
     http://127.0.0.1:25217/exec-ws
→ HTTP/1.1 101 Switching Protocols   (Sec-WebSocket-Accept correct)
```

Also valid against `:25204` directly (same server, same token check —
`read_tokens()` accepts `~/.awrawr_mcp_token`,
`~/.yote_connector_token`, `~/.shim_connector_token`; all three exist
here, 64 bytes each, 0600).

## Verdict

- Server side (awrawr-pc): **healthy**. The 30s zero-byte connects are
  TCP probes doing their job. `101` on a correct-token HTTP/1.1
  handshake; `400` on garbage; silent close only on empty/EOF clients.
- Hatch side: the connector's **ws lane claims down** because it is not
  sending `x-mcp-token` (or its token copy drifted — the knowledgebase
  records the 2026-09-20 host re-provision that wiped
  `/etc/hatch/env.override` and credentials; re-rendered creds may not
  have re-synced the connector token). The **https lane claims up** but
  actually 401s at the funnel because of HTTP/2 + OAuth bearer mismatch.

## Recommended fixes

1. Hatch: restore `~/.yote_connector_token` (64-byte value, must match
   awrawr-pc's `~/.yote_connector_token` — same secret, two boxes) and
   send it as `x-mcp-token` on the WS handshake. Verify from hatch:
   `curl --http1.1 -H "x-mcp-token: $(cat ~/.yote_connector_token)" ...
   https://<estate-host>:8443/exec-ws` — note the **:8443 tailnet-only**
   serve listener tunnels h1.1 correctly, unlike the :443 funnel.
2. Preferred lane order for the connector after the fix:
   `ws (tailnet :8443 or funnel-free tailnet IP) → https (OAuth bearer)`.
   The funnel :443 path should be a last resort for WS.
3. Optionally: teach the connector to treat "connected then closed with
   0 bytes" as `tcp_ok`, distinct from `exec_ok`, so a healthy TCP lane
   no longer masks as "all lanes down" noise.
