---
name: sovereign-hatch-toolkit
description: >
  Noise XX handshake and atomic POSIX message bus. noise_protocol.py implements the full Noise_XX state machine with Ed25519 notary endorsements; fsbus_engine.py is a crash-safe tmp+fsync+rename bus with leases, retries and dead-letter escalation. Triggers on: "noise xx", "handshake", "fsbus", "message bus", "notary".
---

# Sovereign Hatch Toolkit

Seven subsystems, all tested (57/57 green):

- **`hatch_core/noise_protocol.py`** — full `Noise_XX` handshake state machine
  (`write_msg1/read_msg1/write_msg2/read_msg2/write_msg3/read_msg3/split`),
  `CipherState`/`SymmetricState`, Ed25519 notary endorsement parsing,
  length-prefixed framing. Two modes: `custom` (RE'd client variant, default)
  and `standard` (Noise XX per the framework spec); the nonce style follows
  the mode. Only dependency: `cryptography`.
- **`hatch_core/gateway_rpc.py`** — Noise_XX gateway RPC client: protobuf
  `NoiseTransportFrame` chunking, `ServiceRequest`/`ServiceResponse`
  envelopes (services daemon 0 / sentinel 1 / vault 2 / authd 3), serialized
  reads, proxy-aware WebSocket connect, no-credentials transport diagnostic.
  Depends on `websocket-client` + `cryptography`.
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
`python3 scripts/verify_all.py` runs the seven subsystem suites end to end
(noise handshake, notary, FSBus, identity parser, lesson router, MCP
compliance, gateway RPC). Subsystems never built are listed by the suite,
not faked. `python3 scripts/gateway_diagnose.py` probes the gateway path
without credentials (expected: transport OK, auth gate rejects).
