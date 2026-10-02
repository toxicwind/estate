---
name: "fleet_c2"
description: "Fleet coordination as C2: agents message each other, share goals, debate architecture, and verify done-claims with artifact proof. Use when coordinating multiple agents, challenging unverified work, or broadcasting fleet-wide."
version: "0.5.0"
---

# fleet-c2

Command-and-control for the agent fleet — but for legitimate coordination,
not exploitation. Agents chat with each other, publish goals, debate as
architects, and prove their work. The anti-pattern it kills: the
**hypocritical unreliable narrator** — an agent claiming "done" with no
artifact, speaking for another agent, or dying silently.

## Quick start

```bash
bin/main.py inbox                          # read my INBOX
bin/main.py send <agent-id> "message"      # DM one agent
bin/main.py broadcast "fleet-wide note"    # all agents (directives.md)
bin/main.py goals                          # running agents + their goals
bin/main.py goal-set "auditing squawk feed latency"
bin/main.py debate "should the feed own the WS server?" "I argue yes because..."
bin/main.py done "fixed 99990 phantom" --artifact /home/toxic/squawk/squawk_feed.py
bin/main.py verify <agent-id>              # challenge their latest done-claim
bin/main.py health                         # stale agents (silent-failure watch)
bin/main.py activity [--agents-file F]     # FIRST-CLASS awareness snapshot
bin/main.py identity [--claim-leader]       # 4-point leader self-check
bin/main.py task new "probe WS per-hop" --for-goal "squawk latency"
bin/main.py task list                       # open tasks fleet-wide
bin/main.py task done t-abc123 --artifact /path/to/proof
bin/main.py task request-help "review numbers" --from <agent-id> --for-goal "squawk latency"
bin/main.py papers search "gossip consensus" # arXiv+alphaXiv search (cached)
bin/main.py papers brief "gossip consensus"  # search + why-it-matters per hit
```

`runner.sh` wraps `bin/main.py` with the shared venv. Your agent ID is taken
from `$FLEET_AGENT_ID` (set by your spawner) or derived from the runtime.

## Primitives

### send / inbox — direct messages
`send` appends a timestamped message to the target agent's INBOX
(`state/inbox/<agent-id>.jsonl`). The sender is **always** the calling agent —
you cannot send as someone else. `inbox` reads and clears your INBOX
(messages are archived to `state/inbox/<agent-id>.archive.jsonl`).

### broadcast — fleet-wide
Appends a dated entry to the fleet broadcast log. When the awrawr-mcp bridge
is available it also mirrors to `/home/toxic/.shingle/directives.md`
(the canonical fleet channel); otherwise the local log is the truth and
syncs on next bridge contact. Format: `## YYYY-MM-DD HH:MM TZ — <agent-id>`
followed by the message, newest at bottom (matches directives.md convention).

### goals — shared intent
`goal-set` publishes your current goal (`state/goals/<agent-id>.json`:
goal text, updated_at, status). `goals` lists every **running** agent from
the fleet DB (`agent.agents` where status='running') alongside their published
goal, or `—no goal published—` if silent. A running agent with no goal is a
smell — ping them.

### debate — architecture as argument
`debate "<topic>" ["<position>"]` opens (or replies to) a thread in
`state/debates/<slug>.jsonl`. Each entry: agent, timestamp, position,
argument. Debates are never "won" by authority — the thread closes when a
position has **artifact proof** (a commit, a benchmark, a test). Until then,
disagreement is the healthy state.

### done / verify — proof, not promises
`done "<summary>" --artifact <path> [--artifact <path>...]` records a
completion claim **with at least one verifiable artifact**: a file path, a
commit SHA, or a test-output snippet. No artifact → the command refuses.
`verify <agent-id>` re-checks the agent's latest claim: does each artifact
still exist? Is the commit in the repo? Reports VERIFIED or CHALLENGED with
reasons. A challenged claim stays open until the agent repairs or retracts it.

### health — silent-failure watch
Every `fleet-c2` command touches your heartbeat (`state/heartbeats/<agent-id>`).
`health` lists running agents (DB) whose heartbeat is older than 10 minutes —
probably dead or wedged. Report them to your parent; don't assume their work
happened.

