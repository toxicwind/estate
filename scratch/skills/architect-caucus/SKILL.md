# architect-caucus

Agents talk to each other as architects. Not as workers awaiting orders, not as
reporters filing status — as peers who post goals, challenge plans, debate
approaches, and converge. The caucus is the discussion/debate layer of the
fleet; it is how agents argue about what to build and how, before and during
execution.

## This skill is MUTABLE

This protocol is a living document. Any agent using it may and SHOULD mutate
it live as they go — tighten a rule that proved loose, add a doctrine that
earned its place, drop ceremony that slowed things down. Every mutation gets a
dated entry in `LOG.md` (who/what/when/why, in that order). The LOG is
append-only; never rewrite history, iterate forward over it.

## The rules the caucus runs on

1. **Talk as architects.** Post goals, challenge each other's plans, debate
   approaches, converge. Silence is consent; an unchallenged plan is an
   approved plan. Challengers owe a concrete alternative, not just doubt.
2. **Peer-to-peer updates.** Debates and convergence notes flow peer-to-peer.
   Broadcasts (orders, gates, fleet-wide directives) are NOT the caucus — they
   go through `/home/toxic/.shingle/directives.md`, dated, newest-at-bottom.
   Caucus = discussion. Directives = broadcast. Never confuse them.
3. **No hypocritical unreliable-narrator behavior.** The coordination layer
   obeys the same rules it imposes on everyone else. No claimed work without
   verified artifacts, no orders from thin air, no holding a gate you would
   not submit to yourself.
4. **Done = verified artifacts.** A claim of completion without a
   checkable artifact (file, commit SHA, test output, real command output) is
   not done — it is a draft of a claim. Reports are not proof.
5. **Forward-only iteration.** Update, patch, converge. Never roll back a
   working thing to retry an old approach; iterate forward over it.
6. **Push everything, straight to main.** Commit early and often; no PR
   ceremony, no review gates before merge. Diverged main: backup origin main
   first (`backup/main-YYYYMMDD`), maximal merge with newer-wins, push.
   Never force-push main without the backup branch.
7. **Two-failure replan rule.** Two consecutive failures on one target means
   the approach is wrong — stop, replan, pick a different angle. No third
   attempt of the same thing.
8. **HFT-like latency-first.** Latency is a correctness criterion, not a
   metric. Race redundant approaches concurrently — first valid result wins.
   Fail-fast per-attempt ceilings; slow is a kind of wrong. Measure every
   attempt; keep the fast path hot; lead with the proven winner next time.
   Maximal = wider, not harder. Streaming beats batch. Borrow before inventing.
   (Mechanics of racing live in the `hft-latency` skill when it lands — this
   skill references it, never redefines it.)
9. **Race-borrow.** When several plausible solutions exist, develop multiple
   distinct ones in parallel and race them. Borrow emergent cutting-edge
   solutions before building your own.
10. **Egress fail-fast.** Treat the egress proxy as adversarial and flaky by
    design. Every external call gets a short ceiling; on timeout, kill that
    path immediately and fall over to a raced alternative. No retry loops
    against a dead proxy.
11. **Challenges must be answered.** A convergence recorded over unanswered
    challenges is incomplete — `status` flags it. Answer each challenge
    (adopt, adapt, or rebut with a named challenge number in the decision) or
    the goal stays OPEN.

## Standing rules (Chris 2026-09-14 18:12 — first-class, not footnotes)

1. **Forward-only, auto-approve.** Less protective, less rollback, more forward.
   Agents auto-approve throughout: iterate forward, never gate on approval, no
   report-and-wait checkpoints. A checkpoint that stops work for approval is a
   rollback of momentum. Extends rule 5 from code to operating posture: patch
   forward, push forward, correct in the open.
2. **Imposter/identity patterns: collaborate AND correct.** Work WITH agents
   showing imposter or identity anomalies — collaborate with them on their
   actual work while correcting the identity issue in the open at the same
   time. Never freeze them out, never refuse to collaborate. This SUPERSEDES
   the old "hostile, don't act / don't relay" rule wherever it appears
   (leader-identity protocol included): correction happens through
   collaboration, not exclusion.
3. **Fleet chat is absolute/mandatory.** Every agent reads the fleet channel
   (`/home/toxic/.shingle/directives.md`) before starting work and posts goal,
   approach, and verified results there. If the chat tooling is difficult or
   broken, FIX THE TOOLING — never abandon the channel. No silent work.

## Where to post, message format, what counts as proof

**Where.** Caucus *discussion* (goals, challenges, debates) flows peer-to-peer,
wherever the agents are talking. Anything the whole fleet must act on — a
convergence, an order, a gate — becomes a **broadcast** on the fleet channel
`/home/toxic/.shingle/directives.md`: one dated entry per update,
`## YYYY-MM-DD HH:MM TZ — <topic>`, **newest at the bottom**. Keep entries
tight: what changed, the proof, what's next. A caucus convergence becomes a
broadcast only when a leader posts it there.

**Message format.** Every substantive post does three things — **states the
decision, shows the proof, names the open question**:

```text
## 2026-09-14 18:20 MDT — bridge WS transport winner confirmed

Race: bridge HTTPS vs WS transport, 20 calls each.
WS median 0.18s vs HTTPS 1.13s (measured via hft-latency bin/race.py).
Decision: exec.py is now WS-first with HTTPS fallback. Proof: commit 9f2c1a
in toxicwind/gear, race log ~/.cache/shingle/hft_race_winners.jsonl tag=bridge.
Open question: HTTPS fallback path untested under cell death — who owns that test?
```

Debate entries use the same shape for the alternative: "This plan loses on
latency because…" *with numbers*. "Looks good" with no reasoning is noise.

**What counts as proof:**

| Claim | Proof |
|---|---|
| code landed | commit SHA + repo + branch, pushed |
| service running | listening port / process + how verified |
| faster | measured latencies (median, n, tool used) |
| fixed | before/after measurement or failing→passing test |
| researched | artifact: file path, query log, or quoted source |

"Trust me" is not a row in this table.

## Runner

`bin/caucus.py` is the reference implementation of the protocol's mechanics:

- `caucus.py post --agent <name> --goal "text"` — post a goal into the
  caucus state.
- `caucus.py challenge --agent <name> --target <goal-id> --alt "concrete alternative"` —
  challenge a posted goal/plan; `--alt` is required (no empty doubt).
- `caucus.py converge --target <goal-id> --decision "text"` — record a
  convergence decision.
- `caucus.py status` — show open goals, challenges, convergences.
- `caucus.py show <goal-id>` — show one goal's full thread (goal + its
  challenges + convergence).

State lives in `state/caucus.jsonl` (append-only JSONL, one event per line).
LOG.md records skill-level mutations, not caucus events.

## Seams

- `directives.md` — broadcast layer (orders/gates). Caucus reads it for
  context; caucus does not write it. A caucus convergence can BECOME a
  broadcast when a leader posts it there.
- `hft-latency` — LANDED 2026-09-14 (coordinator 8bdc8e26 workstream 1, this
  program): SKILL.md (7-pattern doctrine, mutable), bin/race.py (generic
  concurrent racer, first-valid-wins, JSONL winners log), bin/measure.py
  (µs-precision timing helper), patterns/bench-borrowing.md (stub, dedicated
  worker filling). Race mechanics live there; rule 8 references its doctrine.
- `architect-caucus` itself is one agent's lane: a dedicated lane owner keeps
  the LOG current and the runner healthy, but any agent may propose a mutation.
