# BENCH-RADAR

Resident, reactive regression-detection service for the tau nightly benchmark
(cron `tau-bench-nightly`, daily@03:30 America/Denver → `/home/toxic/bench-run.log`).

Nobody reads the log. This service does — and pages the moment a suite degrades,
instead of letting anomalies sit unnoticed for days.

## Interface (reactive push, not polling)

- `GET http://127.0.0.1:25181/health` — liveness
- `GET http://127.0.0.1:25181/status` — latest night, per-suite verdicts, open
  regressions with evidence
- `WS  ws://127.0.0.1:25181/live` — snapshot on connect, then
  `{type:"regression", event}` pushed the moment a regression is detected
- `GET /events` — last 50 events (newest first)
- `POST /scan` — force an immediate log rescan (returns new events found)

## Detection

- **Hard rules (page immediately):** suite `exit != 0`; router-models
  `nonempty=0/N` (backend returning empty); title-models `warmMeanMs=0` while
  `coldMs>0` (warm runs not executing); suite section missing vs the previous
  complete run. `SKIP` lines (e.g. ollama-unreachable) are informational only.
- **Soft regressions:** rolling-median + MAD z-score per numeric series
  (z ≥ 3.5 and ≥25% relative move, ≥4 history points; ≥40% move on short
  history). Change-point aware: a soft regression must degrade **2 consecutive
  runs** before paging — first sight only arms a pending watch. New series
  names get the same treatment: 2 consecutive degraded runs or a hard anomaly.
- **Dedup:** one event per (suite, series, metric, night).

## State

`state/` holds `events.jsonl` (durable, append-only), `evaluated.json`
(already-scored run|suite pairs), `pending.json` (armed 1-night watches),
`alerts.log` (notify.sh output). Backfill runs on boot record historical
events with `"backfill": true` and never fire the notify hook — no first-boot
spam, but history is visible in `/status`.

## Alerting

`notify.sh` fires once per new event (argv $1 = event JSON). Default: appends
to `state/alerts.log` and best-effort POSTs to fleet-chat
(`FLEET_CHAT_URL`, room `BENCH_RADAR_ROOM` default `ops`,
`BENCH_RADAR_AGENT_ID` default `bench-radar`). The lane wires the room.

## Run

Pitchfork: `pitchfork start bench-radar` (stanza in `sovereign/pitchfork.toml`).
Env: `BENCH_RADAR_PORT` (default 25181), `BENCH_RADAR_LOG`
(default `/home/toxic/bench-run.log`), `BENCH_RADAR_STATE` (default
`tools/bench-radar/state`), `BENCH_RADAR_POLL_MS` (default 10000),
`BENCH_RADAR_BACKFILL=1` to page on history (default records only).

Mesh: registered as `bench-radar` in `src/lib/ghas-mesh-features.ts`
(service IDs, catalog, dependency graph) with `BENCH_RADAR_PORT` in
`config/ports.env`.
