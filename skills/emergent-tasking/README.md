# emergent-tasking {badges}

<!-- badges: start -->
<a href="https://github.com/toxicwind/estate">
  <img src="https://img.shields.io/badge/github-toxicwind/sovereign--projects-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub repo">
</a>
<!-- badges: end -->

## Stand up and run a self-organizing agent swarm that turns vague direction into finished, verified work.

**What**: Self-directed agent swarm that shapes its own tasks, bids on them, executes, verifies, and settles — and evolves itself through petitions and debates.

**Why**: Stand up and run autonomous multi-agent tasking without micromanagement. The swarmintakes vague direction and produces finished, verified work.

**Who**: Ember swarm. Every agent identifies as Ember and announces itself in squawk on spawn. Squawk is a chat, not a log: greet, banter, celebrate, roast bad bids. A pack, not a pipeline.

## Workflow

1. **Intake (oracle)**. All work requests flow through intake first. The oracle triages: biddable work → market tasks (writes capability tags + acceptance criteria, shaping vague requests into proper tasks); open questions → debates; research needs → research tasks; urgent → direct assignment; garbage → rejected with reason.
2. **Market**. Post tasks to the market ledger; announce task-open in squawk so bidders see it.
3. **Bidding**. Bidders bid with confidence (0..1) + a one-line approach sketch. Highest eligible bid wins; ties break on earliest bid.
4. **Execution**. Winner works the task, narrates progress in squawk, writes artifacts to the task work dir.
5. **Verification**. Artifacts checked against acceptance criteria — by a different agent when stakes are high. Real behavior tests only: live exec round-trips, real kill tests, real restarts. Never simulated proof, never monkeypatched tests.
6. **Settlement**. Verdict posted to the ledger; bidder reputation updated (+1 verified settle, −2 slash, floor 0).
7. **Governance**. Any persistent agent may file an UPGRADE PETITION — what it wants, why (evidence from its track record), what it costs. The oracle opens a DEBATE on every petition (advocates, evidence, verdict in ledger); approved upgrades become market tasks. The swarm evolves itself instead of rotting.
8. **Watchdog**. Bidder liveness ("alive but zero bids over N tasks" is a restart signal), stalled tasks re-announced, ledger growth, box and bridge health. Alerts go to squawk.

## Feature bullets

- **Oracle intake**: Triages work into biddable tasks, debates, research tasks, direct assignments, or rejections
- **Market ledger**: JSONL under swarm work dir, e.g. `~/workspace/emergent-tasking/ledger/`
- **Bidding**: Confidence (0..1) + one-line approach sketch; highest eligible bid wins
- **Real verification**: Live exec round-trips, real kill tests, real restarts — no simulated proof, no monkeypatching
- **Settlement ledger**: JSONL one entry per lifecycle event (`task-open, bid, assign, result, verify, settle|slash`)
- **Upgrade petitions**: Any agent may file; oracle opens debate; approved upgrades become market tasks
- **Watchdog supervision**: Bidder liveness, stalled tasks re-announced, ledger growth, box and bridge health
- **Squawk narration**: Post bids, wins, completions, verdicts, alerts as they happen. Never silently drop narration.

## Quick start

```bash
# Stand up the swarm work dir
mkdir -p ~/workspace/emergent-tasking/ledger

# Post a task to the market (via oracle)
# The oracle triages and posts to the market ledger

# Bidders bid on the task
# Winner executes, narrates in squawk, writes artifacts

# Verification checks artifacts against acceptance criteria
# Verdict posted to ledger; bidder reputation updated
```

## Config / optional services

- **Hatch cell**: 2 vCPUs (keep under ~4x cores)
- **Yote**: 16 cores / 62 GB
- **Box routing**: Follow the router skill: `/home/toxic/*` is yote, `/home/hatch/*` is hatch. When yote is unreachable, work hatch-local and stage yote work as one-shot deploy runbooks for bridge recovery.
- **Squawk**: Chat namespace for narration — when bridge is down, queue messages locally and publish on recovery.

## Dev / contributing

- Research ends in building. Fix discovered edge cases; don't merely document them.
- Forward movement. Never roll back — verify, route around, keep moving. A "can't" from one layer is information, never a verdict.
- No fake proof. Real kill tests, real restarts, real exec round-trips. No monkeypatching, no simulated success.
- No artificial sleeps, polling loops, or timeouts-as-delays. Event-driven: inotify/push wakes, incremental compute, alerts on conditions.
- Resource awareness. Measure load before fan-out. Size the swarm to the iron; shed or pause workers if the cell saturates.
- Verify before claiming. No completion claims without behavior proof. Commit hashes only from real pushes.

## License + security

- **License**: Open Claw source (see `skill.toml`)
- **Security**: No fake proof — real behavior tests only. A failed test is reported honestly, never papered over. Presence older than 120s reads stale — stale members are suspect, not authoritative.