#!/usr/bin/env bash
# Dynamic Configuration Loader - NO HARDCODING
# Reads from config files, adapts to any setup
# Usage: source this file

set -euo pipefail

# =============================================================================
# CONFIG FILES (SSOT - Single Source of Truth)
# =============================================================================
export SOVEREIGN_ROOT="${SOVEREIGN_ROOT:-$HOME/sovereign}"
export PORTS_ENV="$SOVEREIGN_ROOT/config/ports.env"
export SECRETS_FILE="$HOME/.secrets"

# =============================================================================
# LOAD CONFIGURATION FROM FILES
# =============================================================================
load_config() {
    [[ -f "$PORTS_ENV" ]] && { set -a; source "$PORTS_ENV"; set +a; }
    [[ -f "$SECRETS_FILE" ]] && { set -a; source "$SECRETS_FILE"; set +a; }
}

# =============================================================================
# GET PORT - reads from env, then ports.env, then dynamic discovery
# =============================================================================
get_port() {
    local service="$1"
    local var_name
    # Convert service name to env var (e.g., llama-swap -> LLAMA_SWAP_PORT)
    var_name=$(echo "${service}" | tr '[:lower:]-' '[:upper:]_')_PORT
    
    # Check env vars first
    if [[ -n "${!var_name:-}" ]]; then
        echo "${!var_name}"
        return 0
    fi
    
    # Check ports.env directly
    if [[ -f "$PORTS_ENV" ]]; then
        local val
        val=$(grep -E "^${var_name}=" "$PORTS_ENV" 2>/dev/null | head -1 | cut -d'=' -f2 | tr -d '"' | tr -d "'" | xargs)
        [[ -n "$val" ]] && { echo "$val"; return 0; }
    fi
    
    # Dynamic discovery - check what's actually running
    discover_port "$service"
}

# =============================================================================
# DISCOVER PORT - find what's actually listening
# =============================================================================
discover_port() {
    local service="$1"
    # Use ss/netstat to find listening ports for this service
    local pid
    pid=$(pgrep -f "$service" 2>/dev/null | head -1)
    if [[ -n "$pid" ]]; then
        local port
        port=$(ss -tlnp 2>/dev/null | grep "pid=$pid" | awk '{print $4}' | grep -oP '\d+$' | head -1)
        [[ -n "$port" ]] && { echo "$port"; return 0; }
    fi
    echo "0"
}

# =============================================================================
# GET URL - dynamic from port
# =============================================================================
get_url() {
    local service="$1"
    local port
    port=$(get_port "$service")
    echo "http://127.0.0.1:${port}"
}

# =============================================================================
# CHECK HEALTH - dynamic endpoint discovery
# =============================================================================
check_health() {
    local service="$1"
    local base_url
    base_url=$(get_url "$service")
    
    # Try common health endpoints
    for endpoint in "/health" "/api/health" "/-/healthy" "/ping"; do
        if curl -sf --max-time 3 "${base_url}${endpoint}" >/dev/null 2>&1; then
            echo "OK:${endpoint}"
            return 0
        fi
    done
    
    echo "FAIL"
    return 1
}

# =============================================================================
# GET API KEY - dynamic provider lookup
# =============================================================================
get_api_key() {
    local provider="$1"
    local var_name="${provider}_API_KEY"
    
    # Check env first
    [[ -n "${!var_name:-}" ]] && { echo "${!var_name}"; return 0; }
    
    # Check secrets file
    [[ -f "$SECRETS_FILE" ]] && grep -E "^${var_name}=" "$SECRETS_FILE" 2>/dev/null | head -1 | cut -d'=' -f2 | tr -d '"' | tr -d "'"
}

# =============================================================================
# LIST FREE MODELS - dynamic from OpenRouter API
# =============================================================================
list_free_models() {
    local key
    key=$(get_api_key "OPENROUTER")
    [[ -z "$key" ]] && { echo "No OPENROUTER key"; return 1; }
    
    curl -s "https://openrouter.ai/api/v1/models" \
        -H "Authorization: Bearer $key" 2>/dev/null | \
        python3 -c "
import json,sys
d = json.load(sys.stdin)
for m in d.get('data', []):
    if ':free' in m.get('id', ''):
        print(m['id'])
" 2>/dev/null
}

# =============================================================================
# ROUTE REQUEST - dynamic through llama-swap
# =============================================================================
route_request() {
    local model="${1:-free}"
    local strategy="${2:-free}"
    local base_url
    # Route via llama-swap:25100 AST matrix
    
    curl -s -X POST "${base_url}/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -H "X-Sovereign-Strategy: $strategy" \
        -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}"
}

# Auto-load on source
load_config
