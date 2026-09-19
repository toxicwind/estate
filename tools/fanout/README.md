# fanout — parallel command fan-out

Runs shell commands concurrently and prints a per-leg receipt. Built for
racing independent probes/checks from a single turn instead of running
them serially.

## Usage

```
fanout <timeout_s> <cmd1> [cmd2 ...]
```

Each command runs via `sh -c`. Stdout streams as each leg finishes, then
one receipt line per leg:

```
leg=N rc=<exit> ms=<wall_ms> cmd=<command>
```

- A leg exceeding `<timeout_s>` is killed and reports `rc=128`.
- Overall exit code is nonzero if any leg failed.

## Measured

2026-09-19 (cell): 4x `sleep 1` -> 1042ms parallel vs 4159ms serial (~4.0x).
Earlier run: 1.02s vs 3.50s (~3.4x).

## Stagger discipline (2026-09-19, from live fleet incidents)

This tool parallelizes *your shell commands*. **Subagent spawns** are a
different surface: the runtime runs agents concurrently, but the spawn
path contends under bulk dispatch. Rules, learned live:

- Stagger bulk spawns ~2s apart. Never fire a large identical bulk spawn
  twice — simultaneous spawns hit DB lock timeouts.
- On a DB lock timeout: retry in **smaller batches**, never the identical
  bulk call.
- A spawn error with an infra signature (compaction-model resolution
  timeout before inference, DB lock timeout, daemon-restart handle loss)
  means the work **never ran** — re-dispatch reactively on a fresh agent.
  Never mark the work failed.
- `completed` + canned `final_response` = refused. Check the digest on
  every spawn, not the status badge.

## Placement

Durable home: `sovereign/tools/fanout/` in `toxicwind/sovereign-projects`.
Working copy on awrawr-pc: `/home/toxic/bin/fanout`. Cell copy:
`~/workspace/bin/fanout` (cell storage is disposable — this repo is the
source of truth).
