# sovereign-hatch-toolkit

A Python toolkit with three production-grade subsystems:

1. **`hatch_core/noise_protocol.py`** — a complete `Noise_XX` handshake
   implementation (X25519 ephemeral/static DH, SHA-256 HKDF-style key
   derivation), plus an Ed25519 notary endorsement token parser and 2-byte
   length-prefixed frame pack/unpack helpers. Live-gateway suite is
   `Noise_XX_25519_AESGCM_SHA256` (AES-256-GCM transport, big-endian
   nonces: 12-byte nonce = 4 zero bytes + 64-bit big-endian counter).
2. **`orchestrator/fsbus_engine.py`** — an atomic POSIX filesystem message bus:
   immutable writes (tmp + fsync + atomic rename + dir fsync), append-only
   `manifest.jsonl` ledger, race-free claims via `rename(2)`, lease-expiry
   reclamation, retry counting, and dead-letter poison-pill queues.
3. **`identity_router/`** — `identity_parser.py` parses `~/IDENTITY.md` into a
   structured identity dict; `router.py` (`LessonRouter`) scores a durable
   lesson against the six standing files (`OWNERSHIP_TABLE`) and recommends
   the target file; `mcp_server.py` is a zero-dependency stdio MCP server
   (JSON-RPC 2.0, MCP 2024-11-05) exposing `current_identity`,
   `route_lesson`, `standing_files`, `hatch_gateway_status`.

`config/gateway_config.json` holds the gateway connection parameters the Noise
transport is configured against (`wss://hatch.metaaivm.com/v1/noise`,
`Noise_XX_25519_AESGCM_SHA256`). It carries no auth material — no tokens live
in this tree.

## Install

```bash
pip install -r requirements.txt   # cryptography>=41.0.0 (only dependency)
```

## Usage

```python
from hatch_core.noise_protocol import NoiseHandshakeState
from orchestrator.fsbus_engine import FSBusEngine
from pathlib import Path

# Noise_XX handshake (initiator <-> responder)
init = NoiseHandshakeState(is_initiator=True)
resp = NoiseHandshakeState(is_initiator=False)
m1 = init.write_msg1(b"hello")
assert resp.read_msg1(m1) == b"hello"
m2 = resp.write_msg2(b"challenge")
assert init.read_msg2(m2) == b"challenge"
m3, (c_send, c_recv) = init.write_msg3(b"done")
payload, (s_send, s_recv) = resp.read_msg3(m3)
# encrypted transport in both directions
ct = c_send.encrypt_with_ad(b"ad", b"secret")
assert s_recv.decrypt_with_ad(b"ad", ct) == b"secret"

# Filesystem message bus (durable scratch, never /tmp — tmpfs janitor)
import os
_scratch = os.environ.get("TMPDIR") or os.path.join(os.path.expanduser("~"), ".cache")
bus = FSBusEngine(Path(_scratch) / "mybus")
tid = bus.submit({"cmd": "render", "scene": 12})
cid, task = bus.claim("worker-1")          # atomic: exactly one worker wins
bus.finish(cid, "worker-1", ok=True, result={"frames": 240})
```

## Test

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
# or: make test
# or: python3 scripts/verify_all.py   (six end-to-end suites)
```

41 tests: Noise_XX handshake vectors, notary token parsing, AES-GCM transport
round-trips, framing, FSBus submit/claim/finish lifecycle, claim-race
single-winner, retry → dead-letter escalation, lease reclamation, worker
threads, identity parsing, lesson routing, MCP compliance.

## Status

**2026-10-01:** `identity_router/` built and tested (parser, router, MCP
server + compliance suite); `scripts/verify_all.py` rewritten as the master
suite covering all six subsystem suites; cipher suite corrected to
`Noise_XX_25519_AESGCM_SHA256` for the live gateway. 41/41 tests pass.

**2026-09-30 audit:** the original drop contained references to subsystems
that were never present in the tree (`gateway_rpc`, `session_vault`,
`telemetry_qpl`, `procedural_dag`, `direct_socket_runner`, `research_meta`,
and a corrupted `verify_all.py` that could not compile). Those dead
references were removed. The five named subsystems remain deliberately
unbuilt — `scripts/verify_all.py` lists them in `NOT_BUILT` (documented,
not faked); refusal/evasion modeling is out of scope by doctrine.

## License

MIT
