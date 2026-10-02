# Yote deploy bundle — post-apply verification (run on yote)

Run these after `apply.sh --apply`. Tailnet DNS name used throughout:
`github-mcp-host.tailc9ac71.ts.net`. Always use the DNS name (correct SNI);
probing the raw tail IP with SNI=localhost produces misleading TLS alerts.

Each check is marked **[BLOCKING]** (must pass before calling the deploy good)
or **[INFO]** (context; a mismatch is noted, not a failure).

---

## 1. Serve map — [BLOCKING for routing, details [INFO]]

```
sudo tailscale serve status
```

Expect the 8-route map (from 2026-09-20 baseline):

| Path              | Backend                |
|-------------------|------------------------|
| /                 | 127.0.0.1:8443         |
| /mcp              | 127.0.0.1:8377/mcp     |
| /exec-ws          | 127.0.0.1:8379/exec-ws |
| /gemini-mcp       | 127.0.0.1:8378/mcp     |
| /squawk-ws        | 127.0.0.1:25147/squawk-ws |
| /squawk-feed/seq  | 127.0.0.1:25135/squawk-feed/seq |
| /whatsapp-webhook | 127.0.0.1:25146/webhook |
| /files            | 127.0.0.1:34567 (tailnet-only host awrawr-pc-1) |

**[BLOCKING]**: `/exec-ws` and `/squawk-ws` must be present. Others [INFO].

## 2. Daemon — [BLOCKING]

```
pitchfork list
```

`awrawr-ws-exec` must show as **running**. If it shows errored/exited, do not
restart it from this checklist — that is a repair action for the parent to
decide (yote-fix.sh v3 is the repair path).

## 3. Route probes via tailnet DNS — [BLOCKING where noted]

Use curl against the DNS name (correct SNI). A plain HTTP GET to the WS
route should return **400** — that means the route is alive and the WS
server is rejecting non-upgrade requests, which is the expected behavior.

```bash
curl -sS -o /dev/null -w '%{http_code}\n' \
  https://github-mcp-host.tailc9ac71.ts.net/exec-ws
# expect: 400  [BLOCKING] — route alive, server responding
```

502 is expected ONLY where the backend is known-down:

```bash
curl -sS -o /dev/null -w '%{http_code}\n' \
  https://github-mcp-host.tailc9ac71.ts.net/mcp
# expect: 502  [INFO] — backend 127.0.0.1:8377 is known-down (baseline)
```

Any 502 on `/exec-ws` is **[BLOCKING]** — it means port 8379's backend is
down even though the route exists. Any connection-refused/TLS alert is
**[BLOCKING]** — re-check you used the tailnet DNS name, not the raw IP.

## 4. WSS handshake — [BLOCKING]

Open a websocket to the exec route with a valid `X-MCP-Token` header
(the token in `~/.awrawr_mcp_token` on yote). Expect **HTTP 101 Switching
Protocols**. Known non-passes:

- **401** → genuine broker/yote token mismatch: mint a new token on yote,
  enter it via the `custom.awrawr-mcp` vault page, and let the daemon
  re-fetch on reconnect (baseline fix 2026-09-19 23:46 MDT).
- **502/503** → backend down; see check 3.
- Stale `~/.cache/awrawr-ws-down` flag (client-side, 15s TTL) makes the
  *client* skip WS and fall back to HTTPS 502: `rm` the flag or wait 15s
  and retry before concluding the server is down.

## 5. Sanity — [INFO]

- `ls -l /home/toxic/yote-ops/` shows both scripts executable.
- `sha256sum` of the installed files matches MANIFEST.txt.
- `awrawr_ws_exec.py.new` exists side-by-side; the live
  `awrawr_ws_exec.py` was NOT overwritten by this bundle.
- No squawk process was touched (`pgrep -fa squawk` still shows the
  server, client, and watchdog running).
