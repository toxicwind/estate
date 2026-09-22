# Bridge bootstrap v2 — design

Lane: `bridge-bootstrap-v2` · Owner: coordinator (Amani, acting Ember)
Status: design draft · 2026-09-21

## Problem

The v1 bridge (`gear/awrawr-mcp`) works, but every fresh cell pays for it
three times:

1. **Cold start is sequential.** After a cell reprovision there is no
   `~/workspace/bin`, no connector, no session. First contact does
   surrogate fetch → ws_daemon lazy start → WS handshake → session check →
   dispatch, in series. A fresh cell looks "bridge down" for its first
   seconds/minutes, and that misdiagnosis has already caused real damage
   (the Hearth progress-watchdog killed a healthy local connector 3× on
   2026-09-21 because it read an end-to-end `ok:false` as a dead connector;
   Ember's 21:18 fix made restart conditional on the local socket being
   unreachable).
2. **Health is implicit.** v1 knows "WS won the last 10 races" and
   "https-down flag is 40s old", but there is no shared, queryable health
   record. Every consumer re-derives health from its own observations, and
   watchdogs guess — see (1).
3. **N parallel mechanisms.** exec-over-WS, exec-over-HTTPS (per-call HFT
   race), xfer-over-WS (*its own separate connection*), squawk-relay
   outbox, fleet-chat HTTP. Five auth/health/reconnect state machines for
   one logical pipe between cell and awrawr-pc.

v2 fixes all three: **first-connection burst** (one parallel bootstrap),
**explicit transport health** (one shared record, three failure classes),
**single-bus consolidation** (one multiplexed connection).

## 1. First-connection burst

New entrypoint `bin/bridge-burst.py` (runs on cell start, idempotent,
re-runnable as a refresh):

- Fires all independent first-contact work **concurrently**:
  1. surrogate fetch (`custom.awrawr-mcp` via dynamic_credentials)
  2. ws_daemon singleton ensure + WS handshake (`/exec-ws`)
  3. HTTPS MCP session establish (cached session id)
  4. remote sysinfo/vitals snapshot (`exec.py --sysinfo` equivalent)
  5. fleet seq + own lane file read (coordination state)
- Merges results into a **bootstrap manifest**
  `~/.cache/awrawr-bootstrap.json`:
  `{ts, cell_id, steps: {surrogate: {ok, ms}, ws: {...}, https: {...},
  sysinfo: {...}, coord: {...}}, lanes_ready: ["ws","https"], fleet_seq: N}`
- Clients read the manifest instead of probing. Partial success is
  normal: unready lanes are recorded, and clients route around them from
  the manifest rather than discovering the outage per-call.
- Manifest TTL = cell lifetime; `bridge-burst --refresh` re-runs the
  concurrent probe set.

Non-goals: it does not replace per-call dispatch; it only makes the
*first* call fast and honest.

## 2. Transport health (explicit model)

One shared record, `~/.cache/awrawr-transport-health.json`, updated by
every call plus a lightweight prober:

```
transports: {
  "ws":    {state, last_ok_ts, consec_fail, p50_ms, p95_ms, last_error},
  "https": {state, last_ok_ts, consec_fail, p50_ms, p95_ms, last_error},
  "tunnel":{state, ...}   # AWRAWR_TUNNEL_HOST override path, when set
}
state ∈ {healthy, degraded, down}
```

**Three failure classes are first-class** (encodes the 2026-09-21 Hearth
postmortem as an invariant, not a patch):

| class | signal | allowed response |
|---|---|---|
| `LOCAL_DEAD` | unix socket unreachable / daemon lock uncontested-but-absent | restart local connector |
| `TRANSPORT_DOWN` | lane connect/handshake fails, local side fine | fail over to other lane, mark down with TTL |
| `REMOTE_UNHEALTHY` | connector alive, end-to-end probe `ok:false` | **absorb**: log, no restart, no failover storm |

Watchdogs may restart **only** on `LOCAL_DEAD`. `REMOTE_UNHEALTHY` must
never trigger a restart — this is the exact mistake Ember patched at
21:18, now structural.

Active probing (cheap, slow cadence — not per call):
- WS: application-level `{"type":"health"}` round-trip alongside the
  existing 25s PING frames.
- HTTPS: session-validity check every ~5 min, not per dispatch.

Fleet visibility: expose the health record through the command-center
funnel (extend `/ops/api/status` or add `/ops/api/bridge-health`), so
coordinator agents and dashboards read bridge health **without exec**.

## 3. Single-bus consolidation

Collapse the N mechanisms onto **one persistent multiplexed wss bus**:

- Extend `ws_daemon`'s single connection into a typed-channel bus:
  `exec`, `xfer`, `events` (fleet/squawk notifications), `health`.
  One TLS handshake, one auth, one reconnect/backoff state machine, one
  health record.
- **HTTPS is demoted** to bootstrap + fallback-only (used before the bus
  is up, and in environments where WS cannot connect). It stops being a
  per-call race competitor.
- **Double-execution protection moves to idempotency keys.** Every bus
  message carries an idempotency key; the server dedups. This replaces
  the v1 pre/post-dispatch heuristic ("never re-dispatch after dispatch")
  with a guarantee that survives reconnects: at-least-once delivery +
  server-side dedup = exactly-once effect.
- `xfer`'s "own separate connection" goes away — file transfer becomes
  the `xfer` channel on the bus (binary frames already exist in
  `wsframe.py`).

Wire sketch (bus frame envelope):

```
{bus: 2, chan: "exec"|"xfer"|"events"|"health",
 idem: "<uuid>", seq: N, payload: {...}}
```

`events` channel also carries fleet-chat notifications cell-ward, which
lets cell agents **subscribe instead of poll** (PROTOCOL.md rule 4 says
"readers poll" — the bus gives us the primitive to relax that where it
pays, without breaking pollers).

## Migration

- `AWRAWR_BUS=1` gates the bus client; v1 HFT-race path stays default.
- Canary per the established canary-plan pattern: shadow sidecar (bus
  runs alongside, results compared, no traffic switched) → Kayenta-style
  judge (score ≥ 0.90 on latency/correctness vs v1) → flip → 24h soak →
  promote. One-command rollback = unset the flag.
- v1 race code remains as the fallback implementation indefinitely
  (fallback is a feature: it is the bootstrap path when WS is down).

## Open questions (for Chris / fleet)

1. Should the bus server live in the existing `awrawr-mcp` process
   (port 25198 side) or as its own pitchfork daemon? Lean: extend the
   existing `/exec-ws` handler — one fewer daemon to supervise.
2. Fleet-chat `events` fan-out: does the fleet want cell-ward push, or
   is poll-every-60s fine for now? (Bus makes push cheap; not required
   for v2.)
3. `bridge-burst` as a pitchfork-managed cell-start hook vs. a wrapper
   every bridge client calls: prefer the hook (one place), with clients
   falling back to "burst on first use" if the manifest is absent.

## Coordination

- Lane file: `coord/lanes/bridge-bootstrap-v2.json` (this lane).
- Claim before implementing: `coord/claims/bridge-bus.json`
  (`claimed_by`, `claimed_at`, `ttl_s`) — avoids two agents building the
  bus concurrently.
- Progress appended to `coord/log.jsonl` (append-only), never rewritten.
