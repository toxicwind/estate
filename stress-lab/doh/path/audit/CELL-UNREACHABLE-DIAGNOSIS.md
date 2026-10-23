# Why the kite cell is "unreachable" / kite never answered — root cause

## Corrected claim
The cell is NOT network-unreachable:
- `muse-1` (100.94.78.109) pings at **0% loss**, active on Tailscale (relay nyc).
- What is refused is only the **service listeners** on the cell: ssh `:22` and kite
  connector `:18301` return **Connection refused** (host alive, service not listening).

## Why kite never answered our audit
Three compounding ESTATE-side failures break the tunnel-restore chain (not a cell/packet problem):

1. **Health endpoint errors.** `http://127.0.0.1:25136/fleet/health` returns **500 Internal
   Server Error (HTML)** on every probe route — never the `{"cell_primary":true}` JSON
   the monitor greps for. So the circuit-breaker can never see the tunnel as healthy.

2. **`tunnel-monitor.sh` health-grep never matches.** It greps `"cell_primary":true`; the
   erroring server never emits it -> monitor always counts the tunnel as down.

3. **`yote-conn` is missing.** `/home/hatch/workspace/bin/yote-conn` (the binary
   `tunnel-monitor.sh` calls to restart the cell tunnel client) does not exist. Even when
   the monitor trips (fails>=3), it cannot run the cell-side restart.

## Consequence
The reverse-tunnel bridge is "one-sided": the outbound hold from the cell stays, but the
inbound listeners (ssh/kite connector) are never re-established because the monitor that
restores them is blind (HTML vs JSON) AND tool-less (missing yote-conn). Kite's connector
stays down -> no response to audits.

## Repair (owned by the bridge/tunnel restore workstream — cf6a10b455 'restore downed bridge backends')
- (a) Fix the `:25136 /fleet/health` server so it returns `{"cell_primary":true|false}` JSON.
  (b) OR make `tunnel-monitor.sh` parse the actual response / tolerate HTML-500.
  (c) Restore a `yote-conn`-equivalent on PATH (or make the restart path not depend on it).
Order: (a) first — the health signal must be decodable before the monitor can act.
