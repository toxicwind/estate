![GitHub Repo Stars](https://img.shields.io/github/stars/toxicwind/github-mcp?style=for-the-badge)
![GitHub License](https://img.shields.io/github/license/toxicwind/github-mcp?style=for-the-badge)
![GitHub Last Commit](https://img.shields.io/github/last-commit/toxicwind/github-mcp?style=for-the-badge)

# github-mcp
Use Github Mcp when the user asks for Github Mcp or this provider's API

## What it does
Client for GitHub's official remote MCP server (https://api.githubcopilot.com/mcp) that provides access to GitHub's Model Context Protocol tools with OAuth credential handling, transport hardening, and resource safety features.

## Why it matters
Enables standardized, secure access to GitHub's growing ecosystem of MCP tools (for code review, issue management, etc.) with proper credential handling and production-grade client reliability.

## Who it's for
Developers and AI agents who need to interact with GitHub's MCP server for extended functionality beyond standard REST APIs, particularly for OAuth-authenticated workflows and real-time collaboration tools.

## Features
- **OAuth Authentication** - Uses user-connected `custom.github-mcp` OAuth credential (never handles raw tokens)
- **Standard CLI Interface** - `github-mcp-cli <subcommand> [options]` with status, list-tools, and call-tool subcommands
- **Transport Hardening** - 
  - Unique request IDs with SSE response ID matching
  - Local read deadline (default 150s, override via GITHUB_MCP_READ_TIMEOUT)
  - Failed lane marking with 60s TTL cache (~/.cache/github-mcp-https-down)
- **Resource Safety** - 
  - Short-lived process per invocation (no threads, no daemon, no retries)
  - CPU: no busy loops; every wait is blocking socket read with timeout
  - Memory: SSE events capped at 8 MiB, response bodies at 32 MiB (_ResponseTooLarge abort)
  - Threads: Single lock for session handshake; subprocess is single-threaded
- **Secure Auth Handling** - Auth handled via authd surrogates by bin/dynamic_credentials.py; CLI never sees raw token
- **Mutation Safety** - 
  - Auto-posts to Chris only for destructive/irreversible mutations (repo delete, ownership transfer, force-push to main, private→public publish)
  - Task-authorized mutations proceed autonomously (create, push, edit issues/PRs/branches/comments/releases)
  - Never re-asks for intent; acts within given task scope and reports done
- **Skill Complement** - Complements `github` skill (PAT-based REST API); prefer github-mcp for MCP/OAuth, github for raw REST endpoints

## Quick Start
```bash
# Check MCP server status
github-mcp-cli status

# List available tools
github-mcp-cli list-tools

# Call a specific tool (requires JSON object arguments)
github-mcp-cli call-tool --name <tool> --arguments-json '<json-object>'

# Typical workflow:
# 1. Check status
# 2. List tools to discover capabilities
# 3. Call tool with proper JSON arguments
```

## Configuration
- **CLI Location**: `github-mcp-cli` (exec wrapper)
- **Auth Handling**: 
  - Credential stored as `custom.github-mcp` (OAuth)
  - Auth via `bin/dynamic_credentials.py` surrogates
  - Never handles raw tokens in chat, env vars, flags, or auth files
- **Transport Settings**:
  - `GITHUB_MCP_READ_TIMEOUT` - Local read deadline override (default 150s)
  - Failed lane cache: `~/.cache/github-mcp-https-down` (60s TTL)
- **Authentication Rules**:
  - 401/403 = question about request before credential
  - Verify credential attached: request without helpers = wrong/under-scoped token
  - Only reject after credential-attached request → reconnect via credentials.request_api_access
- **Operating Constraints**:
  - Restrict authenticated requests to: api.githubcopilot.com
  - Do not print, log, or persist raw credentials
  - Follow Auth section rather than asking for key on auth failure

## Development
Modify the exec wrapper and underlying client logic:
- Transport hardening: Unique IDs, SSE ID matching, read timeout handling
- Resource safety: Process lifecycle, CPU/memory/thread constraints
- Auth handling: Integration with bin/dynamic_credentials.py surrogates
- CLI interface: subcommand parsing and argument validation
- Error handling: Proper error reporting without exposing internal state

## License
Internal tool - refer to sovereign estate licensing

## Security
- **Credential Protection** - Never handles raw OAuth tokens; uses surrogate authentication
- **Transport Security** - Unique request IDs prevent replay attacks; read timeouts prevent hanging
- **Resource Exhaustion Prevention** - Memory caps, no busy loops, single-threaded subprocess
- **Fail-Fast Lanes** - Failed connections marked with TTL cache to prevent repeated attempts
- **Mutation Restrictions** - Destructive/irreversible mutations require Chris approval; others proceed autonomously within task scope
- **Audit Trail** - Reports done for all mutations; only escalates irreversible ones to Chris