# agent-config

Machine-level tau agent configs. Live copies live outside the repo:

- `mcp.json` -> `/home/toxic/.tau/agent/mcp.json` (user scope: every tau session on awrawr-pc)

## mcp.json

Single entry `mesh-gateway` pointing tau at the mesh MCP gateway
(`shep`/`mcpproxy`, pitchfork daemon, `http://127.0.0.1:25127/mcp`,
streamable HTTP, retrieve_tools mode). One hop exposes all 31 upstream
servers (context7, exa, arxiv, ast-grep, codebase-memory, redis, ...).

Verified 2026-09-19: raw MCP initialize + tools/list handshake OK;
context7:resolve-library-id live call OK.

To deploy on a fresh box: `cp agent-config/mcp.json ~/.tau/agent/mcp.json`
(requires the mesh gateway running on 127.0.0.1:25127).
