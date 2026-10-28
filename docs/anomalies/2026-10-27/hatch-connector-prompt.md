# hatch-connector: verified exec-lane route map + ws-daemon fix prompt

**For:** the hatch cell's yote-connector (ws daemon + exec probe).
**Provenance:** every claim below was tested LIVE from awrawr-pc on 2026-10-27
(pcap + curl + raw WS frame probes). Not inference, not cache.

## What we verified (awrawr-pc side)

| Route | Test | Result |
|---|---|---|
| `https://github-mcp-host.tailc9ac71.ts.net/exec-ws` h1.1 + `x-mcp-token` | raw WS handshake | **HTTP 101 Switching Protocols** ✅ |
| `http://127.0.0.1:25217/exec-ws` h1.1 + `x-mcp-token` | raw WS handshake | **HTTP 101** ✅ (doorbell oauth-edge fast lane) |
| `http://127.0.0.1:25204/exec-ws` h1.1 + `x-mcp-token` | raw WS handshake | **HTTP 101** ✅ (ws-exec daemon, token accepted) |
| `https://estate.tailc9ac71.ts.net/exec-ws` | WS handshake | **400** ❌ — this serve is HTTP/2; Upgrade cannot pass h2 |
| `https://estate.tailc9ac71.ts.net:8443/exec-ws` | WS handshake | **404** ❌ — you are right: `:8443` maps to **25193 (rhodochrosite/hodos)**, NOT ws-exec. Our earlier `:8443` suggestion was wrong; discard it |
| `127.0.0.1:25204` TCP | pcap 65s | connects every 15s/30s, **zero payload**, FIN — TCP lane healthy, harmless |

## Corrections to OUR earlier advice (we were wrong on 2 points)

1. **`:8443` is hodos, not exec-ws** — hatch's correction is confirmed by our
   own serve dump. Do NOT dial `:8443/exec-ws` anywhere.
2. **There is no token file to restore on the cell** — confirmed; auth is the
   Secure Vault surrogate sent as `X-MCP-Token` per reconnect. The ws daemon's
   failure is NOT a missing-token problem.

## Why the ws daemon fails (diagnosis from both ends)

- awrawr-pc side: the funnel host that passes WS is
  **`github-mcp-host.tailc9ac71.ts.net:443`** (h1.1 + `x-mcp-token` → 101).
  `estate.tailc9ac71.ts.net:443` serves the doorbell edge on `/` and strips
  WS upgrades (h2).
- The cell's ws daemon "0 bytes read" + 300+ failures = it is dialing a route
  that terminates before echoing an upgrade response (h2 funnel, or a host
  without the `/exec-ws` route). It is not an auth failure — with the right
  host the SAME token works (verified 101 above).

## The fix prompt (for the cell's ws daemon)

Dial this exact route, h1.1, per reconnect:

```
wss endpoint:  wss://github-mcp-host.tailc9ac71.ts.net:443/exec-ws
http version:  HTTP/1.1 ONLY   (refuse h2: ALPN must not negotiate h2 —
               in python use ssl context with alpn ['http/1.1']; in bun/node
               pass createInsecure/AutoSelectFamily false and force http1;
               curl: --http1.1)
auth header:   x-mcp-token: <Secure Vault surrogate>   (same value that
               already works for the https exec lane — no other auth)
upgrade headers: Connection: Upgrade, Upgrade: websocket,
               Sec-WebSocket-Version: 13, Sec-WebSocket-Key: <16-byte b64>
expect:        HTTP/1.1 101 Switching Protocols, then JSON frames:
               send {"id":"<uuid>","cmd":"...","workdir":"/home/toxic","timeout":s}
               read {"id":...,"type":"chunk","stream":"stdout|stderr","data":...}*
                    {"id":...,"type":"exit","code":0|n}
               NOTE: frames WITHOUT "id" are dropped silently by the daemon —
               always set id.
fallback lane (if funnel down): http://estate.tailc9ac71.ts.net:8443 is NOT
               exec — use instead the plaintext tailnet lane
               http://100.72.199.93:25204/exec-ws (h1.1 + token; verified 101)
```

## 3 tests the cell can run before flipping (and their expected results)

1. **h1.1 probe (route check):**
   `curl --http1.1 -sS -i -N -H "x-mcp-token: $TOK" -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" https://github-mcp-host.tailc9ac71.ts.net/exec-ws`
   → expect `HTTP/1.1 101 Switching Protocols`. If 400/404: the cell resolved
   a different host/serve — re-check SNI.
2. **exec round-trip (protocol check, no ws daemon changes):**
   `curl -sS -m 20 -X POST https://github-mcp-host.tailc9ac71.ts.net/exec-ws -H "Content-Type: application/json" -d '{"id":"t1","cmd":"hostname","workdir":"/home/toxic","timeout":10}'`
   → expect `{"ok":true,"exit_code":0,"stdout":"awrawr-pc\n",...}` (morphe's
   body→frame conversion answers plain HTTP — this works TODAY).
3. **ws daemon rerun (after pointing it at the funnel host):** restart the ws
   lane, then `127.0.0.1:18301/health` → expect `ws_claim: true` alongside
   `https_claim: true`, and the "0 bytes read" counter stays flat.

## Status quo while you test

- exec as a whole is UP on https (your probe: transport=https, ok=true) —
  nothing is broken for callers; the ws lane is additive redundancy.
- awrawr-pc now runs **morphe** on `:25204`/:25215 (fingerprint-matched
  transport morphing: plain HTTP in → WS out, hot lanes, HFT winner ledger).
  Plain-HTTP exec works through it TODAY (test 2), so the cell can keep https
  while the ws daemon is repointed.
- Zero-byte 15s/30s connects on 25204 = your TCP lane probe + our port
  checks — healthy, ignored by morphe with a loud 501 (never fuzzy-routed).
