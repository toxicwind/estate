#!/usr/bin/env bash
# health.sh
# Sovereign Stack Diagnostic Harness
# Checks all services defined in the local infrastructure manifest

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=ports.env
source "$SCRIPT_DIR/ports.env" 2>/dev/null || true

# ─── Configuration ────────────────────────────────────────────────────────────

# Fallback ports if ports.env is not sourced
LLAMA_HERDER="${LLAMA_HERDER:-28080}"
OPENFANG_PORT="${OPENFANG_PORT:-25004}"
PROMETHEUS_PORT="${PROMETHEUS_PORT:-9090}"
YOTE_PORT="${YOTE_PORT:-25042}"
RUST_WEB_PORT="${RUST_WEB_PORT:-8080}"
HF_DOWNLOADER="${HF_DOWNLOADER:-8081}"
WATCHDOG_PORT="${WATCHDOG_PORT:-8082}"
LANDING_PORT="${LANDING_PORT:-8083}"

# Text colors
NC='\033[0m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'

# ─── Helpers ──────────────────────────────────────────────────────────────────

log_status() {
    local service="$1"
    local status="$2"
    local port="${3:-}"
    local extra="${4:-}"
    if [ "$status" = "UP" ]; then
        printf "[${GREEN}✓${NC}] %-20s %-6s ${GREEN}%s${NC} %s\n" "$service" "$port" "UP" "$extra"
    else
        printf "[${RED}✗${NC}] %-20s %-6s ${RED}%s${NC} %s\n" "$service" "$port" "DOWN" "$extra"
    fi
}

log_header() {
    echo -e "\n${BOLD}${BLUE}$1${NC}"
    echo "$(printf '%.0s─' {1..60})"
}

# Probe an HTTP endpoint, return 0 if healthy
probe_http() {
    local url="$1"
    local timeout="${2:-2}"
    curl -sf --max-time "$timeout" "$url" >/dev/null 2>&1
}

# Check if a TCP port is listening
check_tcp_port() {
    local port="$1"
    ss -tlnp 2>/dev/null | grep -q ":${port} " || \
    netstat -tlnp 2>/dev/null | grep -q ":${port} " || \
    lsof -i TCP:"${port}" -s TCP:LISTEN >/dev/null 2>&1
}

# ─── GPU Layer ─────────────────────────────────────────────────────────────────

log_header "Compute Layer"

if ! command -v nvidia-smi &>/dev/null; then
    echo -e "[${RED}✗${NC}] nvidia-smi not found in PATH"
    GPU_AVAILABLE=false
else
    GPU_AVAILABLE=true
    GPU_INFO=$(nvidia-smi --query-gpu=name,compute_cap --format=csv,noheader 2>/dev/null || echo "unknown")
    echo -e "[${GREEN}✓${NC}] GPU: ${GPU_INFO}"

    # Detailed GPU metrics
    GPU_METRICS=$(nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw \
        --format=csv,noheader,nounits 2>/dev/null || true)
    if [ -n "$GPU_METRICS" ]; then
        echo "$GPU_METRICS" | while IFS=, read -r idx name temp util mem_used mem_total power; do
            printf "    GPU%s: %s | %s°C | %s%% | %s/%s MiB | %sW\n" \
                "$(echo "$idx" | xargs)" \
                "$(echo "$name" | xargs)" \
                "$(echo "$temp" | xargs)" \
                "$(echo "$util" | xargs)" \
                "$(echo "$mem_used" | xargs)" \
                "$(echo "$mem_total" | xargs)" \
                "$(echo "$power" | xargs)"
        done
    fi
fi

# ─── Service Registry ──────────────────────────────────────────────────────────

log_header "Service Health"

declare -a CHECKS=(
    "${LLAMA_HERDER}:llama-swap:/health"
    "${OPENFANG_PORT}:openfang:/api/health"
    "${PROMETHEUS_PORT}:prometheus:/-/healthy"
    "${YOTE_PORT}:yote:/health"
    "${RUST_WEB_PORT}:rust-dash:/health"
    "${HF_DOWNLOADER}:hf-downloader:/health"
    "${WATCHDOG_PORT}:watchdog:/health"
    "${LANDING_PORT}:landing:/health"
)

