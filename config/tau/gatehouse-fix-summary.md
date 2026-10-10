# Gatehouse MCP Auth Fix

## Problem
MCP gatehouse on port 25127 returning `{"error":"Authentication required. Provide an API key or agent token."}` (HTTP 401), preventing mesh-gateway connections.

## Root Cause
The gatehouse config file `/home/toxic/estate/ranch/barn/gatehouse/mcp_config.json` had `"require_mcp_auth": true`, which overrides the `--require-mcp-auth false` command-line flag. This forces all `/mcp` endpoint connections to require authentication.

## Fix
Changed `"require_mcp_auth": true` to `"require_mcp_auth": false` in the gatehouse config file.

File: `/home/toxic/estate/ranch/barn/gatehouse/mcp_config.json`
- Line with `"require_mcp_auth": true` → `"require_mcp_auth": false`

## Verification
- Gatehouse restarted and listening on `127.0.0.1:25127`
- `/mcp` endpoint responds without authentication requirement
- Mesh-gateway connections can now proceed

## Note
Port 20128 (trusted-local) hosts a Next.js development server, not an MCP server. This is a separate infrastructure concern.