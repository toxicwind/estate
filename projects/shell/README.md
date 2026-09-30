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

## WezTerm

Terminal emulator: `wezterm` (GPU-accelerated, listed in `ii/packages.arch.txt`).

- **Config**: `~/.config/wezterm/wezterm.lua` → `ii/dots/.config/wezterm/wezterm.lua` (symlinked)
  - Lua-first config with Catppuccin Mocha colors, JetBrains Mono/Fira Code fonts
  - **Tab bar enabled** (`enable_tab_bar = true`, `use_fancy_tab_bar = false`, `tab_bar_at_bottom = false`, `hide_tab_bar_if_only_one_tab = false`) with active/inactive/new tab colors
  - **Tab switching**: `Ctrl+Tab` / `Ctrl+Shift+Tab`, `LEADER + [` / `LEADER + ]`, `LEADER + 1-9`, `ALT + 1-9`
  - **Window switching**: `LEADER + p` / `LEADER + n` (previous/next window)
  - **Quick actions**: `Ctrl+Shift+T` (new tab), `Ctrl+Shift+W` (close tab), `LEADER + o` (tab navigator), `LEADER + w` (launcher args)
  - **Pane navigation**: `LEADER + h/j/k/l`, `LEADER + v/s` (splits)
  - **OSC 133 semantic prompt markers** via `wezterm.on("exec-before")` and `wezterm.on("window-created")` hooks
- **OSC 133 shell integration**: `~/.config/wezterm/shell-integration.sh` → `ii/dots/.config/wezterm/shell-integration.sh` — bash-side `PROMPT_COMMAND` + `DEBUG` trap for `A`/`B`/`C`/`D;<status>` semantic markers. Sourced by `.bashrc` when `TERM_PROGRAM=WezTerm`.
- **Command palette**: `wezterm-cmdpicker` plugin (`~/.config/wezterm/plugins/wezterm-cmdpicker` → `ii/dots/.config/wezterm/plugins/wezterm-cmdpicker` → fork `toxicwind/wezterm-cmdpicker` at `abidibo/wezterm-cmdpicker` upstream).
- **Shell search wrappers**: `.bashrc.env` provides `find()` (ffs), `grep()` (ffs local + `gh search code --github`), `findgh()` (`gh search repos`), and `ff()`/`ffa()`/`ffr()`/`ffo()` shorthand aliases.

### Repo layout

| Path | Content |
|---|---|
| `ii/dots/.config/wezterm/shell-integration.sh` | Original bash OSC 133 script |
| `ii/dots/.config/wezterm/plugins/wezterm-cmdpicker/` | Forked cmdpicker plugin repo |
| `ii/dots/.config/wezterm/wezterm.lua` | Active Lua-first config (tab bar + keybindings) |
| `ii/dots/.config/wezterm/shell-integration.sh` | Symlink to shell repo script |
| `ii/dots/.config/wezterm/plugins/wezterm-cmdpicker` | Symlink to shell repo plugin |
| `~/.config/wezterm` | **Symlink** → `ii/dots/.config/wezterm` (managed by Dotbot via `ii/install.conf.yaml`) |