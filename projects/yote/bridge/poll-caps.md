# Capped log-tail polling — cap design

Observability for bridge workers starts as **polling tail**
(`agent.py log <id> --tail N`). The enforcer is
`bin/poll_log.py`: every poll attempt passes the caps BEFORE any bridge
traffic. Calls that fail a cap are **skipped, not queued** (exit 2, the
bridge is never touched).

## Enforced caps

| cap | value | meaning |
|---|---|---|
| `MIN_POLL_INTERVAL_SEC` | 10 s | minimum gap between two served polls of the same worker (burst gate → max 0.1 polls/s/worker) |
| `MAX_POLLS_PER_MINUTE` | 5 | sliding 60-second window per worker (sustained ≤ 0.0833 polls/s/worker; dominates the interval gate at scale) |
| `DEFAULT_TAIL_LINES` | 40 | default `--tail` |
| `MAX_LINE_CHARS` | 500 | per-line truncation |
| `MAX_POLL_BYTES` | 20 KiB (20480) | per-poll byte budget incl. truncation markers |

## Derived bridge budget (worst case, caps fully saturated)

- per worker: 5 polls/min × 20 KiB = **100 KiB/min ≈ 1.7 KiB/s**
- 10 workers: 0.8 polls/s, ~17 KiB/s
- 50 workers: **4.2 polls/s, ~83 KiB/s, ~5 MiB/min**
- 200 workers: 16.7 polls/s, ~330 KiB/s, ~20 MiB/min

Each poll is one `exec.py` round trip (HTTPS ~0.6–7 s wall, WS ~0.2 s warm).
The caps keep poll volume orders of magnitude under both the 200 k-char
output cap and the bridge's serial command capacity. The interval gate
additionally serializes impatient callers: concurrent `poll_log.py`
invocations for the same worker stamp `last_poll_ts` before the bridge
call, so a second concurrent caller sees the gate closed.

## State

- `~/.cache/capped-poll/<worker-id>.json` — `last_poll_ts`, trailing-60s poll timestamps
- `~/.cache/capped-poll/<worker-id>.measurements.jsonl` — one row per
  attempt: ts, served/skip reason, latency_ms, bytes. Evidence for audits.

## What the caps do NOT cover (future work)

- Cross-worker global ceiling (a fleet-wide token bucket) — per-worker caps
  bound the fleet linearly; a global limiter is the next upgrade if worker
  counts grow past ~200.
- WS push — gated by the transport-health checklist
  (`transport-health-checklist.md`); no new daemon, only the existing
  `ws_daemon.py` single persistent connection.