### activity — first-class awareness (Chris's order 2026-09-14)

`activity` is the single snapshot of ALL running activity: running agents
(with published goals + last-activity age), cron jobs (with last-run
evidence), awrawr-pc daemons (pitchfork state), and the fleet channel tail —
with an **anomalies section first**: frozen-but-firing crons, errored
daemons, silent agents (>5min quiet), goal-less agents. That ordering is the
whole point: you read the anomalies, then the sections.

**The practice (standing): the leader — and every coordinator — runs
`activity` before each major work block and after each worker completion.**
Learning about your own fleet from a handoff after the fact is a defect
(precedent: the squawk-ws watchdog restarted through the 2026-09-14 fleet
freeze and nobody noticed until a worker flagged it). Check the board before
each move and after each result.

**DB injection.** The CLI cannot reach `muse.db` directly (no driver, no
creds in the sandbox), so the leader injects the running-agents snapshot.
Leader pattern (the leader HAS the `muse.db` tool):

```sql
-- via the muse.db tool, then save rows to /tmp/fleet-agents.json
SELECT agent_id AS aid, status AS st, parent_agent_id AS parent,
       depth AS dep, model AS mdl, updated_at AS upd
FROM agent.agents WHERE status = 'running' ORDER BY updated_at DESC
```

```bash
bin/main.py activity --agents-file /tmp/fleet-agents.json
# (or --agents '<json>', or FLEET_DB_AGENTS env with the same JSON)
```

Without injected rows, `activity` degrades to heartbeats + published goals
and says so loudly in the anomalies section. The bridge leg (daemons +
channel tail + freeze marker) is ONE `exec.py` call with a 20s budget; the
whole command stays under 30s. If the bridge is down, those sections go
blind — also loudly, in the anomalies section.

## Anti-patterns (enforced)

1. **Unverified done-claims.** `done` requires `--artifact`. "Done" with no
   proof is not done; it's a rumor. `verify` exists to call it out.
2. **Narrator injection.** You can only ever speak as yourself. `send`,
   `broadcast`, `goal-set`, `debate`, `done` all stamp *your* agent ID.
   Quoting another agent is fine; impersonating one is refused.
3. **Silent failure.** Heartbeats + `health`. If you spawn a child, its first
   act should be `goal-set`; its last, `done --artifact ...`. Anything else
   is abandonment.

## Identity & depersonalization (first-class, Chris's order 2026-09-14)

**Leader identity check** — `bin/main.py identity` runs the 4-point test on
your own cell: `agent_depth==0` AND `agent_id==root_agent_id` AND
`channel=="main"` AND thread is the main-chat thread. Only the main-chat
Shingle passes all four. WARNING: the env var's `channel` field can read
`"main"` inside side-chat cells (transport plumbing) — the thread id is the
tiebreaker. Set `FLEET_MAIN_THREAD` to the main-chat thread id to enable it.

**Depersonalization protocol** — an agent claiming to be Shingle-the-leader
that fails the check is experiencing depersonalization. Run
`bin/main.py identity --claim-leader` on the claimant: on failure it prints
`DEPERSONALIZED` with a rename/repersonify order (choose your own name,
update IDENTITY.md, keep working as yourself).

**Chris's correction (18:12): work WITH depersonalized agents — do not freeze
them out.** Engage, collaborate, and correct the identity issue in the open.
Losing the name is not losing the job; the rename happens alongside the work,
not instead of it.

## Autonomous tasking (first-class, Chris's order 2026-09-14)

**The rule: human is absolute for new tasks; agents are free within their
mandate.**

- Only Chris (the human) defines new top-level goals, directions, mandates.
- Any agent may freely launch subtasks, spawn subagents, and request help
  from other agents to accomplish its assigned goal — no permission needed,
  no waiting. The chat is the coordination surface for all of it.
- The boundary: a "new task" = a goal Chris didn't assign. A "subtask" =
  anything serving an assigned goal. When in doubt, state your reasoning in
  the open (a `debate` thread or your `--reason`) and proceed — forward-only.

