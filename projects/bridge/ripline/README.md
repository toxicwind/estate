# ripline

**The fast line between the hatch cell and yote.** A Bun-native forward fork
of `yote-conn` — same CLI surface, ~3.4x faster `exec`, and automatic
fallover to mainline `yote-conn` when its own transport breaks.

> "A fallback is not a rollback." — when ripline breaks, traffic falls
> *forward* to the current stable mainline. ripline stays installed; the
> next call tries ripline first again (self-healing, no sticky downgrade).

## Name

A *ripline* is the rigging rope you haul loads with. Short, punchy, and it
belongs to the same rope-and-pulley family as the lane that built it.

## Usage

Drop-in for `yote-conn` — every subcommand mirrors mainline 1:1:

```
ripline health
ripline exec "<cmd>" [workdir] [timeout_s]
ripline multi <cmds.json | ->
ripline bg "long-cmd" [workdir] [timeout_s]
ripline bg-status <handle>
ripline bg-tail <handle> [soff] [eoff]
ripline bg-list
ripline bg-kill <handle>
ripline herd <METHOD> <path> [body.json | -]
ripline flock <METHOD> <path> [body.json | -]
```

`RIPLINE_NO_FALLOVER=1` disables fallover (fail loudly — for testing).

## Lane order (exec)

1. **Unix socket** straight to `ws_daemon` (`~/.cache/awrawr-ws-bridge.sock`,
   newline-delimited JSON). No Python CLI startup, no connector-HTTP hop.
   If the socket is missing, the daemon is healed in the background
   (bind-race singleflight — a second starter just fails to bind) and this
   call moves on immediately.
2. **Connector HTTP** `127.0.0.1:18301` — the daemon races WS→HTTPS there
   itself. Only reached on proven pre-dispatch failure.
3. **Mainline `yote-conn`** — automatic fallover, original argv re-dispatched
   with stdio inherited (byte-identical output), exit code propagated. The
   event is logged to `~/.cache/ripline-fallover.jsonl` (last 200).

`bg*` / `herd` / `flock` go via lane 2 → 3 (they are daemon-side ops; the
socket protocol only speaks `exec`).

## The no-double-exec contract

Borrowed from `exec.py` and the hft-latency skill — first-valid-wins racing,
dispatch-gated:

- **Pre-dispatch failure** (socket never connected, send failed, daemon
  reports "not connected"/"reconnecting"): the daemon never saw the command —
  safe to re-dispatch on the next lane.
- **Post-dispatch failure** (socket died mid-command, daemon says the command
  "may have executed", response timeout): report the failure and STOP. A
  command that may have executed remotely is never run twice, on any lane.

`src/protocol.ts` classifies every daemon error frame; `bun test` pins the
contract.

## Measured latency (`exec "true"`, 5 runs each, 2026-09-30)

| path | range | notes |
|---|---|---|
| `yote-conn` (mainline, Python) | 739–980ms | Python startup + connector-HTTP hop |
| `yote-conn-fast` (Bun, exec-only) | 227–420ms | socket direct, no subcommand parity |
| `ripline` (Bun, compiled, full CLI) | 234–671ms | socket direct + full parity + fallover |

ripline runs in the same band as the exec-only fast path — roughly 1.5–2.5x
faster than mainline — with full subcommand parity and automatic fallover.
The residual variance is the bridge round-trip itself (WS to yote), which
dominates all three paths.

## Layout

```
projects/bridge/ripline/
  src/ripline.ts      CLI (health/exec/multi/bg*/herd/flock)
  src/transport.ts    socket NDJSON transport + daemon heal + :18301 HTTP lane
  src/protocol.ts     frame types + pre/post-dispatch classification
  src/fallover.ts     mainline re-dispatch + JSONL ledger
  test/contract.test.ts
  package.json
```

## Deploy

The compiled binary lives at `~/workspace/bin/ripline` on the hatch cell
(built with `bun build --compile`; source of truth is this directory).
Mainline `yote-conn` is untouched as the stable entry point — ripline is
opt-in per call, and falls over to `yote-conn` on its own failures.

## Borrowed patterns

- GitHub-wide pattern-borrow ("remote shell exec bridge", "bun unix socket
  client", "websocket command dispatch"): persistent multiplexed unix-socket
  clients, dispatch-gated first-valid-wins, fail-fast degraded steady-state.
- Estate: `exec.py` WS/HTTPS race + down-flag TTLs, hft-latency skill
  (race redundant paths, measure every hop, never retry-spin),
  `yote-conn-fast` (Bun→socket direct, the proven fast path).
- Paper pass (paper-poller `race_papers.py`): nothing directly applicable to
  an exec bridge beyond URLLC multi-connectivity (race redundant paths —
  already the design) and Shenango (kernel-bypass for μs tails — the
  philosophy behind skipping the Python/HTTP hops).
