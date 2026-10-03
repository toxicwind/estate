# Hot Reload + Blue-Green Deploy for Yote Daemons

## Problem

- Pitchfork `restart` is stop-then-start (COLD). Services go down during deploys.
- squawk-feed / squawk-ws have zero signal handling — SIGTERM kills mid-request.
- No health checks, no rollback. A bad deploy = outage.
- Cell shims (`squawk`, `yote-conn`) fail hard when the bridge/server is down.

## Architecture: Proxy + Blue-Green

```
                    ┌─────────────────────────────────┐
  cell shims ──────►│  stable proxy port (e.g. :25147) │──┐
                    └─────────────────────────────────┘  │
                                                         ▼
                    ┌──────────┐  health   ┌──────────┐
                    │  BLUE    │◄──────────│  GREEN   │
                    │ :25148   │   cutover  │ :25149   │
                    │ (live)   │───────────►│ (new)    │
                    └──────────┘            └──────────┘
```

The proxy always listens on the stable port. Backends come and go behind it.
Clients never see a deploy. This is what makes it "impossible break."

## Components

### 1. `proxy.py` (yote)
A minimal TCP proxy that forwards a stable port to the current active backend.
- Hot-swappable backend via a control socket or file watch.
- No dependencies beyond stdlib.
- Handles HTTP and raw TCP (squawk-ws is WebSocket, squawk-feed is HTTP).

### 2. `bluegreen.py` (yote)
Deploy orchestrator. Given a service spec:
1. Start GREEN on the idle port.
2. Poll `/health` until healthy or timeout.
3. On healthy: tell proxy to cut over to GREEN. GREEN becomes BLUE.
4. Drain old BLUE: SIGTERM, wait for connections to close (graceful), SIGKILL after timeout.
5. On unhealthy or any error: kill GREEN, BLUE keeps serving. **Automatic rollback.**

The service is NEVER down: at every step, at least one healthy backend is behind the proxy.

### 3. `graceful.py` (yote)
Mixin for Python servers:
- SIGTERM/SIGINT handler: stop accepting, drain in-flight with timeout, exit clean.
- `/health` endpoint helper: 200 when ready, 503 during shutdown.
- Designed to be dropped into squawk-feed / squawk-ws with minimal changes.

### 4. Shim resilience (cell)
- `yote-conn`: retry with exponential backoff on transient failures.
  Safe to retry: "bridge not connected" (pre-dispatch, never executed).
  NEVER retry: "bridge response timeout", "bridge reconnecting" (may have executed).
- `squawk`: `bridge_resilient()` wrapper with backoff. Failed sends go to a
  local outbox (`~/.cache/squawk/outbox/`); `squawk outbox-flush` retries them.
  Reads already have lane-racing + stale cache; writes get the outbox.

## Service specs

Each service gets a JSON spec:
```json
{
  "name": "squawk-ws",
  "stable_port": 25147,
  "blue_port": 25148,
  "green_port": 25149,
  "health_path": "/health",
  "health_timeout_s": 30,
  "drain_timeout_s": 15,
  "start_cmd": ["python3", "/home/toxic/estate/ranch/squawk/relay/squawk_ws_server.py"],
  "proxy_cmd": ["python3", "/home/toxic/estate/hotreload/proxy.py", "25147"]
}
```

## Rollout

1. Deploy `proxy.py` + `bluegreen.py` + `graceful.py` to `/home/toxic/estate/hotreload/` on yote.
2. Patch squawk-feed / squawk-ws with `graceful.py` mixin (add /health, SIGTERM).
3. Start proxy on stable ports, register existing backends as BLUE.
4. Future deploys go through `bluegreen.py`.
5. Update cell shims (this is local, done first).