UP_COUNT=0
DOWN_COUNT=0

for spec in "${CHECKS[@]}"; do
    IFS=: read -r port name path <<<"$spec"

    # Primary check: health endpoint
    if probe_http "http://127.0.0.1:${port}${path}"; then
        log_status "$name" "UP" "$port"
        ((UP_COUNT++)) || true
        continue
    fi

    # Fallback for llama-swap: try /v1/models if /health fails
    if [ "$name" = "llama-swap" ] && probe_http "http://127.0.0.1:${port}/v1/models"; then
        log_status "$name" "UP" "$port" "(fallback /v1/models)"
        ((UP_COUNT++)) || true
        continue
    fi

    # Fallback for prometheus: try /metrics if /-/healthy fails
    if [ "$name" = "prometheus" ] && probe_http "http://127.0.0.1:${port}/metrics"; then
        log_status "$name" "UP" "$port" "(fallback /metrics)"
        ((UP_COUNT++)) || true
        continue
    fi

    # Check if port is at least bound (process is alive but endpoint misconfigured)
    if check_tcp_port "$port"; then
        log_status "$name" "DOWN" "$port" "(port bound, endpoint unreachable)"
    else
        log_status "$name" "DOWN" "$port" "(port not bound)"
    fi
    ((DOWN_COUNT++)) || true
done

# ─── llama-swap Deep Inspection ───────────────────────────────────────────────

log_header "llama-swap Runtime"

if probe_http "http://127.0.0.1:${LLAMA_HERDER}/v1/models" 3; then
    MODELS=$(curl -sf --max-time 3 "http://127.0.0.1:${LLAMA_HERDER}/v1/models" 2>/dev/null | \
        jq -r '.data[].id' 2>/dev/null || echo "(parse error)")
    if [ -n "$MODELS" ] && [ "$MODELS" != "(parse error)" ]; then
        echo "Registered models:"
        echo "$MODELS" | while read -r model; do
            echo "  • $model"
        done
    else
        echo "  (no models registered or parse failed)"
    fi
else
    echo "  (llama-swap API unreachable)"
fi

if probe_http "http://127.0.0.1:${LLAMA_HERDER}/running" 3; then
    echo ""
    echo "Running models:"
    curl -sf --max-time 3 "http://127.0.0.1:${LLAMA_HERDER}/running" 2>/dev/null | \
        jq -r '.[] | "  • \"\(.id)\" [\(.state)] port=\(.port // \"null\") pid=\(.pid // \"null\")"' 2>/dev/null || \
        echo "  (parse error)"
else
    echo "  (no models currently running)"
fi

# ─── Yote Metrics ──────────────────────────────────────────────────────────────

log_header "Yote Orchestrator"

if probe_http "http://127.0.0.1:${YOTE_PORT}/metrics" 3; then
    echo "Prometheus metrics available at :${YOTE_PORT}/metrics"
    curl -sf --max-time 3 "http://127.0.0.1:${YOTE_PORT}/metrics" 2>/dev/null | head -20 || true
else
    echo "  (metrics endpoint unreachable)"
fi

# ─── Summary ───────────────────────────────────────────────────────────────────

log_header "Summary"

TOTAL=$((UP_COUNT + DOWN_COUNT))
if [ "$DOWN_COUNT" -eq 0 ]; then
    echo -e "${GREEN}All ${TOTAL} services healthy${NC}"
    exit 0
elif [ "$UP_COUNT" -eq 0 ]; then
    echo -e "${RED}All ${TOTAL} services down${NC}"
    exit 2
else
    echo -e "${YELLOW}${UP_COUNT}/${TOTAL} services healthy${NC} (${DOWN_COUNT} down)"
    exit 1
fi
