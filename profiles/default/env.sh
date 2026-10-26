#!/usr/bin/env bash
# ==============================================================================
# Estate Profile: default (Modular / GitHub CI / Contributor Template)
# ==============================================================================
export ESTATE_PROFILE="default"

# Core Ports
export HERD_PORT="${HERD_PORT:-25100}"
export HERD_PORT="${HERD_PORT:-25100}"
export RUST_WEB_PORT="${RUST_WEB_PORT:-25201}"
export MODEL_GUARD_PORT="${MODEL_GUARD_PORT:-25101}"
export OPENFANG_PORT="${OPENFANG_PORT:-25103}"
export HF_DOWNLOADER_PORT="${HF_DOWNLOADER_PORT:-25106}"
export WATCHDOG_PORT="${WATCHDOG_PORT:-25108}"
export MCPPROXY_GO_PORT="${MCPPROXY_GO_PORT:-25127}"
export GHAS_API_PORT="${GHAS_API_PORT:-25112}"
export GHAS_MCP_PORT="${GHAS_MCP_PORT:-25113}"
export GHAS_FRONTEND_PORT="${GHAS_FRONTEND_PORT:-25114}"
export MESH_HUB_PORT="${MESH_HUB_PORT:-25115}"
export HINDSIGHT_API_PORT="${HINDSIGHT_API_PORT:-25117}"
export HINDSIGHT_CP_PORT="${HINDSIGHT_CP_PORT:-25118}"
# MCP_GATEWAY_PORT is a compatibility alias for thresher :25127, the same
# daemon MCPPROXY_GO_PORT names. :25120 belongs to ESTATE_CHAT_PORT; it was
# never this gateway. See config/ports.env.
export MCP_GATEWAY_PORT="${MCP_GATEWAY_PORT:-25127}"
export QDRANT_PORT="${QDRANT_PORT:-25133}"
export REDIS_PORT="${REDIS_PORT:-25203}"

# Inference Defaults (Configurable via environment)
# PI_SUBAGENT_MODEL was here and is gone: 0 source files in the tau monorepo
# read it, so it never selected a subagent model. Subagent routing comes from
# the `subagents:` / `modelRoles:` keys in the agent config
# (config/tau/agent/config.yml), not from the environment.
export SCOUT_MODEL="${SCOUT_MODEL:-local-fast}"
export SCOUT_BASE_URL="${SCOUT_BASE_URL:-http://127.0.0.1:25100/v1}"
export SCOUT_API_KEY="${SCOUT_API_KEY:-herd}"

# Build Concurrency Defaults
export CARGO_BUILD_JOBS="${CARGO_BUILD_JOBS:-$(nproc 2>/dev/null || echo 4)}"

export ESTATE_ROOT="${ESTATE_ROOT:-$HOME/estate}"
export ESTATE_VERSION="mesh-1.0.0"
