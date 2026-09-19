# Quickshell home — `ii`

Canonical home for Chris's `ii` quickshell setup: the `ii` fork of end-4's illogical-impulse
(`ii/`, submodule, remote `toxicwind/sovereign-end4`) plus the first-class operations layer
around it (`bin/`, `lib/`, `deploy/`).

## Layout

- `bin/` — user entrypoints. All quickshell operations go through these:
  - `qs-launch [-c ii] [--systemd]` — canonical launcher (env auto-detect, single-instance
    guard, detached; `--systemd` = foreground mode for the unit)
  - `qs-restart`, `qs-stop` — bounce/stop, systemd-aware
  - `qs-doctor [--repair]` — health: binary, config resolution + sha256 vs canonical repo,
    wayland socket, hyprland instance, process, **IPC reachability**, unit state,
    DP-1/DP-2 layer surfaces
  - `qs-logs [n]` — launcher log + quickshell qslog + unit journal
  - `qs-install` — idempotent install: config symlink, systemd unit, hyprland entries
  - `qs-version` — binary + config + repo pins
- `lib/qs-common.sh` — shared env/pid/unit helpers (sourced by `bin/*`)
- `deploy/quickshell-ii.service` — systemd `--user` unit (`Restart=always`, `RestartSec=2`);
  installed by `qs-install` to `~/.config/systemd/user/`
- `quarantine/` — legacy material, parked never deleted (see `quarantine/MANIFEST.md`)
- `evidence/` — grim DP-1/DP-2 captures per verification run
- `AUDIT.md` — structural inventory + IPC anomaly root cause (2026-09-19)
- `ii/` — the fork. QML/config work lives here; this redo does not touch its content.

`/usr/local/bin/qs` delegates to `bin/qs-launch` (old hand-rolled version in quarantine).

## Live config

`~/.config/quickshell` → `ii/dots/.config/quickshell` (dotbot symlink, `ii/install.conf.yaml:18`).
Edits in the repo reach the live shell immediately.

## Supervision

Hyprland (`~/.config/hypr/hyprland/execs.lua`) starts the `quickshell-ii.service` unit on session
start — idempotent, no-op when already running. The unit restarts quickshell on crash
(`Restart=always`). Manual `qs -c ii` launches are single-instance guarded and converge on the
same path.

## IPC

Instance registration lives at `/run/user/1000/quickshell/by-id/<id>/`. If `qs-doctor` reports
"IPC: No running instances" while the bar renders, the registration dir was lost — restart via
`qs-restart` (recreates it). `qs-doctor` checks this on every run.
