---
name: sovereign-hatch-toolkit
description: Noise_XX_25519_AESGCM_SHA256 handshake toolkit and atomic POSIX filesystem message bus (FSBus) for Python agent infrastructure.
---

# Sovereign Hatch Toolkit

Two subsystems, both tested (41/41 green):

- **`hatch_core/noise_protocol.py`** — full `Noise_XX` handshake state machine
  (`write_msg1/read_msg1/write_msg2/read_msg2/write_msg3/read_msg3/split`),
  `CipherState`/`SymmetricState`, Ed25519 notary endorsement parsing,
  length-prefixed framing. Only dependency: `cryptography`.
- **`orchestrator/fsbus_engine.py`** — atomic POSIX message bus
  (`inbox/claimed/outbox/dead` + append-only `manifest.jsonl`): tmp+fsync+rename
  writes, `rename(2)` claims, lease reclamation, retry/dead-letter escalation,
  threaded workers. Zero dependencies (stdlib only).

- **`identity_router/mcp_server.py`** — zero-dependency stdio MCP server
  (JSON-RPC 2.0, MCP 2024-11-05): `current_identity`, `route_lesson`,
  `standing_files`, `hatch_gateway_status` tools.
- **`identity_router/identity_parser.py`** — parses `~/IDENTITY.md` into a
  structured identity dict (name, emoji, character, vibe, posture, platform).
- **`identity_router/router.py`** — `LessonRouter` scores a durable lesson
  against the six standing files (`OWNERSHIP_TABLE`) and recommends the
  target file; keyword phrases with weights, specific-file tie-break,
  `MEMORY.md` fallback.

`config/gateway_config.json` — gateway connection parameters.

Run `python3 -m unittest discover -s tests -p "test_*.py" -v` (or `make test`);
`python3 scripts/verify_all.py` runs the six subsystem suites end to end
(noise handshake, notary, FSBus, identity parser, lesson router, MCP
compliance). Subsystems never built are listed by the suite, not faked.
