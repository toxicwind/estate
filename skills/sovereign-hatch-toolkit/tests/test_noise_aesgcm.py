"""Tests for the AES-GCM Noise suite (Noise_XX_25519_AESGCM_SHA256) -- live gateway profile.

The gateway at hatch.metaaivm.com negotiates Noise_XX_25519_AESGCM_SHA256 with a
big-endian nonce layout (nonce12(n) = [0x00]*4 || u32be(hi) || u32be(lo)) and a
msg3 variant (fresh ephemeral e2 instead of the initiator static key).
These tests pin that behavior against hatch_core/noise_protocol.py.
"""
import os
import struct
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from hatch_core.noise_protocol import (
    PROTOCOL_NAME,
    CipherState,
    NoiseHandshakeState,
    SymmetricState,
)


class TestAESGCMSuite(unittest.TestCase):
    def test_protocol_name_is_live_gateway_suite(self):
        self.assertEqual(PROTOCOL_NAME, b"Noise_XX_25519_AESGCM_SHA256")

    def test_handshake_completes_and_transport_works_both_directions(self):
        init = NoiseHandshakeState(is_initiator=True)
        resp = NoiseHandshakeState(is_initiator=False)
        m1 = init.write_msg1(b"hello")
        self.assertEqual(resp.read_msg1(m1), b"hello")
        m2 = resp.write_msg2(b"challenge")
        self.assertEqual(init.read_msg2(m2), b"challenge")
        m3, (c_send, c_recv) = init.write_msg3(b"done")
        payload, (s_send, s_recv) = resp.read_msg3(m3)
        self.assertEqual(payload, b"done")
        self.assertTrue(init.completed and resp.completed)
        self.assertEqual(init.symmetric_state.h, resp.symmetric_state.h)
        ct = c_send.encrypt_with_ad(b"ad", b"ping")
        self.assertEqual(s_recv.decrypt_with_ad(b"ad", ct), b"ping")
        ct2 = s_send.encrypt_with_ad(b"ad", b"pong")
        self.assertEqual(c_recv.decrypt_with_ad(b"ad", ct2), b"pong")

    def test_nonce_layout_is_big_endian(self):
        # Gateway wire format: 12-byte nonce = 32 zero bits + big-endian
        # 64-bit counter (nonstandard; Noise spec is little-endian).
        self.assertEqual(CipherState._nonce_bytes(0), b"\x00" * 12)
        self.assertEqual(
            CipherState._nonce_bytes(1), b"\x00\x00\x00\x00" + struct.pack(">Q", 1)
        )
        key = os.urandom(32)
        c = CipherState(key)
        ct = c.encrypt_with_ad(b"ad", b"vector")
        canonical = AESGCM(key).encrypt(
            b"\x00\x00\x00\x00" + struct.pack(">Q", 0), b"vector", b"ad"
        )
        self.assertEqual(ct, canonical)

    def test_nonce_counter_one_diverges_from_little_endian(self):
        # Counter zero cannot distinguish BE from LE (both are 12 zero
        # bytes); encrypt twice so the second message uses counter 1.
        key = os.urandom(32)
        c = CipherState(key)
        c.encrypt_with_ad(b"ad", b"first")
        ct = c.encrypt_with_ad(b"ad", b"second")
        be = AESGCM(key).encrypt(
            b"\x00\x00\x00\x00" + struct.pack(">Q", 1), b"second", b"ad"
        )
        le = AESGCM(key).encrypt(
            b"\x00\x00\x00\x00" + struct.pack("<Q", 1), b"second", b"ad"
        )
        self.assertEqual(ct, be)
        self.assertNotEqual(ct, le)

    def test_key_must_be_32_bytes(self):
        c = CipherState()
        with self.assertRaises(ValueError):
            c.set_key(b"too-short")

    def test_symmetric_state_defaults_to_live_suite(self):
        s = SymmetricState()
        # 28-byte protocol name -> h = name zero-padded to 32 bytes
        self.assertEqual(len(PROTOCOL_NAME), 28)
        self.assertEqual(s.h, PROTOCOL_NAME.ljust(32, b"\x00"))
        self.assertEqual(s.ck, s.h)


if __name__ == "__main__":
    unittest.main()
