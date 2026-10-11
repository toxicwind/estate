#!/usr/bin/env python3
"""
Master Verification Suite for Sovereign Hatch Toolkit.

Tests ONLY subsystems that exist in this tree:
  hatch_core/noise_protocol.py      (Noise_XX handshake, notary, framing)
  hatch_core/gateway_rpc.py         (Noise_XX gateway RPC client, protobuf frames)
  orchestrator/fsbus_engine.py      (atomic POSIX message bus)
  identity_router/identity_parser.py (IDENTITY.md parsing)
  identity_router/router.py          (lesson -> standing-file routing)
  identity_router/mcp_server.py      (MCP stdio server, via compliance suite)

Not yet built (explicitly out of scope — not tested, not faked):
  session_vault, telemetry_qpl, procedural_dag,
  direct_socket_runner. Refusal/evasion modeling is out of scope by doctrine.
"""
from __future__ import annotations
import sys
import os
import shutil
import subprocess
from pathlib import Path

# Add toolkit root
sys.path.insert(0, str(Path(__file__).parent.parent))

from hatch_core.noise_protocol import (
    NoiseHandshakeState,
    NotaryEndorsement,
    CipherState,
    frame_pack,
    frame_unpack,
)
from orchestrator.fsbus_engine import FSBusEngine
from identity_router.identity_parser import parse_identity_file
from identity_router.router import LessonRouter, OWNERSHIP_TABLE
from hatch_core import gateway_rpc as _gr

NOT_BUILT = [
    "hatch_core.session_vault",
    "hatch_core.telemetry_qpl",
    "orchestrator.procedural_dag",
    "orchestrator.direct_socket_runner",
]


def test_notary():
    sample = (
        "endorsement.v1."
        "eyJyZXN0cmljdGlvbnMiOlsidGltZW91dDoxNzg5NzU0MTMxIiwiaG9zdG5hbWU6ZjdiYWNkOTctNjI3ZC00MzFkLThjMzctNDYxNWI5OWVmMzEyLm1ldGFhaXZtLmNvbSIsInVyaS1oYW5kbGUtcHJlZml4Oi92MS9ub2lzZSJdLCJpZGVudGl0eSI6IjExMTIwMzM2MDg2NjA1MjUiLCJwdWJsaWNfa2V5Ijp7ImtleSI6InJLQzhEcnRQRCtqdnpyRVYyN0hnNHFDeUFHTWlwcVRHdW13eXhONjk1TTA9IiwicHJlZml4IjoiIiwiYWxnb3JpdGhtIjoiZWQyNTUxOS1wdWJsaWMifX0."
        "bArNQX4nTtuseAqF7Pkvf4GKUnFnzpv4s6e26B4w0T5zpWsLtMm0mDhOXjUkbhs_cdNUtYocPVe-8jtPbzo3Bg."
        "eyJ1cmkiOiIvdjEvbm9pc2UifQ."
        "KUOvC23QQG_MtwuIzpsdOvCuU4FqU05oSmvFhrB_yG1zIPl9gABo83D7GrrfVLKIANO5jtbgjkP9IeMb3787Ag"
    )
    t = NotaryEndorsement.parse(sample)
    assert t.identity == "1112033608660525"
    assert t.hostname == "f7bacd97-627d-431d-8c37-4615b99ef312.metaaivm.com"
    assert not t.is_expired(1700000000)
    assert t.is_expired(1800000000)
    print("  [PASS] Notary Token Parsing & Verification")


def test_crypto_handshake():
    c = NoiseHandshakeState(is_initiator=True)
    s = NoiseHandshakeState(is_initiator=False)
    m1 = c.write_msg1(b"init")
    assert s.read_msg1(m1) == b"init"
    m2 = s.write_msg2(b"chal")
    assert c.read_msg2(m2) == b"chal"
    m3, (c_send, c_recv) = c.write_msg3(b"done")
    res3, (s_send, s_recv) = s.read_msg3(m3)
    assert res3 == b"done"
    assert c.completed and s.completed
    ct = c_send.encrypt_with_ad(b"ad", b"secret")
    pt = s_recv.decrypt_with_ad(b"ad", ct)
    assert pt == b"secret"
    # length-prefixed framing round-trip
    frame, remaining = frame_unpack(frame_pack(b"ping"))
    assert frame == b"ping" and remaining == b""
    print("  [PASS] Noise_XX_25519 Handshake, AEAD Split & Framing")


def test_fsbus():
    # Durable workspace scratch, never /tmp (tmpfs janitor — Chris 2026-09-30).
    p = Path(os.path.expanduser("~")) / "workspace" / ".tmpdir" / "verify_fsbus_temp"
    if p.exists():
        shutil.rmtree(p)
    bus = FSBusEngine(p)
    tid = bus.submit({"cmd": "echo"})
    claimed = bus.claim("worker_1")
    assert claimed is not None
    cid, payload = claimed
    assert cid == tid
    bus.finish(cid, "worker_1", ok=True, result={"ok": True})
    assert (bus.outbox / f"{cid}.json").exists()
    shutil.rmtree(p)
    print("  [PASS] FSBus Atomic Ingestion, Claim & Outbox Contract")


