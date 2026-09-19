# fleet-watchdog v2

Lane-7-owned fleet presence + rollover watchdog. Durable on awrawr-pc;
the cell only runs the driver.

## Layout (awrawr-pc: `/home/toxic/sovereign/tools/fleet-ops/fleet-watchdog/`)

- `sweep.py` — the watchdog. Runs **on awrawr-pc** (sovereign-chat is
  local at 127.0.0.1:25120, no bridge hop). Heartbeats lane-7, reads
  `/v1/presence` (server timestamps: per-agent `last_heartbeat`, response
  `ts`, `ttl_s`), attributes presence via `lane_manifest.json`, checks
  rollover identity blocks in the durable mirror **against the manifest**,
  diffs against `state.json`, posts **one** consolidated fleet-room message
  only on transitions.
- `lane_manifest.json` — canonical lane identity manifest: chat_id prefix
  → lane (+ full chat_id). The mirror is checked against this, so a lane
  whose whole block disappears from the mirror is **reported, never
  silently dropped** (the old mirror-parsed map had that blind spot).
  Regenerate with `sweep.py --gen-manifest` after a verified rollover
  update, then commit it.
- `driver.sh` — cell-side driver for the platform scheduler: syncs
  `/home/hatch/fleet-rollover.md` → durable mirror (best effort), then
  execs the sweep. The scheduler body is a one-liner fetching this file.
- `state.json` — schema v2: per-lane `{block, live, last_seen_ts,
  last_transition, last_transition_ts}`, `last_sweep_ts`, capped
  `transitions` log (50). v1 state migrates automatically (booleans
  carried, `last_seen_ts` unknown pre-v2, `last_sweep_ts` seeded from
  the v1 file mtime so the gap detector stays honest).
- `fleet-rollover.md` — durable mirror of the lane-adoption doc.
- `test_decide.py` — synthetic transition scenarios against the pure
  `decide()` brain plus the blind-spot checks (`check_blocks` against a
  gutted mirror). Run on awrawr-pc: `python3 test_decide.py`.

## Cadence

60s sweep interval. sovereign-chat presence TTL is 120s: the 60s sweep
keeps the lane-7 heartbeat alive continuously, and the gap detector
(> 2× interval = 120s) pages only after two consecutive missed sweeps —
a real scheduler outage, not jitter.

## Paging rules (change-only; steady state = silence)

- live→stale: `lane-N STALE (last heartbeat Xh Ym ago)`
- stale→live: `lane-N LIVE again after X dark`
- rollover block lost / restored (header + chat_id prefix both required)
- watchdog gap: no sweep for > 2× interval → `watchdog gap: no sweep for X — resumed`
- watchdog blind: manifest + mirror both unreadable → pages at most hourly,
  no fabricated transitions
- first run posts the baseline; every sweep heartbeats (plane TTL mechanism)

## Runbook

- Manual sweep: `driver.sh` from the cell (or the scheduled job does it).
- Brain tests: `python3 test_decide.py` on awrawr-pc (exit 0).
- Regenerate manifest: `python3 sweep.py --gen-manifest` on awrawr-pc,
  verify the 8 lanes, commit.
- Logs: the sweep prints one JSON line per run (ok, live/stale sets,
  pages, posted, transitions, map_source).

## Known limitations

- Last-seen for stale lanes comes from this watchdog's own observation
  history (the server exposes `stale_count` but no per-stale-agent
  timestamps). A lane never seen live by v2 reports "first sighting"
  on recovery instead of a downtime duration.
- Dead-man's switch: if the sweep itself dies, nobody pages until it
  resumes (then the gap page fires). A second independent monitor
  (lane-8's bridge health or equivalent) is the cross-check — not built here.
- The rollover mirror is synced cell→awrawr-pc by the driver each run;
  lanes still append to the cell original.
