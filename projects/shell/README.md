# shell — the ii quickshell shell (first-class home)

This directory is the canonical home of Chris's quickshell setup on awrawr-pc.
"ii" = **Iterative Instinct**, his rebrand/fork of end-4's illogical-impulse
Hyprland shell, rendered by quickshell on **DP-1** (landscape) and **DP-2**
(portrait, 90° transform).

## Layout

| Path | What |
|---|---|
| `ii/` | The fork checkout (git submodule `shell/sovereign-end4` → `toxicwind/sovereign-end4`). Upstream base: end-4 illogical-impulse. Live config deployed from `ii/dots/.config/quickshell/ii` → `~/.config/quickshell/ii` via `ii/install.conf.yaml`. Do not restructure inside `ii/` — it tracks the fork. |
| `bin/qs-launch` | Canonical launcher. Same CLI as quickshell (`-c ii`). Auto-detects `WAYLAND_DISPLAY` + `HYPRLAND_INSTANCE_SIGNATURE`, guards single instance, sanity-checks DP-1/DP-2, detaches via setsid, logs to `~/.local/state/quickshell/launch.log`. |
| `bin/qs-restart` | Graceful stop (SIGTERM, escalates to SIGKILL) then `qs-launch`. |
| `bin/qs-doctor` | Health check: binary, config, wayland socket, hyprland instance, process liveness, **per-display quickshell layers on DP-1/DP-2**. `--repair` relaunches when dead. Exit 0 = healthy. |
| `bin/qs-logs` | Tail launcher log + newest quickshell qslog. |
| `quarantine/` | Holding pen for bizarre/unsure items. Nothing deleted, only parked. See `quarantine/README.md`. |

## Provenance

- Fork repo: `toxicwind/sovereign-end4` (fresh repo, not a GitHub fork; no upstream remote configured). HEAD `204890dbaafee5e9797ca4ef1c29ca70ac3fdddf` (main).
- Local deltas vs upstream illogical-impulse: "ii / Iterative Instinct" rebrand, `AGENTS.md`, `install.conf.yaml` (dotbot manifest), `diagnose` scripts, `system-tuning/` (limine kernel profiles, sysctl, udev), `dots-extra/`, pinned quickshell build.
- quickshell binary: built from upstream `https://git.outfoxxed.me/quickshell/quickshell` pinned at `7511545ee20664e3b8b8d3322c0ffe7567c56f7a` via `ii/sdata/dist-arch/illogical-impulse-quickshell-git/PKGBUILD` (extra Qt deps for ii widgets).
- Hyprland autostart (`~/.config/hypr/hyprland/execs.lua`) runs `qs -c ii`; `/usr/local/bin/qs` now delegates to `bin/qs-launch` (backup at `/usr/local/bin/qs.bak-20260919`).
- Displays: DP-1 `2560x1440@59.95` at `0x0` scale 1; DP-2 `2560x1440@59.95` at `2560x0` scale 1, transform 1 (portrait) — see `~/.config/hypr/monitors.lua`.

## Operations

```sh
~/sovereign/projects/shell/bin/qs-doctor            # health check
~/sovereign/projects/shell/bin/qs-doctor --repair   # fix when dead
~/sovereign/projects/shell/bin/qs-restart -c ii     # bounce
~/sovereign/projects/shell/bin/qs-logs              # recent logs
```

Known gap (2026-09-19): quickshell has no supervisor — if it dies, nothing
restarts it until next Hyprland start (this caused the 2026-09-18 19:32
outage). `qs-doctor --repair` is the manual path; a watchdog is future work.
Also: submodule name `shell/sovereign-end4` ≠ path `projects/shell/ii`
(cosmetic mismatch in `.gitmodules`; harmless, rename is a follow-up).
