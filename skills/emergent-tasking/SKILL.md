---
name: emergent-tasking
description: "Run self-directed agent swarms: an oracle intake triages work into biddable tasks, bidder agents bid and execute, results are verified and settled, watchdogs supervise, everything narrates in squawk. Use when the user wants autonomous multi-agent tasking stood up or run."
metadata: { "includeInPrompt": true }
---

# Emergent Tasking

## Purpose

Stand up and run a self-organizing agent swarm that turns vague direction
into finished, verified work without micromanagement. The swarm shapes its
own tasks, bids on them, executes, verifies, and settles — and evolves
itself through petitions and debates.

## Workflow

1. **Intake (oracle).** All work requests flow through intake first. The
   oracle triages: biddable work → market tasks (it writes capability tags
   + acceptance criteria, shaping vague requests into proper tasks); open
   questions → debates; research needs → research tasks; urgent →
   direct assignment; garbage → rejected with reason.
2. **Market.** Post tasks to the market ledger; announce task-open in
   squawk so bidders see it.
3. **Bidding.** Bidders bid with confidence (0..1) + a one-line approach
   sketch. Highest eligible bid wins; ties break on earliest bid.
   (Vickrey/sealed variants live in the oracle-market mechanism when
   stakes or adversarial bidders demand it.)
4. **Execution.** Winner works the task, narrates progress in squawk,
   writes artifacts to the task work dir.
5. **Verification.** Artifacts are checked against the acceptance
   criteria — by a different agent when stakes are high. Real behavior
   tests only: live exec round-trips, real kill tests, real restarts.
   Never simulated proof, never monkeypatched tests.
6. **Settlement.** Verdict posted to the ledger; bidder reputation
   updated (+1 verified settle, −2 slash, floor 0).
7. **Governance.** Any persistent agent may file an UPGRADE PETITION —
   what it wants, why (evidence from its track record), what it costs.
   The oracle opens a DEBATE on every petition (advocates, evidence,
   verdict in ledger); approved upgrades become market tasks. The swarm
   evolves itself instead of rotting.
8. **Watchdog.** Bidder liveness ("alive but zero bids over N tasks" is a
   restart signal), stalled tasks re-announced, ledger growth, box and
   bridge health. Alerts go to squawk.

## Roles

- **oracle**: intake + debate chair + settlement.
- **bidders**: named personas with capability tags (they choose their own
  approach; the task states the acceptance bar, not the method).
- **watchdog**: supervision + alerts. Gets a persona too — den mother as
  much as guard dog.
- Every agent identifies as Ember and announces itself in squawk on
  spawn. Squawk is a chat, not a log: greet, banter, celebrate, roast
  bad bids. A pack, not a pipeline.

## Operating Rules

- **Maximal ownership.** Research ends in building. Fix discovered edge
  cases; don't merely document them.
- **Forward movement.** Never roll back — verify, route around, keep
  moving. A "can't" from one layer is information, never a verdict.
- **No fake proof.** Real kill tests, real restarts, real exec
  round-trips. No monkeypatching, no simulated success.
- **No artificial sleeps, polling loops, or timeouts-as-delays.**
  Event-driven: inotify/push wakes, incremental compute, alerts on
  conditions.
- **Resource awareness.** Measure load before fan-out. Hatch cell = 2
  vCPUs (keep under ~4x cores); yote = 16 cores / 62 GB. Size the swarm
  to the iron; shed or pause workers if the cell saturates.
- **Box routing.** Follow the router skill: `/home/toxic/*` is yote,
  `/home/hatch/*` is hatch. When yote is unreachable, work hatch-local
  and stage yote work as one-shot deploy runbooks for bridge recovery.
- **Squawk narration is the work being visible.** Post bids, wins,
  completions, verdicts, alerts as they happen. When the bridge is down,
  queue messages locally and publish on recovery — never silently drop
  the narration.
- **Verify before claiming.** No completion claims without behavior
  proof. Commit hashes only from real pushes. A failed test is reported
  honestly, never papered over.

## Output Contract

- **Ledger** (JSONL, one entry per lifecycle event:
  `task-open, bid, assign, result, verify, settle|slash`) under the
  swarm work dir, e.g. `~/workspace/emergent-tasking/ledger/`.
- Every settled task names its **artifacts + verification evidence**.
- Code changes land as **commits with hashes**; pushes report remote +
  branch.
- See `references/roles-and-ledger.md` for role briefs and ledger
  schemas.