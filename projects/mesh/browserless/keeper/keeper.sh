#!/bin/bash
# launcher for browser-keeper (pitchfork daemon browser-keeper, CDP :9223).
# Runs headed on the isolated Xvnc :99 display (Forge 2026-09-21); the keeper owns the nv-audit profile.
unset WAYLAND_DISPLAY
export DISPLAY=":99"  # Forge 2026-09-21: isolated Xvnc display, not Chris's Hyprland session
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/1000}"
export PLAYWRIGHT_BROWSERS_PATH="/home/toxic/.browserless/browsers"
mkdir -p /home/toxic/.browserless/keeper
exec node /home/toxic/sovereign/projects/mesh/browserless/keeper/keeper.js
