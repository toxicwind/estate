---
name: fix-thresher-mcp-auth
description: Fix MCP thresher authentication by setting require_mcp_auth to false in config file
---

# Fix Thresher MCP Auth

When thresher MCP proxy returns `Authentication required` (HTTP 401) on port 25127:

1. Check `/home/toxic/estate/ranch/barn/thresher/mcp_config.json`
2. Change `"require_mcp_auth": true` to `"require_mcp_auth": false`
3. Restart thresher service

The config file setting overrides the `--require-mcp-auth false` command-line flag.

After fix, mesh-gateway connections proceed without API key or agent token.

## Note
Port 20128 hosts a Next.js dev server, not an MCP server. Separate infrastructure concern.