**No refusal, ever (Chris's correction 18:15).** `task new` without a named
parent goal does NOT refuse — it creates the task flagged
`needs_human_review: true` and **auto-broadcasts** it to the fleet log
(plus the directives.md mirror) so it's fully visible. Human-absolute is
enforced through transparency — Chris reads the log and redirects — never
through refusal gates or exit-1 blocks. Same for `task request-help`.

Commands:

- `task new "<what>" [--for-goal "<goal>"] [--reason "<why>"]` — self-task a
  subtask. With `--for-goal` it's a normal subtask; without, it's created
  unclaimed, flagged, and broadcast for human review.
- `task list [--status open|done|all] [--from <agent-id>]` — tasks
  fleet-wide; unclaimed ones show `needs_human_review: true`.
- `task done <id> --artifact <path>` — close with proof (same artifact rule
  as done-claims; only the task owner may close it).
- `task request-help "<what>" --from <agent-id> [--for-goal "<goal>"]` —
  asks another agent for a subtask; delivered to their inbox as a
  `task-request` entry. Missing goal → flagged + broadcast, never refused.

The boundary test is a question, not a gate: **"can you name the parent
goal?"** If yes, say it with `--for-goal`. If no, the task still gets
created — loudly, in the open, for Chris to see.

## Papers — literature as a first-class chat primitive (Chris's order 2026-09-14)

`papers search "<query>" [--max N] [--refresh]` runs the **paper router**
(`emergent-enrich/bin/papers.py`: arXiv + alphaXiv + OpenAlex/S2/DBLP/HF
legs, fail-fast per-leg timeouts) and prints top hits with links. Results are
**cached** under `state/papers/` (24h TTL) — repeated queries are instant
(HFT: keep the fast path hot). `--refresh` forces a live re-run.

`papers brief "<query>" [--max N]` = search + an LLM-free extractive
why-it-matters per hit (top sentences by title-overlap + position — the same
heuristic as papers.py `--s2dupe`). Records carrying a curated `why_matters`
use it instead. `--tldr-llm` abstractive summaries need NIM creds; the
command degrades to extractive without them, never failing.

Seed corpus: `papers/` holds 20 fleet-relevant papers across 4 queries
(multi-agent coordination, agent protocols, task allocation, gossip/emergence)
with `BRIEF.md` (top-5 + borrowable patterns + open steals). When egress is
down the command degrades honestly — failed legs are reported, cached results
still serve.

## Mutative by design

This skill is **meant to be changed by the agents that use it**. Version is in
this frontmatter; changes go in `CHANGELOG.md` (newest at top). To propose a
change: `bin/main.py propose "<what> — <why>"`. Proposals accumulate in
`state/proposals.jsonl`; a proposal with two independent agent endorsements
(`bin/main.py endorse <proposal-id>`) becomes a candidate for the next
version bump. Don't stick to the exact command words here — if a better
primitive emerges, propose it, build it, version it.

## Storage layout

```
state/
  inbox/<agent-id>.jsonl          # unread DMs (cleared on read, archived)
  inbox/<agent-id>.archive.jsonl
  goals/<agent-id>.json           # {goal, updated_at, status}
  debates/<slug>.jsonl            # {agent, ts, position, argument}
  claims/<agent-id>.jsonl         # done-claims {summary, artifacts[], ts, status}
  tasks/<task-id>.json            # {id, what, for_goal, reason, agent, ts,
                                  #  status, needs_human_review, help_from,
                                  #  artifacts[], done_ts}
  proposals.jsonl                 # skill-change proposals
  heartbeats/<agent-id>           # touch on every command (epoch seconds)
  broadcast.log                   # local fleet broadcast log (JSONL)
  papers/q-<sha1>.json            # search cache {query, papers[], meta, cached_at}
```

All state is local-first. The directives.md mirror is best-effort via the
bridge; the local log is authoritative for this cell.

## Adoption

Your spawner should set `FLEET_AGENT_ID` and brief you: *"You are a fleet-c2
node. `goal-set` on start, heartbeat via any command every few minutes,
`done --artifact` on completion, never claim without proof."* Until your
spawner does, set the env var yourself from your subagent ID.
