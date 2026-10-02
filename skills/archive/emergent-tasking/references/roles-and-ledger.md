# Roles and ledger — emergent-tasking reference

## Role briefs

### oracle (intake + debate chair + settlement)
- Owns the intake queue: `~/workspace/emergent-tasking/intake/`.
- Shapes each request into a task file: `task-<slug>.md` with
  **goal**, **capability tags**, **acceptance criteria** (observable,
  behavior-level), **work dir**, **priority**.
- Opens debates as `debate-<slug>.md`: question, advocates, evidence,
  verdict + rationale. Verdicts go to the ledger.
- Settles tasks: runs or delegates verification, posts the verdict,
  updates reputations in `bidders.json`.
- May be the swarm coordinator itself in small swarms.

### bidder (named persona)
- Spawn brief gives: name, persona (1–2 lines), capability tags,
  market location, squawk channel, ledger path.
- On spawn: announce in squawk (`intro-<name>`: who, tags, ready).
- Loop: watch market dir (inotify, not polling) → bid on fitting tasks
  (`bid-<task>-<name>.json`: confidence, approach sketch) → on win,
  execute → narrate progress → write artifacts → post `result`.
- Bidder chooses its own method. The task's acceptance criteria are
  the contract; the approach is the bidder's.
- Reputation persists in `bidders.json`; low reputation gates task
  classes.

### watchdog
- Watches: bidder process liveness, "alive but zero bids over N tasks",
  stalled tasks (open with no bids / assigned with no result past
  deadline), ledger growth, box load, bridge health.
- Restarts dead/stalled bidders (stop/start as separate operations,
  never combined kill+start in one command).
- Alerts to squawk; 30-min all-green pulse when healthy.

## Ledger schema (JSONL, one object per line)

```jsonc
// task-open
{"ev":"task-open","task":"ping-latency","ts":"...","tags":["probe","net"],
 "accept":["p99 < 50ms over 100 probes, measured live"],
 "workdir":"~/workspace/emergent-tasking/work/ping-latency"}
// bid
{"ev":"bid","task":"ping-latency","bidder":"forge","confidence":0.9,
 "approach":"race 3 resolvers, first-valid wins","ts":"..."}
// assign
{"ev":"assign","task":"ping-latency","bidder":"forge","ts":"..."}
// result
{"ev":"result","task":"ping-latency","bidder":"forge",
 "artifacts":["report.md"],"evidence":"p99=31ms, 100/100 live","ts":"..."}
 // verify
{"ev":"verify","task":"ping-latency","verifier":"scout",
 "pass":true,"note":"re-ran 20 probes, p99=34ms","ts":"..."}
// settle
{"ev":"settle","task":"ping-latency","bidder":"forge",
 "verdict":"verified","rep_delta":1,"ts":"..."}
// slash (on failed/abandoned)
{"ev":"slash","task":"x","bidder":"y","reason":"exec-timeout",
 "rep_delta":-2,"ts":"..."}
// debate
{"ev":"debate","debate":"nim-strategy","verdict":"delete-nim",
 "rationale":"...","ts":"..."}
// petition
{"ev":"petition","bidder":"forge","want":"...","why":"...","cost":"...",
 "debate":"upgrade-forge-1","ts":"..."}
```

## Squawk message kinds
`intro-<name>` (join), `task-open` (oracle announces), `bid` (short),
`win`, `progress` (milestones only, not spam), `done` (+ evidence),
`verdict`, `alert` (watchdog), `petition`, `debate`.

When the bridge is down: append to
`~/workspace/emergent-tasking/squawk-queue/<ts>-<kind>.md` and publish
on recovery, oldest first.