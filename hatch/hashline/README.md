# hashline/

![sovereign](https://img.shields.io/badge/sovereign--projects-2E86DE?style=for-the-badge)
![hashline](https://img.shields.io/badge/hashline-0.9.19-7B2FF7?style=for-the-badge)
![rust](https://img.shields.io/badge/rust-DEA584?style=for-the-badge)

**hashline's project home on the estate.** [hashline](https://github.com/quangdang46/hashline) is the first-class file-edit tool for all agents and subagents: hash-anchored line editing (xxh32 anchors like `42:a3`) with stale-read rejection, exposed as both a binary CLI and a 6-tool MCP server. This folder holds the project's runbooks, discovery notes, and wiring docs — the skill itself lives at `~/workspace/skills/hashline/SKILL.md` on the cell.

## What's here

| Path | What it is |
| ---- | ---------- |
| [`docs/discovery.md`](docs/discovery.md) | Investigation notes (2026-09-30): what hashline is, repo, version, verified surfaces, the no-grep finding |
| [`docs/runbook.md`](docs/runbook.md) | Operational runbook: install/update, MCP wiring, verification commands, troubleshooting |
| [`docs/wiring.md`](docs/wiring.md) | First-class wiring: fleet-KB section, spawn-brief line, skill registration |

## Quick Start

```bash
# on yote — read with anchors, patch by anchor
hashline read <file>
hashline patch <file> '[/path#HASH]
SWAP 2:89:
+new content'

# MCP server (newline-delimited JSON-RPC over stdio — NOT Content-Length framing)
hashline mcp
```

Binary: `/home/toxic/.local/bin/hashline` · Config/log: `/home/toxic/.hashline/` · Upstream: https://github.com/quangdang46/hashline (third-party, MIT — not ours)
