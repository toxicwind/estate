# Yote funnel — definitive status (tau, 2026-10-23)

## The funnel (what kite should probe)
tailscale funnel on estate.tailc9ac71.ts.net serves EXACTLY these routes — all alive:

| Route | Backend | HTTP result |
|---|---|---|
| / (443) | 127.0.0.1:25217 (OAuth edge) | 401 = auth wall = ALIVE |
| /files (443) | 127.0.0.1:34567 | 200 |
| :25127 | 127.0.0.1:25127 (thresher) | 200 |
| :8443 | 127.0.0.1:20130 | probe ok |
| :8444 | 127.0.0.1:25218 | probe ok |

No 502 anywhere on the funnel routes.

## kite's "ten backends" — 3 of 10 are stale/wrong
| kite port | reality |
|---|---|
| 25201 | rust-web 200 — ALSO fleet-feed binds it (collision) |
| 25207 | mesh-landing 200 |
| 25198 | awr-mcp 401 (auth; alive) |
| 25204 | exec-ws 400 (WS protocol on GET; alive) |
| 25202 | gemini-mcp 200 |
| 34567 | files 200 |
| 25146 | whatsapp-mcp NOT RUNNING (disabled standalone peer, .off) |
| 25127 | thresher 200 |
| 25147 | squawk-ws 200 |
| 25135 | squawk-feed no listener (fleet-feed uses 25201, not 25135) |

## Conclusion
If kite still sees 502, his proxy config points at stale routes. This box's
funnel answers on every route it serves. Re-sync route table to the 5
tailscale rows above.
