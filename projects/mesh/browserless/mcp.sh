#!/bin/bash
# browserless-mcp stdio launcher (sovereign mesh, first-class keeper wiring).
#
# Spawns the repo MCP server (dist/index.js) on stdio. No port, no daemon:
# MCP clients launch this per session. The persistent_* tools attach to the
# browser-keeper Chromium via CDP at 127.0.0.1:9223 (override with
# BROWSER_KEEPER_CDP); no initialize_browserless needed for them.
#
# Build (node >= 18): npm install && npm run build
# Registered in the mesh MCP registry as: browserless-mcp
set -euo pipefail
exec node /home/toxic/sovereign/projects/mesh/browserless/dist/index.js "$@"
