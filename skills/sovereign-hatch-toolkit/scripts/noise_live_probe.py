#!/usr/bin/env python3
"""Live Noise_XX handshake probe — produces a timestamped transcript receipt.

Runs a full Noise_XX_25519_AESGCM_SHA256 handshake between an initiator and
a responder (both X25519 static keypairs generated fresh), verifies the
notary-endorsement parse/expiry path, splits into transport ciphers, and
round-trips encrypted payloads in BOTH directions. Every step is timed.

Exit 0 = PASS, nonzero = FAIL. Prints the transcript to stdout and appends
it to transcripts/noise_xx_probe_<UTC-ts>.log.
"""
import hashlib
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cryptography.hazmat.primitives.asymmetric import x25519

from hatch_core.noise_protocol import (
    NoiseHandshakeState,
    NotaryEndorsement,
    frame_pack,
    frame_unpack,
)

TS = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
LOGDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "transcripts")
os.makedirs(LOGDIR, exist_ok=True)
LOGPATH = os.path.join(LOGDIR, f"noise_xx_probe_{TS}.log")

lines = []


def say(s):
    print(s, flush=True)
    lines.append(s)


def timed(label, fn, *a, **k):
    t0 = time.perf_counter_ns()
    out = fn(*a, **k)
    dt = (time.perf_counter_ns() - t0) / 1e6
    say(f"  [{label}] {dt:8.3f} ms")
    return out


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def main():
    say(f"=== Noise_XX live probe {TS} ===")
    ok = True

    # 1. keypairs
    init_priv = timed("init static keygen", x25519.X25519PrivateKey.generate)
    resp_priv = timed("resp static keygen", x25519.X25519PrivateKey.generate)
    say(f"  init pub fp={sha(init_priv.public_key().public_bytes_raw())} "
        f"resp pub fp={sha(resp_priv.public_key().public_bytes_raw())}")

    # 2. notary endorsement path (parse + expiry + malformed rejection)
    from tests.test_noise_protocol import SAMPLE_TOKEN
    t = timed("notary parse", NotaryEndorsement.parse, SAMPLE_TOKEN)
    say(f"  identity={t.identity} hostname={t.hostname} "
        f"uri_prefix={t.uri_prefix} expired={t.is_expired()}")
    assert t.identity == "1112033608660525", "notary identity mismatch"
    assert not t.is_expired(1700000000) and t.is_expired(1800000000), "expiry logic broken"
    try:
        NotaryEndorsement.parse("endorsement.v1.too.few")
        say("  FAIL: malformed token accepted"); ok = False
    except ValueError:
        say("  malformed token rejected OK")

    # 3. handshake msg1..msg3 (custom mode = default, RE'd client variant)
    init = NoiseHandshakeState(is_initiator=True, static_key=init_priv)
    resp = NoiseHandshakeState(is_initiator=False, static_key=resp_priv)
    m1 = timed("write msg1", init.write_msg1, b"init-probe")
    assert timed("read  msg1", resp.read_msg1, m1) == b"init-probe"
    say(f"  msg1 len={len(m1)}")
    m2 = timed("write msg2", resp.write_msg2, b"challenge")
    assert timed("read  msg2", init.read_msg2, m2) == b"challenge"
    say(f"  msg2 len={len(m2)}")
    (m3, (c_send, c_recv)) = timed("write msg3", init.write_msg3, b"done")
    (r3, (s_send, s_recv)) = timed("read  msg3", resp.read_msg3, m3)
    assert r3 == b"done"
    say(f"  msg3 len={len(m3)}")
    assert init.completed and resp.completed, "handshake not completed both sides"
    say("  handshake COMPLETE both sides")

    # 4. transport round-trip, both directions
    payload_a = b"ping:" + os.urandom(32)
    ct = timed("enc i->r", c_send.encrypt_with_ad, b"ad-1", payload_a)
    pt = timed("dec i->r", s_recv.decrypt_with_ad, b"ad-1", ct)
    assert pt == payload_a, "initiator->responder payload mismatch"
    say(f"  i->r ct len={len(ct)} payload OK")

    payload_b = b"pong:" + os.urandom(32)
    ct2 = timed("enc r->i", s_send.encrypt_with_ad, b"ad-2", payload_b)
    pt2 = timed("dec r->i", c_recv.decrypt_with_ad, b"ad-2", ct2)
    assert pt2 == payload_b, "responder->initiator payload mismatch"
    say(f"  r->i ct len={len(ct2)} payload OK")

    # wrong-AD must fail (AEAD integrity)
    try:
        s_recv.decrypt_with_ad(b"wrong-ad", ct)
        say("  FAIL: wrong-AD decrypt accepted"); ok = False
    except Exception:
        say("  wrong-AD decrypt rejected OK")

    # 5. framing round-trip
    fr = frame_pack(ct)
    first, rest = frame_unpack(fr)
    assert first == ct and rest == b"", "framing round-trip broken"
    say(f"  frame_pack/unpack OK (frame len={len(fr)})")

    # 6. interop sanity: two independent sessions with fresh keys each —
    #    full msg1->msg3 handshake + transport round-trip on both;
    #    derived session keys must differ (no nonce/key reuse across sessions).
    #    (Note: the implementation is the muse.ai custom Noise_XX variant —
    #    msg3 carries a second ephemeral e2, not the standard -> s, se —
    #    so there is no "standard mode" switch; interop means self-consistent.)
    session_keys = []
    for n in range(2):
        a = NoiseHandshakeState(is_initiator=True)
        b = NoiseHandshakeState(is_initiator=False)
        x1 = a.write_msg1(); b.read_msg1(x1)
        x2 = b.write_msg2(); a.read_msg2(x2)
        x3, (a_send, a_recv) = a.write_msg3()
        y3, (b_send, b_recv) = b.read_msg3(x3)
        assert a.completed and b.completed, f"session {n} handshake not complete"
        c = a_send.encrypt_with_ad(b"a", b"std"); assert b_recv.decrypt_with_ad(b"a", c) == b"std"
        d = b_send.encrypt_with_ad(b"b", b"std2"); assert a_recv.decrypt_with_ad(b"b", d) == b"std2"
        session_keys.append(a_send.key)
    assert session_keys[0] != session_keys[1], "session keys must differ across handshakes"
    say("  interop sanity: 2 fresh sessions handshake+transport OK, session keys independent")

    say(f"=== PROBE {'PASS' if ok else 'FAIL'} ===")
    with open(LOGPATH, "w") as f:
        f.write("\n".join(lines) + "\n")
    say(f"transcript: {LOGPATH}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