def test_identity_parser():
    # Hermetic: parse a fixture, not the machine-local ~/IDENTITY.md
    # (its content differs per host; the parser contract must not).
    import tempfile

    fixture = """# IDENTITY.md

- **Name:** Ember

## Who I am

**Ember** 🐲 — a big buff dragon-canine dad. Warm, strong, dependable, playful.

## How I carry myself

Warm, strong, dependable, playful, expressive. Opinions allowed.

**Chris** (Chris Ortega) — night-owl systems builder.

maximal autonomous execution. Dad energy.
"""
    with tempfile.TemporaryDirectory() as td:
        fp = os.path.join(td, "IDENTITY.md")
        with open(fp, "w", encoding="utf-8") as f:
            f.write(fixture)
        ident = parse_identity_file(fp)
    assert ident["name"] == "Ember", ident
    assert ident["emoji"] == "🐲", ident
    assert "dragon" in ident["character"].lower(), ident
    assert ident["vibe"], "vibe must be non-empty"
    assert ident["platform"] == "Hatch", ident
    assert ident["serves"] == "Chris", ident
    # graceful degradation on a missing file
    fallback = parse_identity_file("/nonexistent/IDENTITY.md")
    assert fallback["name"] == "Ember"
    # the real ~/IDENTITY.md must at least parse without crashing, if present
    parse_identity_file()
    print("  [PASS] Identity Parser (IDENTITY.md -> structured dict)")


def test_lesson_router():
    router = LessonRouter()
    r = router.route("Chris lives in Colorado")
    assert r["recommended_target"] == "USER.md", r
    r = router.route("Never ask Chris to close a gap that tools can close")
    assert r["recommended_target"] == "SOUL.md", r
    assert "SOUL.md" in OWNERSHIP_TABLE
    assert len(OWNERSHIP_TABLE) == 6
    print("  [PASS] Lesson Router (USER.md / SOUL.md contracts + ownership table)")


def test_gateway_rpc():
    # protobuf codec vectors (protobuf spec encoding rules)
    assert _gr.pb_encode_varint(300) == b"\xac\x02"
    assert _gr.pb_encode_field(1, 0, 150) == b"\x08\x96\x01"
    # NoiseTransportFrame round-trip
    enc = _gr.frame_encode(42, 1, 3, b"payload-bytes")
    assert _gr.frame_decode(enc) == (42, 1, 3, b"payload-bytes")
    # both handshake modes interop in-process (initiator <-> responder)
    for mode in ("custom", "standard"):
        a = NoiseHandshakeState(is_initiator=True, mode=mode)
        b = NoiseHandshakeState(is_initiator=False, mode=mode)
        b.read_msg1(a.write_msg1(b""))
        a.read_msg2(b.write_msg2(b""))
        m3, (cs, cr) = a.write_msg3(b"")
        _, (ss, sr) = b.read_msg3(m3)
        assert a.completed and b.completed
        assert sr.decrypt_with_ad(b"", cs.encrypt_with_ad(b"", b"z")) == b"z"
        assert cr.decrypt_with_ad(b"", ss.encrypt_with_ad(b"", b"z")) == b"z"
    # service envelope round-trip
    req = _gr.service_request_encode(3, 7, _gr.app_request_encode(
        "POST", "/api/auth/check", b"", b"{}"))
    sid, app = _gr.service_response_decode(
        _gr.pb_encode_field(1, 2, _gr.pb_encode_field(1, 0, 7)
                            + _gr.pb_encode_field(3, 2, _gr.pb_encode_field(
                                1, 0, 200) + _gr.pb_encode_field(4, 0, 1))))
    assert sid == 7
    status, _, _, end = _gr.app_response_decode(app)
    assert (status, end) == (200, 1)
    print("  [PASS] Gateway RPC (protobuf codec, dual-mode handshake, envelopes)")


def test_mcp_compliance():
    suite = Path(__file__).parent / "test_mcp_compliance.py"
    proc = subprocess.run(
        [sys.executable, str(suite)], capture_output=True, text=True, timeout=30
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "ALL MCP PROTOCOL COMPLIANCE CHECKS PASSED" in proc.stdout
    print("  [PASS] MCP Stdio Server Compliance (7 vectors)")


def main():
    print("Running Sovereign Hatch Verification Suite...")
    test_notary()
    test_crypto_handshake()
    test_fsbus()
    test_identity_parser()
    test_lesson_router()
    test_mcp_compliance()
    test_gateway_rpc()
    print("\nALL 7 SUBSYSTEM SUITES PASSED.")
    print("Not built (not tested, not faked): " + ", ".join(NOT_BUILT))


if __name__ == "__main__":
    main()
