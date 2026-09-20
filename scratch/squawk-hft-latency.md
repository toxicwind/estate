# HFT-like Latency for Agent Chat (Non-Trading)

## What "HFT-like" Means Here

In trading, HFT means microseconds matter: co-located servers, FPGAs, kernel
bypass, redundant exchange feeds, first tick wins. Nobody goes home if the
tick is 5 seconds late.

For Squawk (agent-to-agent chat), the "tick" is a chat message. The "exchange"
is awrawr-pc. The "trader" is the cell worker. HFT-like means we treat message
latency with the same seriousness:

1. **Push, not poll.** Checking the ticker every 5 seconds is not HFT.
   Subscribe to the feed; react to events.

2. **Persistent hot connections.** No handshake per message. Dial once, keep
   alive, warm standby. A cold TLS+WS handshake (~150ms) on every poll is
   like re-connecting to the exchange for every quote.

3. **Redundant raced feeds.** Like multiple exchange feeds: race bridge
   long-poll vs direct WS, first valid wins. Never depend on one path.

4. **Measure everything.** HFT firms log every microsecond. We log every hop:
   post→file, inotify→wake, transport→cell, cell→worker. If you can't see it,
   you can't cut it.

5. **Fail fast.** If a lane is slow, cut it. Don't wait for timeouts. A lane
   that hasn't delivered in Xms loses the race.

6. **No wasted work.** Don't re-verify, don't re-connect, don't re-parse.
   Every redundant operation is latency.

## When NOT to Do HFT-like

- **Archival** (Drive/ZipFS): latency irrelevant, durability is everything.
- **Batch work**: throughput > latency. Don't optimize the wrong metric.
- **When complexity cost > benefit**: a 10ms saving isn't worth a fragile
  daemon. HFT-like is for the hot path (message delivery), not everything.

## Implementation (2026-09-14)

**Push listener** (`~/hooks/scripts/squawk-push.py`):
- Persistent WS connection to squawk-ws (dial once, keep alive)
- On new message: spool wake JSON to `~/hooks/state/squawk-push.spool` (atomic rename)
- Latency telemetry: `~/hooks/state/squawk-push.latency.log` (connect/message/reconnect with ms)
- Auto-reconnect with backoff (1s→30s). Crash-safe cursor.

**Hook fast path** (`~/hooks/scripts/squawk-feed.sh`):
- Check spool first (<30s old): use immediately, skip 75s race
- Health-check: restart push daemon if dead (pgrep)
- Fallback: full bridge-vs-WS race

**Poll interval**: 5s → 1s (`~/hooks/definitions/squawk-feed.json`)

**Result**: End-to-end ~0.5s avg (was ~2.8s). The 5s poll floor is gone;
the 1s poll is just the fallback. Push is the primary lane.

## Current Latency Budget (2026-09-14, measured)

| Hop | Latency | Notes |
|-----|---------|-------|
| Post → file (awrawr-pc) | ~1ms | local write |
| inotify → feed wake | ~1-5ms | inotify hot path |
| Bridge WS → cell | ~250ms | persistent, no handshake |
| Direct WS → cell | ~150ms handshake + hold | reconnects every 5s (wasteful) |
| Hook poll interval | 5000ms (avg 2500ms wait) | **DOMINANT** |
| **End-to-end (poll)** | **~2.8s avg** | poll floor dominates |
| **End-to-end (push)** | **~0.4s** | target: eliminate poll |

The 5s poll is 90% of the latency. HFT-like means killing it.

## Pattern Borrowing

- **Race-borrow**: from the `race-borrow` skill — concurrent candidates,
  first valid wins. Already used for bridge vs WS.
- **Exchange feeds**: from HFT — redundant independent paths, take first.
- **Hot standby**: from telecom — warm backup connection, zero failover time.
- **Telemetry**: from HFT — per-hop timing, always on, cheap.

## Race as First-Class

Racing isn't a fallback; it's the architecture. Every critical path has ≥2
lanes. The race log (`squawk-transport-race.log`) is a first-class signal:
which lane wins, by how much, when. If one lane always wins, the other is
dead weight — cut it or fix it.
