# quarantine/MANIFEST.md

Legacy material parked during the 2026-09-19 redo. Park-first, never delete.

| File | Origin | Why parked |
|---|---|---|
| `qs.bak-20260919` | `/usr/local/bin/qs` before the redo (112 bytes, root-owned) | Hand-rolled pre-redo launcher: `export XDG_RUNTIME_DIR/WAYLAND_DISPLAY; exec /usr/bin/quickshell "$@"`. Superseded by the delegating wrapper → `bin/qs-launch`. Kept for provenance. |

Nothing else is parked yet. `README.md` (the prior policy doc) stays as-is.

| `execs.lua.bak-20260918T201147` | `~/.config/hypr/hyprland/execs.lua` (via ii dots) | Pre-redo Hyprland start hook: `hl.exec_cmd("qs -c $qsConfig")` one-shot. Superseded by `systemctl --user start quickshell-ii.service`. |
| `keybinds.lua.bak-20260918T201147` | `~/.config/hypr/hyprland/keybinds.lua` (via ii dots) | Pre-redo CTRL+SUPER+R: `killall ydotool qs quickshell; qs -c $qsConfig &`. Superseded by `qs-restart -c $qsConfig`. |
