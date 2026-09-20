# The runtime cell

## The one-line version

Every Muse session runs inside a **disposable systemd-nspawn container** (the "runtime cell", machine name `htch-runtime`) on a host VM. The agent daemon (`hatch daemon`) lives inside the cell. `/home/hatch` is a persistent volume (the "reliable volume", RV); the container root filesystem is fresh on every boot. When the platform replaces the cell, everything outside `/home/hatch` — journal, wtmp, boot ID, `/tmp` — is born new. That is why "random disconnects" nuke subagents and leave no local audit trail.

## How we know (evidence)

| Observation | Source |
|---|---|
| Cell is the nspawn machine `htch-runtime`; its "leader" (PID 1) is resolved via `machinectl show htch-runtime -p Leader` | `/opt/hatch/runtime-cell/runtime-cell-entry.sh` |
| Launched via `systemd-nspawn --boot --directory=<rootfs> --machine=htch-runtime --private-users-ownership=map` | `/opt/hatch/runtime-cell/launch-daemon.sh` |
| `/home/hatch` is "the RV home is persistent user state"; a stub is replaced when the reliable volume attaches | `/opt/hatch/runtime-cell/pre-start.sh` |
| Fresh `boot_id`, `wtmp`, journal after every restart; `who -b` shows a new boot each time | observed 2026-09-14 (two replacements in one day) |
| Daemon cmdline: `hatch daemon --runtime-cell-leader=<pid>` | `ps` inside the cell |
| Host spawner `spawnd` (`queue-runtime-cell-bootstrap`, `ensure-guest-home-mountpoints`) | `launch-daemon.sh`, `pre-start.sh` |
| Credential broker `authd` on `/run/hatch/auth/authd.sock`; callers authenticated by cgroup membership | `runtime-cell-entry.sh` |
| Egress via `hatch-egress-proxy:3128` ("Sentinel-routed"); in-cell DNS is deliberately dead; TLS-intercept CA at `/run/hatch/egress-tls/ca-bundle.pem` | `guest.env`, `guest-runtime-env.sh` |
| Platform codename `hatch` (binaries `hatch`/`spawnd`/`authd`/`hatch-execd`); `JARVIS` only the cell-internal codename | `guest.env`, binary names |
| Per-channel skill/binary gating: `skill-scopes.conf` / `bin-scopes.conf` overlay revealed items into the cell | `launch-daemon.sh` |

## Lifecycle

1. Host `spawnd` runs `pre-start.sh` (guest home mountpoints, trust store, rootfs at `/var/lib/hatch-runtime/rootfs`).
2. `launch-daemon.sh` boots the nspawn container; per-channel scoped skills/binaries are overlay-mounted in.
3. Cell signals readiness via `/run/hatch/runtime-cell/runtime-cell.ready`.
4. Host `control-daemon.sh` resolves the leader PID, joins the cell cgroup, enters all namespaces, and execs `hatch daemon --runtime-cell-leader=<pid>` as guest root.
5. `hatch-execd` serves tool execution; subagents are logical agents run as daemon tool calls (no separate OS processes observed 2026-09-14) — so when the cell dies, they all die instantly.

## Persistence model

- **Persists**: `/home/hatch` (reliable volume) — workspace, memory files, skills, cron definitions.
- **Ephemeral**: everything else — container rootfs, journald, wtmp, boot ID, `/tmp` (tmpfs), the whole process tree.
- **External and persistent**: the Postgres behind `agent.*` (agents, subagent_spawns, restart checkpoints) — the only real audit trail across replacements.

## Naming map

- Product: **Muse** (muse.ai); models: Muse Spark (Muse family), built by Meta.
- Platform codename: **hatch** (first-class). `JARVIS` is only the runtime-cell internal codename (`JARVIS_HOME`, `JARVIS_CD_CHANNEL`).
- Binaries: `hatch` (agent daemon), `spawnd` (host spawner), `authd` (credential broker), `hatch-execd` (tool executor).

## Process parentage (traced 2026-09-14, uid=0 inside the cell)

From `/` downward, verified via `ps -ef --forest` and
`/proc/<pid>/status` (`NSpid`/`PPid`):

- **Above the cell (host, invisible from inside):** the spawner. Both
  `hatch daemon --runtime-cell-leader=<pid>` and `hatch-execd` report
  **PPid 0** — their parent lives outside this PID namespace. That is as
  high as the trace goes from inside; the host side is unobservable here.
- **PID 1:** `/usr/lib/systemd/systemd` — the cell init. Direct parent of
  every in-cell daemon (ws bridge, squawk push client, buildsrvd,
  proxy_fwd, health poller, journald).
- **The fleet is not processes.** Subagents/workers have no OS PIDs; they
  are logical rows in the external Postgres (`agent.agents`,
  `agent.subagent_spawns`) executed as `hatch-execd` tool calls. Consequence:
  the DB can report agents "running" with zero processes behind them
  (ghost rows, dangling activity cards) — process inspection alone cannot
  audit the fleet; the DB ledger is the source of truth.
