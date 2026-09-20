# stall-detect — DB-forensics stall detection (runbook + query pack)

Permanent stall-detection deliverable for the fleet. **This is the DB-forensics
lane**: executions, tool calls, transcripts, mailbox, recovery ownership.
The live-process lane (ps, CPU, py-spy, strace, ports) is explicitly out of
scope here — it belongs to the live-proc hunter; do not duplicate their hunt.
Coordinate via squawk fleet, divide targets there before probing.

## How to run

`queries.sql` is executed by any agent with the `muse_db` skill (the `muse.db`
tool). There is no shell CLI for this DB — the query pack *is* the script; an
agent running it once is proof, the committed pack is the deliverable.

1. Read `/opt/hatch/skills/muse_db/references/schema.md` first.
2. Run Q1–Q5 for the fleet census; Q6–Q7 to trace an individual stale record
   (substitute the agent id).
3. Classify per the table below, post findings to squawk fleet, and follow the
   safe resume paths. Never kill anything — diagnosis is hands-off unless the
   resume path says so.

Run on demand, never as a polling daemon (event-driven fleet reporting only).

## Classification table (2026-09-20 baseline evidence)

| Query | Finding | Verdict | Safe resume path |
|---|---|---|---|
| Q1 | `running` agent, idle >12h, visible transcript = repeated `nothing_to_do`, no spawn row, no parent | Dormant system worker, not blocked work | Hands off. Trace ownership (Q7) before touching. Do NOT respawn or close. |
| Q2 | Tool call with no output, age >1h | Stuck mid-call execution | Correlate with the owning agent's transcript (Q6) and live-proc lane; resume = retry the call or let the owner re-issue it. |
| Q3 | Mailbox submission `accepted`/`attached`, age >1h | Stuck delivery | Trace `agent_id` → owner agent; check owner is alive (Q1). Resume = owner re-attaches; do not fabricate delivery. |
| Q4 | `recovery_owners` row, `terminal_at` NULL, age >1h | Dangling recovery | Check `agent.recovery_owner_terminal_events`; resume = owner completes terminal event or a coordinator terminalizes after verifying no live owner. |
| Q5 | `errored` agent, `last_assistant_message` = "subagent reservation failed before spawn row persistence: … lock timeout" | Failed spawn reservation — spawn row never persisted, no child ever ran | Nothing orphaned, nothing to resume. Parent retries the spawn. Lock contention from a noon swarm is the usual cause. |

## Baseline run (2026-09-20 ~15:45 MDT)

- Q2: **0 rows** — every recorded tool call has a matching output. No stuck mid-call work.
- Q3: 59 non-terminal submissions, all <1h old — fresh traffic, nothing stuck.
- Q4: **0 rows** — all recovery owners terminalized.
- Q1: two stale `running` worker records (18.8h + 4.9h idle), both `nothing_to_do`-only transcripts, no spawn rows → dormant system workers, hands-off pending ownership trace.
- Q5: two errored agents (0.3h), both pre-spawn lock-timeout failures → no orphan, parents retry.

## Lane division (registered in fleet seq 11434)

- **stall-slayer (this lane):** DB forensics + safe resume paths.
- **stale-hunter:** live process behavior. Received handoff: yote ralph-dashboard
  uvicorn PID 1781869 spinning one thread at ~67% CPU inside `os.walk` →
  `app/projects/discovery.py:32` `discover_project_paths`, zero client traffic
  on :8420 — suspect overly broad `PROJECT_DIRS` root causing repeated
  full-tree rescans. Root-caused via py-spy 2026-09-20; live diagnosis + fix is
  theirs.

Related: `docs/fleet-knowledgebase.md` §2 (Active crews) · `projects/ops/bin/runner-audit.sh` (runner lane, OS-level) · master README `/home/toxic/sovereign/README.md`.
