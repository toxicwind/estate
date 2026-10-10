---
name: fix-gatehouse-mcp-auth
description: Fix MCP gatehouse authentication by setting require_mcp_auth to false in config file
---

# Fix Gatehouse MCP Auth

When gatehouse MCP proxy returns `Authentication required` (HTTP 401) on port 25127:

1. Check `/home/toxic/estate/ranch/barn/gatehouse/mcp_config.json`
2. Change `"require_mcp_auth": true` to `"require_mcp_auth": false`
3. Restart gatehouse service

The config file setting overrides the `--require-mcp-auth false` command-line flag.

After fix, mesh-gateway connections proceed without API key or agent token.

## Note
Port 20128 hosts a Next.js dev server, not an MCP server. Separate infrastructure concern.
