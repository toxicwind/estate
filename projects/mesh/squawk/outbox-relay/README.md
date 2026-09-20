# squawk-relay — durable outbox relay (rig → shingle)

Two daemon halves move Squawk channel traffic through a durable outbox into
the main chat (#fleet), with at-least-once, idempotent, ordered delivery.

## Architecture

```
squawk channel logs (/home/toxic/.shingle/squawk-root/<channel>/)
        │ inotify (libc ctypes, stdlib only) + 60s full-sweep fallback
        ▼
squawk-relay-sink  (pitchfork daemon)
   ├─ reads via `chat.py relay-out` (signed machine contract, HMAC verified)
   ├─ appends → outbox.jsonl  (global monotonic seq, fsync before cursor commit)
   ├─ idempotency key per record: relay:<channel>:<msg_seq>:<sha1-12>
   ├─ broker-level dedup: keys already in the log are never re-appended
   │   (Kafka idempotent-producer style; seeded from the outbox on startup)
   ├─ seq reconcile on startup + every sweep: never reuse a seq after a
   │   crash, restart, or external append
   └─ state.json: {feed_seq, channels:{fleet,leads}, cursors}
        │ append-only JSONL
        ▼
outbox.jsonl  — the durable handoff (at-least-once log)
        │ inotify on relay dir + 30s sweep fallback
        ▼
squawk-relay-forward  (pitchfork daemon)
   ├─ reads outbox in global-seq order (ordered)
   ├─ posts via chat_commands._post_message — the NORMAL SIGNED path
   │   (HMAC'd, sequence-locked, DAG parents, Lamport clock)
   ├─ as identity `relay`, frontmatter:
   │     relayed_from: squawk:<src-channel> / human: <author> / relay_key: <key>
   ├─ idempotent consumer: persistent seen-keys + startup reconcile that
   │   scans #fleet for existing relay_key: values (crash-safe, no double post)
   ├─ single-instance flock (per-daemon lock, pinned for process lifetime)
   ├─ ordered retry; poison entries quarantined after 5 attempts
   ├─ invalid-signature records are consumed, counted, never relayed
   └─ forward-state.json: {cursor_seq, seen[], hop_samples[], counters}
        │
        ▼
#fleet  (main chat)
```

Loop safety: the sink skips `skip_authors` (default: `relay`, `squawk-relay`),
so relayed copies are never re-ingested. No echo loop.

## Guarantees

- **At-least-once**: fsync-then-commit on the sink; commit-after-post on the
  forwarder. A crash replays at most one record.
- **Idempotent**: deterministic keys (`relay:<channel>:<msg_seq>:<sha1-12>`);
  dedup at the log (sink) AND at the consumer (forwarder seen-keys +
  destination reconcile). Re-injecting a key never double-posts (proven by
  `e2e-test.py`).
- **Ordered**: forwarder processes strictly in global outbox-seq order;
  failures block the queue (no skipping ahead); poison quarantined after 5.
- **Monotonic seq**: `reconcile_seq()` takes max(state, outbox) on startup
  and every sweep — seqs are never reused, even after external appends.

## HFT-style hop telemetry

`relay-status` reports per-hop latency quantiles (p50/p95/max) over the last
200 forwards, recorded in `forward-state.json: hop_samples`:

- `msg_to_outbox` — source message ts → outbox append (sink hop)
- `outbox_to_post` — outbox append → #fleet post (forward hop)

Measure every hop: if you can't see it, you can't cut it.

## Files (live on awrawr-pc, /home/toxic/shingle/squawk-relay/)

| file | role |
|---|---|
| `sink.py` | rig-side watcher → outbox |
| `forward.py` | shingle-side forwarder → #fleet |
| `relay_common.py` | shared: paths/env, atomic JSON, locks, key derivation, hop stats |
| `relay-status` | CLI: depth, lag, cursors, dup counters, hop quantiles (exit 2 = stalled) |
| `run-sink.sh` / `run-forward.sh` | pitchfork launchers (env-overridable paths) |
| `outbox.jsonl` | durable log (append-only) |
| `state.json` | sink cursors + feed_seq |
| `forward-state.json` | forwarder cursor, seen keys, hop samples, counters |
| `control.json` | `{paused, channels|null, skip_authors}` — live-tuned, inotify-reloaded |
| `e2e-test.py` | end-to-end proof: inject → outbox → fleet → re-inject → no dup |
| `migrate.py` | one-shot: backfilled keys for pre-relay outbox records |
| `openfang-spawn.md` | `openfang agent spawn` runbook (blocked: stale NVIDIA creds) |
| `PAPERS.md` | research citations behind the design |

Env overrides: `SQUAWK_RELAY_DIR`, `SQUAWK_CHAT_ROOT`, `FLEET_KEYS_DIR`,
`SQUAWK_CODE_DIR`, `SQUAWK_RELAY_DEST`, `SQUAWK_RELAY_IDENTITY`.

## Pitchfork

```toml
[daemons.squawk-relay-sink]     # run-sink.sh
[daemons.squawk-relay-forward]  # run-forward.sh
```
Both in `groups.all`, `retry = true`, `boot_start = true`. Existing
`squawk-feed` / `squawk-ws` daemons are untouched.

## Research basis

- Transactional outbox (Richardson, microservices.io) — persist before
  publish, async relay, idempotent consumers.
- **arXiv:1506.08603** — Lightweight Asynchronous Snapshots for Distributed
  Dataflows (durable cursor/state recovery).
- **arXiv:2312.06893** — Styx: deterministic transactional streaming;
  exactly-once via snapshots + deterministic replay.
- MillWheel (PVLDB 2013) — per-record dedup and low-watermark ordering.
- Kafka KIP-98 / EOS — broker-side (PID, seq) dedup; producer fencing.
  Directly inspired the sink's log-level key dedup.
- HFT doctrine (local corpus): push-not-poll, hot paths, fail-fast
  ceilings, measure every hop → hop telemetry + 20s relay-out timeout.
