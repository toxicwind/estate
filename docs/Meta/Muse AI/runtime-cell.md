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
| Internal codename `JARVIS` (`JARVIS_HOME=/home/hatch`, per-VM `JARVIS_CD_CHANNEL`) | `guest.env` |
| Per-channel skill/binary gating: `skill-scopes.conf` / `bin-scopes.conf` overlay revealed items into the cell | `launch-daemon.sh` |

## Lifecycle

1. Host `spawnd` runs `pre-start.sh` (guest home mountpoints, trust store, rootfs at `/var/lib/hatch-runtime/rootfs`).
2. `launch-daemon.sh` boots the nspawn container; per-channel scoped skills/binaries are overlay-mounted in.
3. Cell signals readiness via `/run/hatch/runtime-cell/runtime-cell.ready`.
4. Host `control-daemon.sh` resolves the leader PID, joins the cell cgroup, enters all namespaces, and execs `hatch daemon --runtime-cell-leader=<pid>` as guest root.
5. `hatch-execd` serves tool execution; subagents run as daemon children — so when the cell dies, they all die instantly.

## Persistence model

- **Persists**: `/home/hatch` (reliable volume) — workspace, memory files, skills, cron definitions.
- **Ephemeral**: everything else — container rootfs, journald, wtmp, boot ID, `/tmp` (tmpfs), the whole process tree.
- **External and persistent**: the Postgres behind `agent.*` (agents, subagent_spawns, restart checkpoints) — the only real audit trail across replacements.

## Naming map

- Product: **Muse** (muse.ai); models: Muse Spark (Muse family), built by Meta.
- Internal platform: **Jarvis**.
- Binaries: `hatch` (agent daemon), `spawnd` (host spawner), `authd` (credential broker), `hatch-execd` (tool executor).
