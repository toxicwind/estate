# Socket Stream & Cognitive EKG Architecture

## Overview

This document describes the Socket Stream transport layer and the Cognitive EKG monitoring system for the Sovereign operating environment. Both are components of the Inference and Router Fleet Audit phase, ensuring reliable long-running reasoning streams and system health observability.

## Socket Stream Transport

### Problem

Long-running reasoning SSE streams are dropped by middleboxes (NAT, load balancers, firewalls) that enforce idle-timeout policies. The OS-level TCP keepalive defaults (typically 2 hours) are too slow to prevent these drops during active reasoning generation that produces no data for extended periods.

### Solution

A two-tier transport architecture:

1. **Socket Stream Config** (`sovereign/packages/sovereign-utils/src/transport/socket-stream.ts`)
   - `SocketStreamConfig` interface with OS-level keepalive parameters
   - `RingTokenBuffer` — append-only ring buffer preserving validated reasoning tokens across mid-flight network interrupts
   - `DirectSocketStreamClient` — connects to the Stream Broker UNIX socket or TCP port with robust keepalive

2. **Stream Broker Daemon** (`sovereign/projects/range/ranch/stockyard/stream-broker/`)
   - UNIX socket server (`/run/user/1000/sovereign-stream-broker.sock`)
   - TCP server (port 25215)
   - Echo service with OS-level keepalive (TCP_KEEPIDLE=30s)
   - Supervised by Pitchfork with auto-restart

### Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `socketPath` | `/run/user/1000/sovereign-stream-broker.sock` | UNIX socket path |
| `tcpPort` | `25215` | TCP listen port |
| `tcpHost` | `127.0.0.1` | TCP bind address |
| `tcpKeepAlive` | `true` | Enable OS-level keepalive |
| `tcpKeepAliveInitialDelayMs` | `30000` | TCP_KEEPIDLE (30s) |
| `tcpNoDelay` | `true` | Disable Nagle's algorithm |
| `maxRingBufferTokens` | `32768` | Ring buffer capacity |

### Integration

- The Stream Broker is registered in `pitchfork.toml` as `[daemons.sovereign-stream-broker]`
- The `socket-stream.ts` module is exported from `sovereign/packages/sovereign-utils/src/index.ts`
- The Stream Broker listens on port 25215 (per `config/ports.env`)

## Cognitive EKG (Electrocardiogram Monitoring)

### Problem

The Sovereign fleet requires continuous health monitoring of all inference daemons to detect degraded performance, connection resets, and upstream failures before they cascade into user-facing 503 errors.

### Solution

The model-guard proxy (`herd-model-guard.py`) serves as the primary health enforcement layer:

1. **Connection Reset Handling** — The `_proxy` method wraps the entire request/response lifecycle in `try/except (BrokenPipeError, ConnectionResetError)` to prevent server thread crashes when clients disconnect mid-stream.

2. **Fail-Open Upstream** — If the constraints file is unreadable or the upstream (herd) resets, traffic passes through untouched with the error logged.

3. **Audit Trail** — Every rewrite appends a JSON line to `/home/toxic/sovereign/data/model-guard-audit.jsonl`, rotated at 10MB.

### Health Endpoints

| Daemon | Port | Health Check |
|--------|------|-------------|
| herd | 25100 | `GET /health` → 200 |
| model-guard | 25101 | `GET /health` → 200 |
| sovereign-router | 25104 | `GET /health` → 200 |
| squawk-feed | 25135 | `GET /seq` → 200 |
| stream-broker | 25215 | `ss -ltn 'sport = :25215'` |

### Port SSOT

All port assignments are defined in `config/ports.env`. The `bin/port-audit` tool diffs the live `ss -tlnp` listener table against `config/ports.env` to detect bind conflicts and unregistered listeners.

## Pitchfork Supervision

### Daemon Lifecycle

All daemons are supervised by Pitchfork (systemd user unit). The supervisor reads `pitchfork.toml` and manages daemon lifecycle:

- **auto = ["start"]** — Daemon starts automatically on supervisor boot
- **retry = true** — Daemon restarts on failure
- **ready_http** / **ready_cmd** — Health check before marking daemon ready

### Config Loading

The `pitchfork.toml` at `/home/toxic/sovereign/pitchfork.toml` is the single source of truth for all daemon definitions. Pitchfork does NOT hot-reload — editing any `[daemons.*]` section requires `pitchfork restart sovereign/<name>`.

The symlink `/home/toxic/pitchfork.toml → /home/toxic/sovereign/pitchfork.toml` ensures the supervisor (running from `/home/toxic`) can find the config.

### Version Management

Pitchfork is pinned to version 2.25 in `~/.config/mise/config.toml` (`pitchfork = "2.25"`). The `latest` symlink in `/home/toxic/.local/share/mise/installs/pitchfork/` points to 2.25.0.

## Recent Fixes (2026-09-23)

1. **503 Error Resolution** — The pitchfork supervisor was running from `/home/toxic` instead of `/home/toxic/sovereign`, causing it to not find `pitchfork.toml`. Fixed by creating the symlink `/home/toxic/pitchfork.toml → /home/toxic/sovereign/pitchfork.toml`.

2. **Model-Guard Connection Reset** — Added `try/except (BrokenPipeError, ConnectionResetError)` around the entire `_proxy` method body in `herd-model-guard.py` to prevent server thread crashes.

3. **Squawk-Feed Path Fix** — Updated `run-feed.sh` to point to the correct `squawk_feed.py` path in the ranch directory.

4. **Pitchfork Version Pinning** — Changed `pitchfork = "latest"` to `pitchfork = "2.25"` in mise config to avoid version ambiguity.

## References

- `config/ports.env` — Port SSOT
- `pitchfork.toml` — Daemon definitions
- `config/model_constraints.yaml` — Model constraint definitions
- `docs/ARCHITECTURE.md` — Full architecture documentation
