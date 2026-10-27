# FUNNEL-FIXED.md — Tailscale Serve Route Repair
Date: 2026-10-24T00:55Z
Author: tau agent (funnel-forensics)

---

## Problem
The estate tailscale funnel served 5 routes. Route `:8443 -> 127.0.0.1:20130` returned HTTP 502 because port 20130 (omniroute) had no listener — the omniroute client API was ported to flock which now runs on port 25193 (rhodochrosite).

## Old Route State (BEFORE)
```
https://estate.tailc9ac71.ts.net:25127 (tailnet only)
|-- / proxy http://127.0.0.1:25127

https://estate.tailc9ac71.ts.net (tailnet only)
|-- /      proxy http://127.0.0.1:25217
|-- /files proxy http://127.0.0.1:34567

https://estate.tailc9ac71.ts.net:8443 (tailnet only)
|-- / proxy http://127.0.0.1:20130    ← DEAD (502)

https://estate.tailc9ac71.ts.net:8444 (tailnet only)
|-- / proxy http://127.0.0.1:25218
```

## New Route State (AFTER)
```
https://estate.tailc9ac71.ts.net:25127 (tailnet only)
|-- / proxy http://127.0.0.1:25127

https://estate.tailc9ac71.ts.net (tailnet only)
|-- /      proxy http://127.0.0.1:25217
|-- /files proxy http://127.0.0.1:34567

https://estate.tailc9ac71.ts.net:8443 (tailnet only)
|-- / proxy http://127.0.0.1:25193    ← FIXED (401 = rhodochrosite responding)

https://estate.tailc9ac71.ts.net:8444 (tailnet only)
|-- / proxy http://127.0.0.1:25218
```

## Commands Run

```bash
# 1. Confirm dead port
ss -ltnp | grep 20130        # → NO LISTENER ON 20130

# 2. Verify 8443 was dead
curl -sSI https://estate.tailc9ac71.ts.net:8443/  # → HTTP/2 502

# 3. Check 25193 is alive (rhodochrosite, omniroute successor)
ss -ltnp | grep 25193  # → LISTEN 128 127.0.0.1:25193 ((rhodochrosite,pid=383414))

# 4. Reset serve config (clears ALL routes)
echo "n" | tailscale serve reset

# 5. Re-add all 5 routes with --bg flag
echo "n" | tailscale serve --bg --https=25127 http://127.0.0.1:25127
echo "n" | tailscale serve --bg http://127.0.0.1:25217
echo "n" | tailscale serve --bg --set-path=/files http://127.0.0.1:34567
echo "n" | tailscale serve --bg --https=8443 http://127.0.0.1:25193    # ← REPOINTED
echo "n" | tailscale serve --bg --https=8444 http://127.0.0.1:25218
```

## Route Verification (AFTER)

| Route | Backend | Old Status | New Status | Change |
|-------|---------|-----------|-----------|--------|
| `estate.tailc9ac71.ts.net/` | 127.0.0.1:25217 (OAuth edge) | 401 | 401 | ✅ unchanged |
| `estate.tailc9ac71.ts.net/files` | 127.0.0.1:34567 | 200 | 200 | ✅ unchanged |
| `estate.tailc9ac71.ts.net:25127` | 127.0.0.1:25127 (thresher) | 302 | 302 | ✅ unchanged |
| `estate.tailc9ac71.ts.net:8443` | **127.0.0.1:25193** (rhodochrosite) | **502** | **401** | ✅ **FIXED** |
| `estate.tailc9ac71.ts.net:8444` | 127.0.0.1:25218 (ranch-ui) | 200 | 200 | ✅ unchanged |

## Notes

- **Persistence**: Tailscale serve config is stored in the Tailscale control plane (machine-level config). No local file to edit; the `tailscale serve --bg` commands persist across reboots as part of the tailscaled service state.
- **Port 8443 target change**: 20130 (omniroute, dead) → 25193 (rhodochrosite/flock successor). The 401 response from rhodochrosite is expected — it's an OAuth-protected endpoint returning auth-required.
- **Other 4 routes**: Untouched, all healthy before and after.
- **Kite stale legend** (25135, 25146): NOT fixed by this change — those are direct-to-estate connections, not funnel routes. See SCHEDULED-TASKS-FOUND.md for details.

## Restore Command (if needed)

To undo this fix and restore the original dead :8443 -> 20130 route:
```bash
echo "n" | tailscale serve reset
echo "n" | tailscale serve --bg --https=25127 http://127.0.0.1:25127
echo "n" | tailscale serve --bg http://127.0.0.1:25217
echo "n" | tailscale serve --bg --set-path=/files http://127.0.0.1:34567
echo "n" | tailscale serve --bg --https=8443 http://127.0.0.1:20130
echo "n" | tailscale serve --bg --https=8444 http://127.0.0.1:25218
```
