#!/bin/bash
# launcher for browser-keeper (pitchfork daemon browser-keeper, CDP :9223).
# Runs headed on the Wayland session; the keeper owns the nv-audit profile.
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/1000}"
export PLAYWRIGHT_BROWSERS_PATH="/home/toxic/.browserless/browsers"
mkdir -p /home/toxic/.browserless/keeper
exec node /home/toxic/sovereign/projects/mesh/browserless/keeper/keeper.js
