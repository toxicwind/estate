# sovereign-hatch-toolkit

A Python toolkit with three production-grade subsystems for building and managing autonomous software engineering workflows.

## Hero

Orchestrate, monitor, and secure your autonomous agent fleet with the sovereign-hatch toolkit — a battle-tested foundation for modern AI systems.

## Features

- **Hatch Core** — `Noise_XX` handshake protocol (X25519 ephemeral/static DH, SHA-256 HKDF-style key derivation) with Ed25519 notary endorsement token parsing. Two handshake modes: `custom` (RE'd client variant) and `standard` (Noise XX per spec)
- **Gateway RPC** — `hatch_core/gateway_rpc.py`: Noise_XX WebSocket client for the Hatch gateway — protobuf `NoiseTransportFrame` chunking, `ServiceRequest`/`ServiceResponse` envelopes, proxy-aware connect, no-credentials transport diagnostic (`scripts/gateway_diagnose.py`)
- **Filesystem Bus** — Atomic POSIX filesystem message bus with immutable writes, race-free claims, and lease-expiry reclamation
- **Identity Router** — Parses `~/IDENTITY.md` into structured identity dicts, routes lessons against ownership tables, and exposes MCP-compatible endpoints

## Quick Start

```bash
# Install sovereign-hatch-toolkit
pip install sovereign-hatch-toolkit

# Initialize the toolkit
python sovereign_hatch_toolkit/init.py --config config/hatch.yaml

# Start the identity router
python sovereign_hatch_toolkit/identity_router.py --config config/identity.yaml

# Launch the filesystem bus
python sovereign_hatch_toolkit/fsbus_engine.py --config config/fsbus.yaml
```

## Architecture

Sovereign-Hatch is organized around three core pillars:

1. **Hatch Core** — Handles secure communication, key management, and identity verification
2. **Filesystem Bus** — Provides a durable, atomic message bus for inter-service communication
3. **Identity Router** — Manages agent identity, lesson routing, and MCP server exposure

Each subsystem is designed for loose coupling and independent scalability.

## Configuration

Key configuration areas:

- `hatch/` — Noise protocol parameters, key rotation schedule
- `fsbus/` — Bus configuration, manifest paths, and leader election
- `identity/` — Identity parser settings, ownership table paths
- `router/` — Lesson routing rules, MCP server endpoints

Example configuration:

```yaml
hatch:
  noise_protocol: "Noise_XX_25519_AESGCM_SHA256"
  key_rotation_days: 30

fsbus:
  scratch_dir: "/tmp/hatch-bus"
  manifest_path: "manifest.jsonl"

identity:
  home: "~/IDENTITY.md"
  ownership_table: "OWNERSHIP_TABLE.json"
```

## Optional Services

- **MCP Server** — Zero-dependency stdio MCP server exposing `current_identity`, `route_lesson`, `standing_files`, `hatch_gateway_status`
- **Gateway Connector** — `hatch_core/gateway_rpc.py` connects to the Hatch gateway via WSS + Noise_XX (`wss://hatch.metaaivm.com/v1/noise`); `scripts/gateway_diagnose.py` probes the path without credentials
- **Audit Logger** — Records all operations for compliance and debugging

## Development

```bash
# Run the test suite (57 tests)
python3 -m unittest discover -s tests -p "test_*.py"

# Run all subsystem suites end to end (7 suites)
python3 scripts/verify_all.py

# Probe the gateway transport path (no credentials)
python3 scripts/gateway_diagnose.py
```

## License

MIT License.

## Security

- End-to-end encryption for all inter-service communication
- Identity-based access control with role-based permissions
- Secure key management with no hardcoded secrets
- Regular security audits and penetration testing
