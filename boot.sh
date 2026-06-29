#!/bin/bash
set -euo pipefail
SOVEREIGN_HOME="/home/toxic/sovereign"
SECRETS_FILE="/home/toxic/.secrets"
LOG_DIR="$SOVEREIGN_HOME/logs"

source "$SECRETS_FILE" 2>/dev/null || true
mkdir -p "$LOG_DIR"

PROTECTED_REGEX="antigravity|node|npm|vscode|antigravity-private|Hyprland|pipewire|wireplumber|waybar"

cleanup_port() {
    local port=$1
    local pids=$(lsof -ti ":${port}" 2>/dev/null || true)
    for pid in $pids; do
        local cmdline=$(cat "/proc/${pid}/cmdline" 2>/dev/null | tr '\0' ' ' || true)
        if echo "$cmdline" | grep -qEi "$PROTECTED_REGEX"; then
            echo "⚠ Skipping protected process on :${port} (PID ${pid})"
        else
            kill "$pid" 2>/dev/null || true
        fi
    done
}

for port in 25001 25004 25008; do cleanup_port "$port"; done
sleep 2

pkill -f "sovereign_watchdog.py" || true
pkill -f "process-compose" || true

echo "▶ Starting Sovereign Stack..."
cd "$SOVEREIGN_HOME"
devenv up -d || { echo "✗ devenv up failed"; exit 1; }
echo "✅ SOVEREIGN STACK ONLINE"
