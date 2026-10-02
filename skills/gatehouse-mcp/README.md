# gatehouse-mcp

**Add a new MCP server to Gatehouse as a first-class citizen** – search the estate for an existing implementation (bridge first, then GitHub, then web), adopt it directly or fork it under toxicwind preserving ancestry, register it in Gatehouse's live config and durable .dist template, restart Gatehouse through its owned pitchfork path, and verify tool discovery, end-to-end calls, and secret hygiene.

## What It Does

This skill implements the repeatable workflow for turning any capability into a first-class Gatehouse MCP server. It follows a proven pattern demonstrated with the `rsync` lane (2026-09-30), ensuring that new MCP servers integrate properly with Gatehouse's infrastructure while maintaining security and reliability standards.

## Why It Matters

Gatehouse acts as a central hub for MCP (Model Context Protocol) tools. Adding new servers requires careful handling to avoid breaking existing integrations, leaking secrets, or introducing performance issues. This skill provides a systematic approach that:

- **Ensures compatibility** with Gatehouse's mark3labs/mcp-go v0.57.0 transport standard (newline-delimited JSON with proper framing).
- **Enforces security** by requiring ancestor preservation, no-force-pushes, and secret-free code.
- **Validates functionality** through comprehensive testing before registration.
- **Maintains operability** by guiding users through restart procedures and rollback strategies.

## Features

- **Discovery-first approach**: Searches yote, GitHub, and web for existing implementations before building from scratch.
- **Ancestry-preserving forks**: Creates toxicwind forks that inherit upstream history, avoiding unnecessary rewrites.
- **Rigorous testing**: Compilation, protocol smoke tests (framed and lines modes), and end-to-end calls before registration.
- **Secure registration**: Canonical source from `/home/toxic/estate/projects/range/ranch/barn/gatehouse`, live config in `mcp_config.json`, and durable template in `mcp_config.json.dist`.
- **Operational readiness**: Clear restart procedure via Gatehouse's pitchfork, health-check monitoring, and secret hygiene enforcement.

## Quick Start

```bash
# 1. Search for an existing MCP implementation
#    (bridge first, then GitHub, then web)
find /home/toxic -type d -name "*rsync*" -o -name "*sync*" -o -name "*file*" | head -20

# 2. Adopt or fork the implementation
#    - If a suitable implementation exists, adopt it directly
#    - Otherwise, fork under toxicwind (preserve ancestry)

# 3. Build to the house transport standard
#    Ensure the server compiles and passes protocol smoke tests

# 4. Register in Gatehouse
#    - Write entry to both live config (mcp_config.json) and .dist template (mcp_config.json.dist)
#    - Validate JSON after each edit
#    - Commit + push to toxicwind/<name> main

# 5. Restart Gatehouse
cd /home/toxic/estate && ./bin/pitchfork-restart sovereign/gatehouse

# 6. Verify
#    - Check server logs for health status
#    - Confirm tool discovery responds to MCP queries
#    - Run bounded real read through the new route
```

## Configuration

- **`mcp_config.json`** (live config): Registered MCP server entry with fields `name`, `command`, `args`, `env`, `protocol: "stdio"`, `enabled: true`, `health_check_interval: "15s"`, `tool_discovery_interval: "2m0s"`, `isolation: {enabled:false,mode:"none"}`, `quarantined: false`.
- **`mcp_config.json.dist`** (durable template): Bootstrap source copied when live config is missing; includes the same field structure.
- **Source**: Canonical implementation at `/home/toxic/estate/projects/range/ranch/barn/gatehouse`.

## Procedure Overview

1. **Search** – Use `yote` with `ffs grep` keywords, GitHub search, and web search to locate an existing MCP implementation.
2. **Adopt/Fork** – Adopt directly if the implementation meets quality bar; otherwise fork under `toxicwind/*` with full upstream ancestry.
3. **Build & Test** – Compile with `bun build src/server.ts --outfile /dev/null`; run protocol smoke tests in both framed and lines modes; commit and push.
4. **Register** – Write entries to both live config and .dist template; validate JSON; commit + push.
5. **Restart** – Use `pitchfork-restart sovereign/gatehouse` to bring the new server online.
6. **Verify** – Check logs, tool discovery, end-to-end calls, and ensure secret hygiene.

## Prevention

- Always use word-boundary-safe patterns when modifying file paths in MCP server code.
- Preserve full upstream ancestry when forking; never squash history.
- Never open PRs against original upstreams; always commit and push to the fork's `main`.
- Sandbox all paths touched by the server; require explicit confirmation for destructive operations.
- Keep secret values out of code, configs, logs, commits, and reports.

## Security & Licensing

- **Security**: The skill enforces no secrets in code/configs/logs/commits/reports, uses sandboxed paths, and requires confirmation for destructive operations.
- **License**: The canonical source (`/home/toxic/estate/projects/range/ranch/barn/gatehouse`) carries its own licensing terms; the skill does not impose additional restrictions.

## References

- Gatehouse MCP Integration workflow (this skill)
- Mark3labs/mcp-go v0.57.0 transport specification
- ToxicWind fork policy and best practices
