# Orphan sweep — 2026-09-20 (orphan-sweep, pack-fix crew)

Lane: **yote processes only** (Chris directive). /tmp file triage → kimi-unlock-audit.
Repo orphan integration → repo-integrator-max. Stale pid files stay in this lane.

Permanent deliverable: [bin/orphan-sweep.sh](bin/orphan-sweep.sh) — repeatable
process-orphan audit. This doc is the evidence log for this run.

## Process inventory (full `ps` mapped)

### Cleaned during the announcement beat (fleet seq 11317, no objections)

| pid | process | evidence | disposition |
|-----|---------|----------|-------------|
| 241217 | `python3 /tmp/dir-trap.py` | inotify trap watching `/home/toxic/sovereign/hatch/agents/ember/squawk-root` + `/home/toxic/shingle/squawk-root` (same target now). Log `/tmp/dir-trap.log` deleted; stdout `/tmp/dir-trap.out` 0 bytes. Migration it watched is committed (`5d8a02b4b3`). Redundant diagnostic. | **GONE by ~15:32** — cleaned by another fleet agent during the beat window |
| 3427996/7 | `nginx -c /tmp/nginx-8901.conf` | 33h old, serving `kodi-fleet/releases` which **does not exist**; access log = only 404 probes. No repo refs to port 8901. No owner. Zero active connections. | **GONE by ~15:32** — cleaned by another fleet agent during the beat window |

Their /tmp files (`dir-trap.py`, `dir-trap.out`, `nginx-8901.*`) are kimi-unlock-audit's
lane; /tmp/os-test.out is my own script-test artifact (6.6KB) — kimi-unlock-audit may remove it.

### LEFT + reason

| process | reason |
|---------|--------|
| cloudflared quick tunnel pid 2960494 → `https://suse-hydrocodone-motherboard-sperm.trycloudflare.com` → `localhost:8379` (exec-ws) | **UNCLAIMED, security-relevant.** Owner launcher script not found (searched ops/yote-ops/bin/tools). Started 01:08 by a "quick tunnel fallback" launcher. Left running; flagged in fleet — claim it or it dies next sweep. Note: backend still requires the bridge token (401s apply), so this is exposure, not an auth bypass. |
| tmux `tau-hyperfix` ×2 (default socket + `-L tauhyperfix`, identical 4-window layout, idle bash, no clients) | Live `wt-tau-hyperfix` worktree with active tau worker (probe ran 15:18). Duplicate layout but not touching a live worker's consoles. |
| `eval_runner.py` (sovereign-eval-wt), `bench.sh --all` + guidellm runs | guidellm lane — do not stomp (directive). |
| phone-lane `phone-vitals` + `phone-lane-keeper` | **Adopted**: systemd user units exist (`phone-lane-keeper.service`, `phone-vitals.service`). Legit infra. |
| ralph-dashboard uvicorn :8420 | Brand-new (started during sweep), likely live worker spinning it up. |
| 7 zombies under shep (2883915) | Reported in fleet; shep's owner should reap. Harmless. |
| Everything pitchfork-supervised, systemd units, desktop (wezterm/firefox/hyprland), actions-runner, docker, postgres | Known-good. |

### Reorg verification (fed to repo-integrator-max)

`shingle → hatch/agents/ember` reorg is **complete and committed** (`5d8a02b4b3
reorg: shingle->hatch/agents/ember, shingle-workspace->scratch, bridge/ canonical`).
Symlinks intact: `~/.shingle → shingle → /home/toxic/sovereign/hatch/agents/ember`.
Squawk feed/ws daemons resolve correctly through them. No half-move remains.

## Stale pid files (14 found, then cleaned by another agent mid-sweep)

Found 14 dead pid files at 15:23. By 15:30 a second `find` showed **zero** —
another fleet agent cleaned them between my scans. No action needed; noted here
so nobody re-hunts them:

- `/home/toxic/projects/moonbox-intel-v2/{github_audit,sync_daemon}.pid` (dead; no live moonbox procs)
- `/home/toxic/projects/experimental-crisis-2026/zmq_daemon.pid` (dead)
- `/home/toxic/sovereign/scratch/{service-health-poller,squawk-ws-client}.pid` (dead)
- `/home/toxic/paper-poller/state/poller.pid` (dead; poller now runs under pitchfork — pid file was a pre-pitchfork lie)
- `/home/toxic/buildsrv/buildsrvd.pid` (dead; buildsrvd runs under pitchfork)
- `sovereign-wt-provider-surgeon-2/scratch/`, `sovereign-eval-wt/scratch/`, `wt-tau-hyperfix/scratch/` — `service-health-poller.pid` + `squawk-ws-client.pid` (dead)
- `/tmp/bench-all.pid` → pids 1517072/1517076 dead (live bench is 1600478) — **fed to kimi-unlock-audit** (/tmp lane), not deleted by me

## Permanent script

`bin/orphan-sweep.sh` snapshots `ps`, classifies against the known-daemon
allowlist (herd :25100, keypool :25109, model-guard :25101, squawk, pitchfork,
oracle_loop, bridge, desktop session, MCP servers, build tooling…), skips its
own pipeline via a live `/proc` ancestor walk, skips already-exited transients,
flags unknowns with owner evidence (cwd/cmdline/start), and scans pid dirs for
stale pids. Report-only — it never kills. `orphan-sweep.sh --json` for automation.

Verified by running: final pass shows **4 residual processes, 0 real orphans** —
all transient worker commands (`pip install`, `rg`, `grep`, mesh `run.sh`)
or live project workloads. Known-daemon classification converged over 4 tuning
iterations (tmux panes, desktop infra, MCP servers, build tools all classified).

## Stale pid follow-up (recurring seed)

The `codex-readme/scratch/{service-health-poller,squawk-ws-client}.pid` pair was
deleted twice and **recreated** — something reseeds worktree scratch dirs with
this dead pair. No seeder found in `sovereign/bin|scripts` or `~/bin`. Flagged
for the fleet: whoever owns worktree bootstrapping should stop seeding these.

## Follow-ups

- cloudflared tunnel: needs an owner claim (fleet). Kill on next sweep if unclaimed.
- Duplicate tau-hyperfix tmux: revisit when wt-tau-hyperfix work lands.
- shep zombies: owner should reap children.
