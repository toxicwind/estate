#!/usr/bin/env bash
# health.sh — Sovereign Stack Diagnostic Harness
set -euo pipefail

# ─── Ports (SSOT: mise.toml [env]) ───────────────────────────────────────────
LLAMA_SWAP_PORT="${LLAMA_SWAP_PORT:-25100}"
RUST_WEB_PORT="${RUST_WEB_PORT:-25101}"
YOTE_PORT="${YOTE_PORT:-25102}"
OPENFANG_PORT="${OPENFANG_PORT:-25103}"
WATCHDOG_PORT="${WATCHDOG_PORT:-25104}"
PROMETHEUS_PORT="${PROMETHEUS_PORT:-25105}"
HF_DOWNLOADER_PORT="${HF_DOWNLOADER_PORT:-25106}"
NULL_G_PORT="${NULL_G_PORT:-8787}"

# ─── Colors ───────────────────────────────────────────────────────────────────
NC='\033[0m'; GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[0;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'

log_status() {
  local kind="$1" name="$2" port="$3" extra="${4:-}"
  if [[ "$kind" == "UP" ]]; then
    printf "[${GREEN}✓${NC}] %-20s :%-5s ${GREEN}UP${NC} %s\n" "$name" "$port" "$extra"
  else
    printf "[${RED}✗${NC}] %-20s :%-5s ${RED}DOWN${NC} %s\n" "$name" "$port" "$extra"
  fi
}

log_header() { echo -e "\n${BOLD}${BLUE}$1${NC}"; printf '%.0s─' {1..60}; }

probe_http() { curl -sf --max-time "${2:-3}" "$1" >/dev/null 2>&1; }

# ─── GPU ──────────────────────────────────────────────────────────────────────
log_header "Compute Layer"
if command -v nvidia-smi &>/dev/null; then
  nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total \
    --format=csv,noheader,nounits 2>/dev/null | while IFS=, read -r idx name temp util mem_used mem_total; do
    printf "  GPU%s: %s | %s°C | %s%% | %s/%s MiB\n" "$(echo "$idx"|xargs)" "$(echo "$name"|xargs)" \
      "$(echo "$temp"|xargs)" "$(echo "$util"|xargs)" "$(echo "$mem_used"|xargs)" "$(echo "$mem_total"|xargs)"
  done
else
  echo -e "  [${RED}✗${NC}] nvidia-smi not found"
fi

# ─── Services ─────────────────────────────────────────────────────────────────
log_header "Service Health"

CORE=0; CORE_FAIL=0; OPT=0; OPT_FAIL=0

check() {
  local kind="$1" name="$2" port="$3" path="$4"
  local url="http://127.0.0.1:${port}${path}"
  if probe_http "$url"; then
    log_status "UP" "$name" "$port"
    ((CORE++)) || true
  else
    log_status "DOWN" "$name" "$port"
    ((CORE_FAIL++)) || true
  fi
}

opt() {
  local kind="$1" name="$2" port="$3" path="$4"
  local url="http://127.0.0.1:${port}${path}"
  if probe_http "$url"; then
    log_status "UP" "$name" "$port"
    ((OPT++)) || true
  else
    log_status "DOWN" "$name" "$port"
    ((OPT_FAIL++)) || true
  fi
}

# Core
check  llama-swap     "$LLAMA_SWAP_PORT"  /health
check  openfang       "$OPENFANG_PORT"    /api/health
check  prometheus     "$PROMETHEUS_PORT"  /-/healthy
check  rust-web       "$RUST_WEB_PORT"    /health

# Optional
opt  yote             "$YOTE_PORT"        /health
opt  null-g           "$NULL_G_PORT"      /health
opt  hf-downloader    "$HF_DOWNLOADER_PORT" /api/health

# ─── llama-swap Deep Inspection ───────────────────────────────────────────────
log_header "llama-swap Runtime"

if probe_http "http://127.0.0.1:${LLAMA_SWAP_PORT}/v1/models" 3; then
  echo "Registered models:"
  curl -sf --max-time 3 "http://127.0.0.1:${LLAMA_SWAP_PORT}/v1/models" | \
    jq -r '.data[].id' 2>/dev/null | while read -r m; do echo "  • $m"; done
else
  echo "  (llama-swap API unreachable)"
fi

# ─── Summary ──────────────────────────────────────────────────────────────────
log_header "Summary"
TOTAL=$((CORE + CORE_FAIL + OPT + OPT_FAIL))
if [[ "$CORE_FAIL" -gt 0 ]]; then
  echo -e "${RED}CORE RED: ${CORE_FAIL} core services down${NC}"
  exit 1
elif [[ "$OPT_FAIL" -gt 0 ]]; then
  echo -e "${YELLOW}CORE GREEN, ${OPT_FAIL} optional down${NC}"
  exit 0
else
  echo -e "${GREEN}All ${TOTAL} services healthy${NC}"
  exit 0
fi
