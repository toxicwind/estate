# Lane Heartbeat Staleness Thresholds

Read-only detection policy for lane liveness in
`/home/toxic/sovereign/hatch/agents/ember/coord/lanes/*.json`.

## Constants

| Name | Value | Rationale |
|---|---|---|
| `HEARTBEAT_EXPECTED_INTERVAL` | 180 s | The Nightjar + sibling persona poll crons run on a 3-minute cadence and refresh lane heartbeats. |
| `ACCEPTABLE_HEARTBEAT_PAUSE` | 1 interval (180 s) | Suspicion accrues only after 6 min of silence — cron scheduling jitter on shared cells is noise, not death (cf. Akka `acceptable-heartbeat-pause`). |
| `SUSPECT_AFTER` | 2 intervals (12 min) | Memberlist-style suspect-before-dead: a lane this quiet is flagged `suspect`, not `dead`. |
| `STALE_AFTER` | 10 intervals (30 min) | Unrefuted suspicion becomes `stale` — escalate to the coordinator. |
| `COLD_START_EXEMPTION` | < 3 recorded heartbeats | φ-style detectors need warmup samples; a brand-new lane is never suspect (cf. Cassandra warmup). |

## States

- `alive`: age < 6 min.
- `suspect`: 6 min ≤ age < 30 min. The owning lane gets one poll cycle to refute: a fresh heartbeat clears suspicion automatically, because suspicion is *derived* from the heartbeat field, never stored.
- `stale`: age ≥ 30 min. Report to the coordinator by exception.

## Reason codes

Staleness reports carry a reason, modeled on Erlang's `nodedown_reason`:

- `heartbeat_timeout` — the lane's `heartbeat` field is old; the lane agent is presumably not refreshing it.
- `poll_cron_missed` — the poll cron's own last run is older than 2× the interval; the *observer* is the slow party (cf. Lifeguard local-health awareness). Check this before blaming the lane.
- `bridge_unreachable` — the lane file could not be read at all; transport problem, not lane death.

## Maximum staleness bound

The poll crons perform a full-state sync each cycle (memberlist push/pull analog), so
maximum presence staleness = one poll interval + file-write latency (~3–4 min).
Anything older than `STALE_AFTER` is a real anomaly, not gossip lag.

## Consistency rule

Every poll cron must use the *same* constants above, or suspicion scores are not
comparable across reporters. This file is the single source of truth.
