# hatch/bin — hatch cell swarm tooling (canonical)

Emergency intervention + crash-prevention interlock for the agent swarm
running against the hatch runtime cell (2 vCPUs — saturates fast).

| tool | what it does |
|---|---|
| `swarm-watchdog` | Cron every 2 min. hatch load1 > 10 → `swarm-pause` + squawk alert; yote load1 > 40 → `swarm-eject --yote-only`. Tracks storm *episodes*: if load stays over threshold across consecutive runs the freeze is leaky (agents on other cells keep spawning) and it escalates once per episode. A circuit breaker, not a polling daemon. |
| `swarm-pause` | SIGSTOP-freezes the whole agent tool-call tree on the cell (excludes own chain + process group). Proven: 18 procs in one shot, 50 on a storm day. State → `~/.cache/shingle/swarm-paused.json`. |
| `swarm-resume` | Thaws everything frozen by swarm-pause (SIGCONT). |
| `swarm-eject` | The big red button: STOPs (default, reversible) or KILLs (`--kill`) the agent tool tree on hatch AND runaway processes on yote via the bridge (CPU >90% of one core; protected: bridge, squawk, tailscaled, sshd, systemd, herd serving, pitchfork). Yote PIDs recorded for resume. |
| `progress-watchdog` | Hearth watchdog (cron, 30-min pulse). One ConditionRegistry drives alerts AND pulse: identical alerts fire once (never re-fire); pulse says "all green" only on a fresh snapshot with zero active conditions, "eyes closed" on stale snapshot. Stuck-task re-announce capped at 3. Oracle alerts are process/per-request facts (loop-dead, intake backlog), never ledger-age guesses. |
| `tests/test_watchdog.py` | Unit tests (40 pass): registry dedup, domain sweeps, atomic writes, run ledger, pause verification, pulse honesty, re-announce cap, per-request intake backlog. |
| `squawk` | Cell CLI for the squawk fleet bus: `send`/`read`/`watch` over the yote bridge. `send` allocates seq atomically (per-channel `flock`, single remote allocate-and-write — fixed the 2026-09-20 stale-hunter/port-hunter 11387 collision, race-tested 8-way). |
| `watchdog_lib.py` | Shared helpers: pause verification against live /proc, run ledger. |
| `jarvis-static` | Reproducible static-analysis pipeline for the Hatch/Jarvis daemon binary: strings → env-var inventory, model-route inventory, stem-anchored compaction-token extraction, transport evidence, human-readable log-message corpus. Re-runnable after a daemon rebuild. Findings: `../audit-jarvis/`. |
| `jarvis-capture` | Bounded one-shot live capture (NOT a daemon): N-second pcap of cell egress + socket//proc/ledger snapshots → timestamped bundle + `SUMMARY.txt`. Invoke manually around real work. |
| `tcpdump` + `pcap-install.sh` | Packet-capture wrapper (`-Z root`, `$HOME`-relative) and its reproducible installer (DoH via 1.1.1.1 → Ubuntu archive debs → `pcaproot/`). |

## Deploy

Copies live at `~/workspace/bin/` on the hatch cell (the cron calls the
deployed copy). To deploy after a change: copy the file(s) to
`~/workspace/bin/` on the cell and chmod +x. The cron job is the watchdog
itself (`swarm-watchdog` entry, every 2 min).

## Rules (standing, from Chris)

- The interlock exists to protect the boxes — never disable it to make a
  workload fit.
- Never kill the live bridge daemon without a verified hot-replacement
  path; bridge-repair scripts must never kill squawk processes.
- Pause claims are verified against live /proc state (watchdog_lib.
  verify_pause) — the alert says "paused" only when processes are actually
  observed frozen.

## Docs

Fleet knowledgebase: `docs/fleet-knowledgebase.md` (repo root) § crash
interlock. Goal workspace on the cell:
`~/workspace/goals/forceful-pause-and-resume-for-agent-swarms/`.
