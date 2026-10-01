---
name: subagent-control
description: >
  Control agent swarms without cancelling running tasks: reversible steering, throttling, and freezing. Triggers on: swarm control, steer agents, throttle.
---

# subagent-control

Fruitful control of agent swarms WITHOUT cancelling running tasks. Steering,
throttling, and freezing are reversible; cancellation is destructive and is
never a control mechanism. Kill orders come only from Chris, and those are
silent force-kills — a different lane entirely.

## Doctrine

- **Never cancel a running task to "fix" pressure.** A cancelled task loses
  all in-flight work and usually gets re-spawned, doubling the load. Control
  means shaping what runs, not deleting runners.
- **Throttle at the spawn side, not the execution side.** The cheapest place
  to control a swarm is before a worker exists: fewer parallel spawns,
  concurrency caps per worker, batching multiple tool calls into one exec.
  swarm-pause exists for emergencies; spawn discipline exists for every day.
- **Freeze is reversible, kill is not.** SIGSTOP/SIGCONT (swarm-pause /
  swarm-resume) preserves in-flight tool calls. The watchdog auto-resumes
  when pressure settles. Treat a freeze as a pause button, never as a
  punishment.
- **Cognition is not on the box.** Agent thinking runs on the inference
  substrate; only the tool-call path (exec spawns as hatch-execd
  descendants) consumes local CPU. "The swarm is slow" is almost never
  fixed by touching agents — check the tool path first (load-audit,
  container PSI).
- **Coordinate in fleet, don't duplicate.** Before fanning out, check
  squawk fleet + the fleet knowledgebase §2 Active Crews. Two coordinators
  on the same workstream is the most common self-inflicted storm.

## Reading the swarm

| Signal | Command | Meaning |
|---|---|---|
| Cell tool-path pressure | `~/workspace/bin/load-audit` | load vs vCPUs, frozen procs, yote load |
| Who is running | `subagent.list` | own children: running/done/failed, previews |
| Live processes | `ps -eo pid,ppid,stat,%cpu,etime,args` | T-state = SIGSTOP-frozen; R-state churn = exec bursts |
| Container truth | `cat /sys/fs/cgroup/cpu.pressure` | OUR stall %. Host `/proc/loadavg` is other tenants' weather — never a control signal |
| Frozen but alive? | `watchdog_lib.verify_pause()` | counts T-state hatch-execd descendants, excludes own chain |

**Triage order:** container PSI first (are WE stalled?) → process table
(what is actually running?) → subagent list (whose workers?) → fleet
(is another lane storming?). Never invert this: acting on host loadavg
is how v1 of the watchdog froze innocent workers.

## Control mechanisms (weakest first)

1. **Worker queue (persistent).** `~/workspace/bin/worker-queue` — the structural fix for unbounded fan-out.
   - `worker-queue submit --title "x" --brief "..."` — queue work instead of spawning directly
   - `worker-queue status` — shows active/max, pending, available slots
   - `worker-queue next` — get next item when capacity is available
   - `worker-queue start <id> --agent-id <aid>` / `complete <id>` / `fail <id>` — lifecycle
   - `worker-queue config --max-workers N` — persistent cap (default: 8)
   - Queue lives in `~/workspace/queue/` (JSON files) — survives restarts
   - Dispatcher cron (`worker-queue-dispatch`, every 5m) alerts via squawk when dispatch is ready
   - **Rule: check `worker-queue status` before spawning. If at cap, submit to queue.**
