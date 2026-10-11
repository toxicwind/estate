# AUDIT — /home/toxic/sovereign/projects/shell

Inventory of 2026-09-19 (UTC). Evidence, not opinions. Read-only probe; nothing moved or deleted.

## A. Layout

```
projects/shell/
├── README.md
├── AUDIT.md            (this file)
├── bin/
│   ├── qs-launch       canonical launcher (guarded, env-detecting, detached)
│   ├── qs-restart      graceful bounce (systemd-aware)
│   ├── qs-stop         SIGTERM→SIGKILL stop (systemd-aware)
│   ├── qs-doctor       health: binary/config-hash/IPC/unit/layers
│   ├── qs-logs         launcher log + qslog + unit journal
│   ├── qs-install      idempotent install (symlink, unit, hyprland entries)
│   └── qs-version      binary + config + repo pins
├── lib/
│   └── qs-common.sh    shared env/pid/unit helpers, sourced by bin/*
├── deploy/
│   └── quickshell-ii.service   systemd --user unit (Restart=always)
├── quarantine/
│   ├── README.md       park-first policy
│   └── MANIFEST.md     what is parked and why
├── evidence/
│   └── <UTC-ts>/      grim DP-1/DP-2 captures per verification run
└── ii/                 the fork (git submodule, see B)
```

## B. The `ii` fork (untouched by this redo)

- Git submodule: `.git` gitfile → `/home/toxic/sovereign/.git/modules/shell/sovereign-end4`;
  submodule NAME `shell/sovereign-end4` ≠ checkout path `projects/shell/ii` (cosmetic mismatch, noted).
- Remote: `https://github.com/toxicwind/sovereign-end4.git` (fresh repo, not a GitHub fork; no upstream remote).
- Top level: `AGENTS.md`, `diagnose`, `diagnose.result`, `docs/`, `dots/`, `dots-extra/`, `.github/`,
  `install.conf.yaml`, `LICENSE`, `licenses/`, `packages.arch.txt`, `README.md`, `scripts/` (only
  `apply-keyring-pam.sh`), `sdata/` (incl. `dist-arch/illogical-impulse-quickshell-git/PKGBUILD`),
  `system-tuning/`.
- Live config: `ii/dots/.config/quickshell/ii/` (shell.qml, GlobalStates.qml, settings.qml,
  modules/, services/, panelFamilies/, scripts/, assets/, defaults/).
- **Deployment is a real symlink, not a copy**: `/home/toxic/.config/quickshell`
  → `/home/toxic/sovereign/projects/shell/ii/dots/.config/quickshell` (installed 2026-09-14 18:51,
  per `install.conf.yaml:18`). Verified same inode for shell.qml (113747522) in both paths.
  Edits in the repo reach the live config immediately (no redeploy step needed for quickshell).

## C. Launch paths — who can start quickshell

| # | Path | Type | Guarded? |
|---|---|---|---|
| 1 | `~/.config/hypr/hyprland/execs.lua:6` → `systemctl --user start quickshell-ii.service` | Autostart (Hyprland start hook; was `qs -c $qsConfig` one-shot, now unit start) | yes (unit is idempotent) |
| 2 | `bin/qs-launch` (directly, or via `/usr/local/bin/qs`) | Manual CLI | yes (pgrep guard) |
| 3 | `bin/qs-restart` | Manual bounce | yes (stops first) |
| 4 | `bin/qs-doctor --repair` | Manual repair | yes |
| 5 | `~/.config/hypr/hyprland/keybinds.lua` CTRL+SUPER+R → `qs-restart -c $qsConfig` | Keybind (was `killall ydotool qs quickshell; qs -c $qsConfig &` — unguarded) | yes (fixed by qs-install) |
| 6 | `/usr/bin/qs` → `/usr/bin/quickshell` | Legacy symlink alias, shadowed by `/usr/local/bin/qs` in PATH | no (silent bypass if PATH order changes) |
| 7 | systemd unit `quickshell-ii.service` | Supervisor (Restart=always, RestartSec=2) | yes (systemd) |

Previous gaps closed: execs.lua one-shot (crash left it dead) is now a unit start; the CTRL+SUPER+R
keybind no longer bypasses the guard; `qs -c ii ipc …` client calls (cliphistService updates from
wl-paste watchers, keybinds) work again once the instance registers.

## D. Dead/duplicate/stale references

- `/usr/local/bin/qs.bak-20260919` — backup of the pre-redo hand-rolled launcher. Parked in
  quarantine/MANIFEST.md; the live `/usr/local/bin/qs` delegates to `bin/qs-launch`.
- `/usr/bin/qs` legacy symlink → `/usr/bin/quickshell`: harmless while `/usr/local/bin` precedes
  `/usr/bin` in PATH; documented as the one remaining unguarded path (removing it needs root and
  touches a package-owned file — left in place).
- `quarantine/` holds only the old launcher backup + MANIFEST; no live code references it.
- README provenance (prior revision): the redo commit `fff4dcae9f` is on origin/main; ii fork HEAD
  at audit time was `88705ea2` (README's recorded hash `204890db` was one commit back — updated).

## E. IPC anomaly (2026-09-19)

Symptom: `quickshell -c ii ipc show` → `No running instances for "/home/toxic/.config/quickshell/ii/shell.qml"`
while PID 786264 rendered on DP-1/DP-2.

Root cause: the instance's IPC registration directory `/run/user/1000/quickshell/by-id/oougod8llt`
(log.log, log.qslog, instance.lock, socket) was deleted out from under the live process —
`/proc/786264/fd` showed the (deleted) targets. The by-path registration
(`by-path/<md5(config path)>` → `by-shell/<md5>` → `by-id/<id>`) dangled, so the IPC client found
no instances. Functional casualty: `qs -c ii ipc call cliphistService update` (wl-paste watchers,
keybinds) silently failed. Fix: clean restart recreates by-id registration; qs-doctor now checks
IPC reachability and fails loudly if it regresses.

## F. Git state (pre-existing, preserved)

- Sovereign repo root `/home/toxic/sovereign`; `fff4dcae9f` verified on origin/main
  (`merge-base --is-ancestor fff4dcae9f origin/main` → yes).
- Pre-existing dirt, NOT touched by this redo:
  - `M pitchfork.toml` — +5 comment lines (chat-coord retirement note, unrelated).
  - `m projects/shell/ii` — submodule content dirty: `dots/.config/fuzzel/fuzzel_theme.ini`,
    `dots/.config/hypr/hyprland/colors.lua`, `dots/.config/hypr/hyprlock/colors.conf`.
- Many pre-existing untracked scratch dirs at repo level — unrelated, left alone.
- Pre-push hook: absent in `/home/toxic/sovereign/.git/hooks/` (only `pre-commit`); installed
  from `/home/toxic/bin/pre-push` before pushing this rework.
