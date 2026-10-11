# subagent-control {badges}

<!-- badges: start -->
<a href="https://github.com/toxicwind/estate">
  <img src="https://img.shields.io/badge/github-toxicwind/sovereign--projects-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub repo">
</a>
<!-- badges: end -->

## Control agent swarms without cancelling running tasks.

**What**: Reversible steering, throttling, and freezing of agent swarms. Cancellation is destructive and never a control mechanism. Kill orders come only from Chris, and those are silent force-kills — a different lane entirely.

**Why**: Never cancel a running task to "fix" pressure — a cancelled task loses all in-flight work and usually gets re-spawned, doubling the load. Control means shaping what runs, not deleting runners.

**Who**: Doctrine applies to swarm control across the fleet. Coordination in fleet, not duplication — two coordinators on the same workstream is the most common self-inflicted storm.

## Doctrine

- **Never cancel a running task** to "fix" pressure. Cancelled work is lost and usually re-spawned, doubling the load.
- **Throttle at the spawn side, not the execution side**. Fewer parallel spawns, concurrency caps per worker, batching multiple tool calls into one exec. `swarm-pause` for emergencies; `spawn discipline` for every day.
- **Freeze is reversible, kill is not**. `SIGSTOP/SIGCONT` (`swarm-pause` / `swarm-resume`) preserves in-flight tool calls. The watchdog auto-resumes when pressure settles.
- **Cognition is not on the box**. Agent thinking runs on the inference substrate; only the tool-call path (exec spawns as hatch-execd descendants) consumes local CPU.
- **Coordinate in fleet, don't duplicate**. Before fanning out, check squawk fleet + fleet knowledgebase §2 Active Crews. Two coordinators on the same workstream is the most common self-inflicted storm.

## Feature bullets

- **Worker queue (persistent)**: `~/workspace/bin/worker-queue` — structural fix for unbounded fan-out
  - `worker-queue submit --title "x" --brief "..."` — queue work instead of spawning directly
  - `worker-queue status` — shows active/max, pending, available slots
  - `worker-queue next` — get next item when capacity is available
  - `worker-queue start <id> --agent-id <aid>` / `complete <id>` / `fail <id>` — lifecycle
  - `worker-queue config --max-workers N` — persistent cap (default: 8)
  - Queue lives in `~/workspace/queue/` (JSON files) — survives restarts
- **Send, don't spawn**: `subagent.send` steers a live worker's next steps without restarting it. Use for throttling directives ("cap parallel execs at 3, batch file ops per call"). Queued, non-interrupting by default; `interrupt: true` only to cut off actively harmful work.
- **Spawn discipline**: Cap fan-out by measured load (`load-audit` before big spawns; keep cell tool path under ~4x). One coordinator per workstream — `fleet-lock acquire <workstream>` before fanning out. Now enforced structurally via worker-queue max_workers.
- **swarm-pause / swarm-resume**: Reversible SIGSTOP/SIGCONT of the tool tree. Excludes own chain. For genuine container-pressure emergencies (PSI-verified), not for host busyness.
- **swarm-watchdog (v2, cron)**: The interlock: freezes ONLY on container cgroupv2 PSI (cpu some>30%, mem full>10%, io some>50%), auto-resumes on settle. Host metrics are alert context, never triggers. Silent when fine.
- **swarm-eject**: Last-resort control: STOP (default, reversible) or `--kill` the agent tool tree on hatch plus runaway processes on yote. For runaway processes, not for busy workers.

## Quick start

```bash
# Check worker-queue status before spawning
worker-queue status

# If at cap, submit to queue instead of spawning directly
worker-queue submit --title "My task" --brief "Original brief here"

# Or steer a live worker's next steps without restarting
subagent.send --agent-id <id> --brief "New directive"
```

## Config / optional services

- **Worker queue**: Lives in `~/workspace/queue/` (JSON files), survives restarts. Default max-workers: 8.
- **Fleet lock**: `fleet-lock acquire <workstream>` — structural one-coordinator-per-workstream enforcement.
- **Load audit**: `~/workspace/bin/load-audit` — load vs vCPUs, frozen procs, yote load.

## Dev / contributing

- Check `worker-queue status` before spawning. If at cap, submit to queue rather than spawning directly.
- Before big spawns, run `load-audit` to measure load and keep cell tool path under ~4x.
- One coordinator per workstream — use `fleet-lock acquire <workstream>` before fanning out.
- `swarm-pause` / `swarm-resume` only for genuine container-pressure emergencies (PSI-verified).

## License + security

- **License**: Open Claw source (see `skill.toml`)
- **Security**: Never `subagent.close` a healthy-but-busy worker — you orphan its in-flight work and its parent re-spawns it. Never read host `/proc/loadavg` as a per-lane signal inside the container — it is the host's weather, not a control signal. Never run `pkill -f` against tool patterns — it can SIGTERM your own exec shell.