#!/usr/bin/env bash
# ==============================================================================
# Sovereign Profile: toxic (Workstation SSOT)
# AMD Ryzen 7 8700F (8C/16T, Zen 4) + NVIDIA RTX 3090 (24GB VRAM)
export SOVEREIGN_PROFILE="toxic"
# ==============================================================================

# 1. Inference & Subagent Models
export PI_SUBAGENT_MODEL="thinkingmachines/inkling"
export SCOUT_MODEL="local-fast"
export SCOUT_BASE_URL="http://127.0.0.1:25100/v1"
export SCOUT_API_KEY="llama-swap"
export NIM_QUEUE_BASE_URL="https://integrate.api.nvidia.com/v1"
export LLAMA_SWAP_MODEL="beellama/qwen-flash-64k"

# 2. Local Mesh & Gateway Ports (Aligned with sovereign/config/ports.env)
export LLAMA_SWAP_PORT="25100"
export HERD_PORT="25100"
export RUST_WEB_PORT="25101"
export OPENFANG_PORT="25103"
export HF_DOWNLOADER_PORT="25106"
export WATCHDOG_PORT="25108"
export MCPPROXY_PORT="25109"
export GHAS_API_PORT="25112"
export GHAS_MCP_PORT="25113"
export GHAS_FRONTEND_PORT="25114"
export MESH_HUB_PORT="25115"
export HINDSIGHT_API_PORT="25117"
export HINDSIGHT_CP_PORT="25118"
export MCP_GATEWAY_PORT="25120"
export BYTE_VISION_PORT="25121"
export BEELLAMA_PORT="25122"
export IK_LLAMA_PORT="25123"
export KIMI_CODE_PORT="25126"
export MCPPROXY_GO_PORT="25127"
export ZEDRA_HOST_PORT="25130"
export SOV_GHAS_PORT="25131"
export QDRANT_PORT="25133"
export REDIS_PORT="25199"

# 3. Build & Compiler Concurrency Throttling (Prevents L3 cache thrashing)
export CARGO_BUILD_JOBS="12"
export RUSTFLAGS="-C target-cpu=znver4 -C codegen-units=16"

# 4. Engine & Developer Paths
export SOVEREIGN_ROOT="${SOVEREIGN_ROOT:-$HOME/sovereign}"
export SOVEREIGN_VERSION="mesh-1.0.0"
export PATH="${HOME}/.local/bin:${SOVEREIGN_ROOT}/bin:${PATH}"
