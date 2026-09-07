#!/usr/bin/env bash
# ==============================================================================
# Sovereign Profile: default (Modular / GitHub CI / Contributor Template)
# ==============================================================================
export SOVEREIGN_PROFILE="default"

# Core Ports
export LLAMA_SWAP_PORT="${LLAMA_SWAP_PORT:-25100}"
export HERD_PORT="${HERD_PORT:-25100}"
export RUST_WEB_PORT="${RUST_WEB_PORT:-25101}"
export OPENFANG_PORT="${OPENFANG_PORT:-25103}"
export HF_DOWNLOADER_PORT="${HF_DOWNLOADER_PORT:-25106}"
export WATCHDOG_PORT="${WATCHDOG_PORT:-25108}"
export MCPPROXY_PORT="${MCPPROXY_PORT:-25109}"
export GHAS_API_PORT="${GHAS_API_PORT:-25112}"
export GHAS_MCP_PORT="${GHAS_MCP_PORT:-25113}"
export GHAS_FRONTEND_PORT="${GHAS_FRONTEND_PORT:-25114}"
export MESH_HUB_PORT="${MESH_HUB_PORT:-25115}"
export HINDSIGHT_API_PORT="${HINDSIGHT_API_PORT:-25117}"
export HINDSIGHT_CP_PORT="${HINDSIGHT_CP_PORT:-25118}"
export MCP_GATEWAY_PORT="${MCP_GATEWAY_PORT:-25120}"
export MCPPROXY_GO_PORT="${MCPPROXY_GO_PORT:-25127}"
export QDRANT_PORT="${QDRANT_PORT:-25133}"
export REDIS_PORT="${REDIS_PORT:-25199}"

# Inference Defaults (Configurable via environment)
export PI_SUBAGENT_MODEL="${PI_SUBAGENT_MODEL:-thinkingmachines/inkling}"
export SCOUT_MODEL="${SCOUT_MODEL:-local-fast}"
export SCOUT_BASE_URL="${SCOUT_BASE_URL:-http://127.0.0.1:25100/v1}"
export SCOUT_API_KEY="${SCOUT_API_KEY:-llama-swap}"

# Build Concurrency Defaults
export CARGO_BUILD_JOBS="${CARGO_BUILD_JOBS:-$(nproc 2>/dev/null || echo 4)}"

export SOVEREIGN_ROOT="${SOVEREIGN_ROOT:-$HOME/sovereign}"
export SOVEREIGN_VERSION="mesh-1.0.0"
