![GitHub Repo Stars](https://img.shields.io/github/stars/toxicwind/hashline?style=for-the-badge)
![GitHub License](https://img.shields.io/github/license/toxicwind/hashline?style=for-the-badge)
![GitHub Last Commit](https://img.shields.io/github/last-commit/toxicwind/hashline?style=for-the-badge)

# hashline
Hash-anchored file editing for agents — the first-class edit tool

## What it does
Binary CLI tool (11 subcommands) + 6-tool MCP server + daemon mode that provides hash-anchored file editing using xxh32 line anchors. Replaces fragile str_replace/sed-style editing with content-hashed anchors that survive nearby edits and fail fast on stale reads.

## Why it matters
Prevents silent corruption in agent-mediated file edits by using content-hashed line anchors (42:a3 format) that detect when files have changed between read and patch operations, forcing a re-read instead of applying stale patches.

## Who it's for
AI agents and developers who perform programmatic file edits and need guaranteed correctness — any edit where a wrong change is worse than no change.

## Features
- **Hash-Anchored Editing** - Uses xxh32 hashes (42:a3) to create stable line references that survive nearby edits
- **Stale Read Detection** - Hard-rejects patches based on stale reads (exit 1, ERR STALE) instead of corrupting files
- **Atomic Operations** - All patches are applied atomically with verifiable before/after states
- **Multi-Mode Interface** - Binary CLI (11 subcommands), 6-tool MCP server (newline-delimited JSON-RPC), and daemon mode
- **Rich Patch Operations** - SWAP, DEL, INS.*, BLK.*, CUT/PUT operations with syntactic block awareness
- **Language-Aware Blocks** - Automatic detection of brace-balanced ({}), indentation-based (.py/.verse), and Ruby (def/class/end) blocks
- **MCP Server** - stdio MCP server with 6 tools (read, patch, write, find_block, remove_file, rename_file)
- **Daemon Support** - HTTP and Unix socket modes with detach/pid-file supervision

## Quick Start
```bash
# Read file to get anchors
hashline read src/auth.js
# Returns: src/auth.js#1A2B with anchored lines like: 1:ee|function verifyToken(token) {

# Patch by anchor (preferred method for multi-op)
hashline patch src/auth.js - <<'EOF'
SWAP 2:c6:
  const decoded = jwt.verify(token, env.SECRET)
EOF
# Returns: OK src/auth.js#7f2a edits=1 changed=1

# Daemon mode for repeated operations
hashline serve --http 17300 &
HASHLINE_URL=http://127.0.0.1:17300 hashline read src/file
```

## Configuration
- **Binary Location**: `/home/toxic/.local/bin/hashline` (v0.9.19)
- **Config/Log**: `/home/toxic/.hashline/` (hashline.log, update-check.json)
- **Environment Variables**:
  - `HASHLINE_NO_UPDATE_CHECK=1` - Silence daily update notice
  - `HASHLINE_RETURN_ANCHORS=1` - Always emit fresh anchors after patch
  - `HASHLINE_URL` / `HASHLINE_SOCKET` - Point CLI at running daemon
  - `HASHLINE_BIN` - Binary path override

## Development
Based on third-party hashline (v0.9.19) from https://github.com/quangdang46/hashline (MIT license, Rust). Estate-specific agent hygiene practices documented in SKILL.md.

## License
MIT (third-party tool)

## Security
- UTF-8 text only (dos2unix first for CRLF)
- No regex/search surface by design - use grep/rg/ffs for search, then anchor edit with hashline
- Fail-fast on stale reads prevents silent corruption
- Agent hygiene: Use `*** Begin Patch` heredoc form for yote-conn bridge to avoid quote nesting issues