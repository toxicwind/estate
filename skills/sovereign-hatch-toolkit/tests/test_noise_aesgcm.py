"""Tests for the AES-GCM Noise suite (Noise_XX_25519_AESGCM_SHA256) -- live gateway profile.

The gateway at hatch.metaaivm.com negotiates Noise_XX_25519_AESGCM_SHA256 with a
big-endian nonce layout and a msg3 variant (fresh ephemeral e2 instead of the
initiator static key). These tests pin that behavior.
"""
import os
import struct
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from hatch_core.noise_protocol import (
    PROTOCOL_NAME,
    PROTOCOL_NAME_AESGCM,
    PROTOCOL_NAME_CHACHAPOLY,
    NoiseHandshakeState,
    SymmetricState,
)


class TestAESGCMSuite(unittest.TestCase):
    def test_default_protocol_is_live_gateway_suite(self):
        self.assertEqual(PROTOCOL_NAME, PROTOCOL_NAME_AESGCM)
        self.assertEqual(PROTOCOL_NAME, b"Noise_XX_25519_AESGCM_SHA256")

    def test_explicit_chachapoly_suite_still_handshakes(self):
        init = NoiseHandshakeState(is_initiator=True, protocol_name=PROTOCOL_NAME_CHACHAPOLY)
        resp = NoiseHandshakeState(is_initiator=False, protocol_name=PROTOCOL_NAME_CHACHAPOLY)
        m1 = init.write_msg1(b"")
        self.assertEqual(resp.read_msg1(m1), b"")
        m2 = resp.write_msg2(b"")
        self.assertEqual(init.read_msg2(m2), b"")
        m3, (c_send, c_recv) = init.write_msg3(b"")
        res3, (s_send, s_recv) = resp.read_msg3(m3)
        self.assertEqual(res3, b"")
        self.assertTrue(init.completed and resp.completed)
        self.assertEqual(init.symmetric_state.h, resp.symmetric_state.h)
        ct = c_send.encrypt_with_ad(b"ad", b"ping")
        self.assertEqual(s_recv.decrypt_with_ad(b"ad", ct), b"ping")

    def test_gateway_nonce_layout_is_big_endian(self):
        # Captured gateway wire format: 12-byte nonce = 32 zero bits +
        # big-endian 64-bit counter (nonstandard; Noise spec is little-endian).
        s = SymmetricState(PROTOCOL_NAME_AESGCM)
        key = os.urandom(32)
        s.cipher_state.set_key(key)
        ct = s.cipher_state.encrypt_with_ad(b"ad", b"vector")
        canonical = AESGCM(key).encrypt(
            b"\x00\x00\x00\x00" + struct.pack(">Q", 0), b"vector", b"ad"
        )
        self.assertEqual(ct, canonical)

    def test_meta_msg3_variant_interop(self):
        # Default AESGCM handshake uses the msg3 variant (fresh e2); the
        # reader side is wire-identical to textbook XX, so the handshake
        # completes and both directions of transport work.
        init = NoiseHandshakeState(is_initiator=True, protocol_name=PROTOCOL_NAME_AESGCM)
        resp = NoiseHandshakeState(is_initiator=False, protocol_name=PROTOCOL_NAME_AESGCM)
        self.assertTrue(init.meta_msg3)
        m1 = init.write_msg1()
        resp.read_msg1(m1)
        m2 = resp.write_msg2()
        init.read_msg2(m2)
        m3, (c_send, c_recv) = init.write_msg3()
        # Empty-payload msg3 is 48 (encrypted key) + 16 (tag) = 64 bytes,
        # matching the captured gateway msg3 length.
        self.assertEqual(len(m3), 64)
        res3, (s_send, s_recv) = resp.read_msg3(m3)
        self.assertEqual(res3, b"")
        self.assertEqual(init.symmetric_state.h, resp.symmetric_state.h)
        ct = c_send.encrypt_with_ad(b"", b"x")
        self.assertEqual(s_recv.decrypt_with_ad(b"", ct), b"x")
        ct2 = s_send.encrypt_with_ad(b"", b"y")
        self.assertEqual(c_recv.decrypt_with_ad(b"", ct2), b"y")

    def test_cross_suite_handshake_fails(self):
        init = NoiseHandshakeState(is_initiator=True, protocol_name=PROTOCOL_NAME_AESGCM)
        resp = NoiseHandshakeState(is_initiator=False, protocol_name=PROTOCOL_NAME_CHACHAPOLY)
        m1 = init.write_msg1()
        resp.read_msg1(m1)
        m2 = resp.write_msg2()
        with self.assertRaises(Exception):
            init.read_msg2(m2)


if __name__ == "__main__":
    unittest.main()
