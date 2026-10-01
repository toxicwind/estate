# fleet-mirror-flush

Yote-native completion path for fleet messages, under .

## Why this exists

 (hatch cell) hyper-races fleet delivery. Alongside the race it
writes a **write-ahead journal record** to
 on yote. On any confirmed
delivery the record is deleted. If the race fails but the journal landed, this
timer completes the post — so a message survives even if the cell dies
mid-race. If the journal write also fails (bridge down),  falls
back to the cell spool , exactly as before.

## The three stores are disjoint — no double-fire

| Store | Written when | Swept by |
|---|---|---|
|  (yote mirror) | journal write landed (bridge up at post time) | this timer () |
|  (cell spool) | journal AND both delivery paths failed (bridge down) | Hatch platform cron  |
|  (yote-local spool) | yote fleet-post cell-shaped paths fail on yote (market-loop posts) | this timer (added 2026-10-01; 39 orphans drained) |

A message is journaled to **exactly one** store, decided by whether the journal
write landed. The Hatch cron never sees mirror records; this timer never sees
the cell spool. All three sweepers must keep running — disabling one strands its
store's messages. "Never leave both running" applies to duplicate coverage of
the *same* source; here the sources are disjoint by construction.

## Idempotency (two-pass already-delivered check)

For each record the flusher checks the channel dir before posting:

1. **uuid pass** —  anywhere in a channel file head. Catches
   path-B posts, this flusher's own earlier completions, and path-A posts
   whose files  stamped with the uuid.
2. **content pass** — same  on a channel file whose
   mtime is within 15 min of the journal record's mtime. Catches path-A
   () posts, which historically carried no uuid (observed
   2026-09-30: 7 duplicates in one sweep before this check existed).

Already-delivered → delete the stale record. Crash between post and delete →
next run finds the uuid and deletes the record. A message is therefore posted
at most once per store, and each store is swept by exactly one flusher.

## Files

-  — the sweeper (Bun/TypeScript, PID-checked single-instance lock,
  appends to ). Primary.
-  — original bash+python3 implementation. Kept as a backup; the
  systemd unit points at .
-  /  — systemd user
  units, installed to , every 2 min, 
- Install: 
- Verify: Wed 2026-09-30 00:26:00 MDT      33s Wed 2026-09-30 00:24:25 MDT 1min 1s ago fleet-mirror-flush.timer      fleet-mirror-flush.service, then drop a test
  record in  with a fresh uuid and watch it get completed + logged.