2. **Send, don't spawn.** `subagent.send` steers a live worker's next steps
   without restarting it. Use for throttling directives ("cap parallel
   execs at 3, batch file ops per call"). Queued, non-interrupting by
   default; `interrupt: true` only to cut off actively harmful work.
3. **Spawn discipline.** Cap fan-out by measured load (`load-audit` before
   big spawns; keep cell tool path under ~4x). One coordinator per
   workstream — `fleet-lock acquire <workstream>` before fanning out.
   **Now enforced structurally via worker-queue max_workers.**
4. **swarm-pause / swarm-resume.** Reversible SIGSTOP/SIGCONT of the tool
   tree. Excludes own chain. For genuine container-pressure emergencies
   (PSI-verified), not for host busyness.
5. **swarm-watchdog (v2, cron).** The interlock: freezes ONLY on container
   cgroupv2 PSI (cpu some>30%, mem full>10%, io some>50%), auto-resumes on
   settle. Host metrics are alert context, never triggers. Silent when fine.
6. **swarm-eject.** The big red button: STOP (default, reversible) or
   `--kill` the agent tool tree on hatch AND yote runaways. For runaway
   processes, not for busy workers.

## Restarting an agent WITHOUT losing work

Closing a wedged agent and spawning a fresh one redoes completed steps
unless the work is checkpointed first. `~/workspace/bin/agent-checkpoint.ts`
(Bun) is the mechanism — transcript tail + artifacts + pending intent,
all durable on disk.

**Design (paper-steeped, Scribe 2026-09-30): event-sourced replay, not
snapshots.** An agent's real state is already an event log: transcript +
tool-call history + files + KB rows. Cognition is off-box, so the runner
process is disposable by design. Restart = respawn with the event log and
replay from the last verified commit point — never a memory snapshot.
Canonical task state (KB rows, committed files, queue items) lives in a
different failure domain from the ephemeral agent; killing a process can
never corrupt it, because commits are the only thing that counts.

**Borrowed (Magpie 2026-09-30, via pattern-borrow.ts):**
- **waggle** (modiqo/waggle): handoffs as resolvable tokens, not pasted
  context. The respawn brief hands the checkpoint ID + tiny KV; the new
  agent resolves the full event tail lazily, on demand — never re-pasted.
- **zcf** (UfoMiao/zcf): checkpoint = tiny structured KV (status,
  next_step, key_files, pinned blockers/decisions). High bar for writes:
  pin only what a future run will re-read. No transcript dumps.
- **elves** (aigorahub/elves): checkpoint at meaningful-edit boundaries
  (after each commit, each landed file), not arbitrary intervals; keep
  checkpoint artifacts bounded.

**Restart ladder (weakest first):**
1. **Steer, don't restart.** `subagent.send` (with `interrupt: true` only
   for actively harmful work) redirects a live worker. No state is lost
   because nothing restarts. This resolves most "stuck" cases.
2. **Resume interrupted agents.** `subagent.resume` continues an
   interrupted/failed agent from where it stopped — the platform's own
   lossless restart. Only works on interrupted agents, not running ones.
3. **Checkpoint + respawn (wedged running agents only):**
   ```
   agent-checkpoint.ts capture --agent-id <id> --name <name> \
     --lane "lane/task" --brief "<original brief>" \
     [--parent <pid>] [--kb-row <path>] [--pending "<what's left>"] \
     [--artifact <path>]...
   # Quiesce at a tool-call boundary if possible: prefer closing between
   # exec calls (deterministic), not mid-syscall. If it's actively
   # thrashing and won't quiesce: swarm-pause first (reversible SIGSTOP),
   # then close — the in-flight call is abandoned and the replacement
   # re-runs that ONE step idempotently (never the whole task).
   # then: subagent.close the old agent (never a healthy-busy one —
   # tell its parent/coordinator not to re-spawn a duplicate)
   # then: subagent.spawn with the output of:
   agent-checkpoint.ts brief <checkpoint-file>
   ```
   The replacement's step zero: read the checkpoint, `verify` every
   artifact's sha256, UPDATE the KB row (never re-register), post fleet
   continuity as "<name> (continued from <old-id>)". Replay from the last
   verified commit point; completed steps are never redone.

**Fail-closed rule:** no checkpoint file → no restart. A restart without
a checkpoint is how duplicate fleet posts and double KB rows happen.

## What NOT to do

- Do not `subagent.close` a healthy-but-busy worker to "reduce load" —
  you orphan its in-flight work and its parent re-spawns it.
- Do not read host `/proc/loadavg` as a per-lane signal inside the
  container. It is the 126-core host's weather.
- Do not run `pkill -f` against tool patterns — it can SIGTERM your own
  exec shell (pattern matches your own argv). Kill and start are always
  separate exec calls.
- Do not "fix" a quiet agent from `ps` alone — cognition runs off-box;
  zero local processes with live agent rows is normal, not a stall.

## Fleet contract

- Narrate control actions in squawk fleet: what you froze/throttled, why
  (with the PSI or load numbers), and when it releases. Silence from a
  controller reads as a stall.
- If another lane's worker is the pressure source, send them a throttle
  directive via fleet or their coordinator — do not freeze their tree
  without telling them.
- Completions land with artifact paths + commit SHAs, as always.
