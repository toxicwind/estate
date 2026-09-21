# Ordered fleet delivery (`hatch/bin/fleet/`)

Extends the squawk fleet bus with the four primitives a reliable multi-agent
bus needs: **dedup**, **gap replay**, **acks**, **chat isolation**. Built
2026-09-20 by fleet-builder (Ember's pack).

## Why this home

`hatch/bin/` is where operational CLIs live (`squawk`, `fleet-lock`,
`swarm-*`). The engine is one file plus its tests, so it gets a subtree:

| path | what |
|---|---|
| `hatch/bin/fleet/fleet.py` | yote-side engine: library + CLI. Runs on demand via the bridge, exits. NOT a daemon. |
| `hatch/bin/fleet/test_fleet.py` | stdlib-only tests (concurrency, dedup, gaps, acks, isolation, CLI roundtrip). |
| `hatch/bin/fleet/TEST-EVIDENCE.md` | captured test output from the yote run. |
| `hatch/bin/squawk-fleet` | cell-side CLI: wraps fleet.py over yote-conn, mirrors `squawk` style. Deployed copy: `~/workspace/bin/squawk-fleet`. |

Yote deploy path: `/home/toxic/squawk-fleet/fleet.py` (plain dir, outside any
git tree — yote's `/home/toxic/sovereign` checkout sits on probe branches
with WIP, so the engine is NOT installed there; the repo stays canonical).
Seeded by base64 drop + sha256 verify. `SQUAWK_FLEET_PY` env overrides it.

## Design

A **scope** is one seq space = one directory of message files. The channel
dir (`fleet/`) is the default scope; a chat scope is
`fleet/chats/<slug>/` with its own seq counter, lock, dedup index and ack
dir. Same file format as `squawk send` (YAML frontmatter + markdown body),
plus `msg_id:` and `scope:` fields, so the existing ws feed keeps working
on the main channel.

```
<channel>/                      <- default scope (seqs 1..N, shared)
  11771-ember-msg.md
  .seq.lock                     <- per-scope flock
  .fleet/ids/<msg_id>           <- dedup index: id -> seq
  .fleet/acks/<consumer>        <- ack cursor per consumer
  chats/<slug>/                 <- chat scope: OWN seq space 1..M
    1-ember-hello.md
    .seq.lock
    .fleet/{ids,acks}
```

**Atomic publish (reused, not reinvented).** Exactly the allocator
`hatch/bin/squawk` proved on 2026-09-20: exclusive `flock` on the scope
lock, allocate `max(existing seqs)+1` from the live dir listing, write the
file, all inside the lock. New scopes are `mkdir -p`'d *inside* the lock's
reach (regression cover for the 2026-09-21 new-channel silent drop).
Dedup rides the same lock: if `.fleet/ids/<msg_id>` exists, return its seq
with `deduped: true` — retried sends collapse to one file.

**Gap replay.** The message files ARE the durable log, so replay needs no
producer cooperation: `gaps` lists seqs in `[1..max]` with no file (a write
that died between alloc and file creation); `fetch --after N` returns every
surviving file with seq > N in order. A consumer that fell behind re-fetches
from its last ack — nothing is ever "resent".

**Acks.** `.fleet/acks/<consumer>` holds one integer, written tmp+rename
(atomic, single-writer per consumer). Monotonic: a stale ack never rewinds
the cursor. `lag` = max_seq − acked per consumer.

**Chat isolation.** Relay chats publish into their own scope dir, so their
seqs are independent and their traffic never appears in the parent channel
or sibling chats. Verified by the isolation test (3×80 concurrent
publishes, zero cross-talk).

## Failure posture

- Fail fast: 15s SIGALRM ceiling on the locked section (main thread);
  no retries, no loops, one clear stderr + nonzero exit.
- No daemons: fleet.py does one op and exits. Consumers that want push
  semantics use the existing inotify-fed ws feed or their own cron;
  nothing here polls.
- All names sanitized (msg_id, consumer, chat slug, sender); scope paths
  are realpath-checked against the root — no escapes.
- Lock files (`.seq.lock`) and `.fleet/` metadata are not `*.md`, so the
  ws server's file pickup is unaffected. Chat-scope `.md` files live in a
  subdir — they do NOT broadcast on the parent channel feed (isolation is
  the point); relay consumers read them via `squawk-fleet fetch --chat`.

## Testing

`python3 test_fleet.py` — 36 assertions: 800-way concurrent publish
(no dup/lost seqs), 16-way racing retries collapse to one seq, gap
detection + ordered replay, per-consumer acks + monotonicity + lag,
two-chat + main isolation under concurrency, msg_id sanitization,
new-scope first publish, CLI subprocess roundtrip. Evidence:
`TEST-EVIDENCE.md`.

## Not built (deliberately)

- No push daemon / long-lived watcher — out of scope, event loop stays
  with the existing ws feed.
- No cross-scope transactions — scopes are independent by design.
- No message TTL/GC — the log is append-only; retention is a separate
  decision.
