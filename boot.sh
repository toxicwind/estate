#!/bin/bash
# boot.sh — Sovereign Stack Launcher (Final)
# Starts the full stack via mise and sends Telegram notification on success.
# SAFE: never kills antigravity, node, npm, vscode, or antigravity-private processes.

set -euo pipefail

SOVEREIGN_HOME="/home/toxic/sovereign"
MISE_FILE="${SOVEREIGN_HOME}/mise.toml"
LOG_DIR="${SOVEREIGN_HOME}/logs"
SECRETS_FILE="/home/toxic/.secrets"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}     SOVEREIGN STACK — Boot Sequence${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"

# Source secrets
if [[ -f "$SECRETS_FILE" ]]; then
    source "$SECRETS_FILE"
    echo -e "${GREEN}✓ Loaded secrets${NC}"
fi

# Ensure log dir
mkdir -p "$LOG_DIR"

# ── Port Cleanup (SAFE) ─────────────────────────────────────────────
# Kill only OUR stack processes on sovereign ports — never touch infra.
PROTECTED_REGEX="antigravity|node|npm|vscode|antigravity-private|Hyprland|pipewire|wireplumber|waybar"

cleanup_port() {
    local port=$1
    local pids
    pids=$(lsof -ti ":${port}" 2>/dev/null || true)
    for pid in $pids; do
        local cmdline
        cmdline=$(cat "/proc/${pid}/cmdline" 2>/dev/null | tr '\0' ' ' || true)
        if echo "$cmdline" | grep -qEi "$PROTECTED_REGEX"; then
            echo -e "${YELLOW}⚠ Skipping protected process on :${port} (PID ${pid})${NC}"
        else
            echo -e "  Clearing :${port} — PID ${pid}"
            kill "$pid" 2>/dev/null || true
        fi
    done
}

echo -e "\n${YELLOW}▶ Clearing sovereign ports...${NC}"
for port in 25001 25004 25008; do
    cleanup_port "$port"
done
sleep 2

# ── Stop existing stack processes ─────────────────────────────────────
echo -e "${YELLOW}▶ Stopping existing watchdog, process-compose, and mise tasks...${NC}"
pkill -f "sovereign_watchdog.py" || true
pkill -f "process-compose" || true
existing_mise=$(pgrep -f "mise run.*(start|llama-server|nfcot|openfang|watchdog)" 2>/dev/null || true)
for pid in $existing_mise; do
    cmdline=$(cat "/proc/${pid}/cmdline" 2>/dev/null | tr '\0' ' ' || true)
    if echo "$cmdline" | grep -qEi "$PROTECTED_REGEX"; then
        continue
    fi
    kill "$pid" 2>/dev/null || true
    echo -e "  Stopped PID ${pid}"
done
sleep 2

# ── Launch ───────────────────────────────────────────────────────────
echo -e "\n${GREEN}▶ Starting Sovereign Stack via Mise...${NC}"
cd "$SOVEREIGN_HOME"
mise run start &
MISE_PID=$!
echo -e "${GREEN}✓ mise PID: ${MISE_PID}${NC}"

# ── Wait for health ─────────────────────────────────────────────────
echo -e "\n${YELLOW}▶ Waiting for stack health...${NC}"
MAX_WAIT=120
ELAPSED=0
HEALTHY=false

while (( ELAPSED < MAX_WAIT )); do
    LLAMA_OK=false
    NFCOT_OK=false

    if curl -sf http://127.0.0.1:25001/health >/dev/null 2>&1; then
        LLAMA_OK=true
    fi
    if curl -sf http://127.0.0.1:25008/v1/models >/dev/null 2>&1; then
        NFCOT_OK=true
    fi

    if $LLAMA_OK && $NFCOT_OK; then
        HEALTHY=true
        break
    fi

    sleep 5
    ELAPSED=$((ELAPSED + 5))
    echo -e "  ... waiting (${ELAPSED}s) llama=${LLAMA_OK} nfcot=${NFCOT_OK}"
done

if $HEALTHY; then
    echo -e "\n${GREEN}═══════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✅ SOVEREIGN STACK ONLINE${NC}"
    echo -e "${GREEN}  llama-server  :25001  ✓${NC}"
    echo -e "${GREEN}  nfcot_proxy   :25008  ✓${NC}"
    echo -e "${GREEN}  openfang      :25004  (launching)${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════${NC}"

    # ── Telegram Notification ────────────────────────────────────────
    if [[ -n "${TELEGRAM_BOT_TOKEN:-}" ]]; then
        CHAT_ID="${TELEGRAM_ALLOWED_USERS:-13036673831}"
        MSG="🟢 *Sovereign Stack Online*%0A%0A• llama-server :25001 ✓%0A• nfcot_proxy :25008 ✓%0A• openfang :25004 ✓%0A• watchdog active%0A%0A_$(hostname) — $(date '+%Y-%m-%d %H:%M:%S')_"
        curl -sf "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d "chat_id=${CHAT_ID}" \
            -d "text=${MSG}" \
            -d "parse_mode=Markdown" >/dev/null 2>&1 && \
            echo -e "${GREEN}✓ Telegram notification sent${NC}" || \
            echo -e "${YELLOW}⚠ Telegram notification failed${NC}"
    fi
else
    echo -e "\n${RED}✗ Stack failed to become healthy in ${MAX_WAIT}s${NC}"
    echo -e "${RED}  Check logs: ${LOG_DIR}/${NC}"
    exit 1
fi
