"""Tests for hatch_core/noise_protocol.py — Noise_XX_25519_ChaChaPoly_SHA256."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hatch_core.noise_protocol import (
    b64url_encode,
    b64url_decode,
    NotaryEndorsement,
    CipherState,
    SymmetricState,
    NoiseHandshakeState,
    frame_pack,
    frame_unpack,
)

SAMPLE_TOKEN = (
    "endorsement.v1."
    "eyJyZXN0cmljdGlvbnMiOlsidGltZW91dDoxNzg5NzU0MTMxIiwiaG9zdG5hbWU6ZjdiYWNkOTctNjI3ZC00MzFkLThjMzctNDYxNWI5OWVmMzEyLm1ldGFhaXZtLmNvbSIsInVyaS1oYW5kbGUtcHJlZml4Oi92MS9ub2lzZSJdLCJpZGVudGl0eSI6IjExMTIwMzM2MDg2NjA1MjUiLCJwdWJsaWNfa2V5Ijp7ImtleSI6InJLQzhEcnRQRCtqdnpyRVYyN0hnNHFDeUFHTWlwcVRHdW13eXhONjk1TTA9IiwicHJlZml4IjoiIiwiYWxnb3JpdGhtIjoiZWQyNTUxOS1wdWJsaWMifX0."
    "bArNQX4nTtuseAqF7Pkvf4GKUnFnzpv4s6e26B4w0T5zpWsLtMm0mDhOXjUkbhs_cdNUtYocPVe-8jtPbzo3Bg."
    "eyJ1cmkiOiIvdjEvbm9pc2UifQ."
    "KUOvC23QQG_MtwuIzpsdOvCuU4FqU05oSmvFhrB_yG1zIPl9gABo83D7GrrfVLKIANO5jtbgjkP9IeMb3787Ag"
)


class TestB64Url(unittest.TestCase):
    def test_roundtrip(self):
        data = os.urandom(64)
        self.assertEqual(b64url_decode(b64url_encode(data)), data)

    def test_no_padding_chars(self):
        enc = b64url_encode(b"\xfb\xff\xfe")
        self.assertNotIn("=", enc)
        self.assertNotIn("+", enc)
        self.assertNotIn("/", enc)


class TestNotaryEndorsement(unittest.TestCase):
    def test_parse_sample(self):
        t = NotaryEndorsement.parse(SAMPLE_TOKEN)
        self.assertEqual(t.identity, "1112033608660525")
        self.assertEqual(
            t.hostname, "f7bacd97-627d-431d-8c37-4615b99ef312.metaaivm.com"
        )
        self.assertEqual(t.uri_prefix, "/v1/noise")
        self.assertEqual(t.timeout_ts, 1789754131)

    def test_expiry(self):
        t = NotaryEndorsement.parse(SAMPLE_TOKEN)
        self.assertFalse(t.is_expired(1700000000))
        self.assertTrue(t.is_expired(1800000000))

    def test_malformed_raises(self):
        with self.assertRaises(ValueError):
            NotaryEndorsement.parse("endorsement.v1.too.few")


class TestCipherState(unittest.TestCase):
    def test_roundtrip_with_ad(self):
        c = CipherState()
        c.set_key(os.urandom(32))
        ct = c.encrypt_with_ad(b"ad", b"secret message")
        self.assertNotEqual(ct, b"secret message")
        # fresh state, same key, decrypt first ciphertext (nonce 0)
        d = CipherState()
        d.set_key(c.key)
        self.assertEqual(d.decrypt_with_ad(b"ad", ct), b"secret message")

    def test_nonce_advances(self):
        c = CipherState()
        c.set_key(os.urandom(32))
        ct1 = c.encrypt_with_ad(b"", b"same")
        ct2 = c.encrypt_with_ad(b"", b"same")
        self.assertNotEqual(ct1, ct2)  # different nonces -> different ct

    def test_wrong_ad_fails(self):
        c = CipherState()
        c.set_key(os.urandom(32))
        ct = c.encrypt_with_ad(b"ad", b"data")
        d = CipherState()
        d.set_key(c.key)
        with self.assertRaises(Exception):
            d.decrypt_with_ad(b"wrong-ad", ct)

    def test_no_key_passthrough(self):
        c = CipherState()
        self.assertFalse(c.has_key())
        self.assertEqual(c.encrypt_with_ad(b"ad", b"plain"), b"plain")
        self.assertEqual(c.decrypt_with_ad(b"ad", b"plain"), b"plain")

    def test_bad_key_length(self):
        c = CipherState()
        with self.assertRaises(ValueError):
            c.set_key(b"short")

    def test_nonce_layout_matches_noise_spec_12_3(self):
        # Noise §12.3: 96-bit nonce = 32 bits of zeros followed by
        # little-endian n. Ciphertext must equal an independent
        # ChaCha20Poly1305 computed with the canonical nonce bytes.
        import struct
        from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
        key = os.urandom(32)
        c = CipherState()
        c.set_key(key)
        ct = c.encrypt_with_ad(b"ad", b"vector")
        canonical = ChaCha20Poly1305(key).encrypt(
            b"\x00\x00\x00\x00" + struct.pack("<Q", 0), b"vector", b"ad"
        )
        self.assertEqual(ct, canonical)


class TestHandshake(unittest.TestCase):
    def _handshake(self, p1=b"init", p2=b"chal", p3=b"done"):
        init = NoiseHandshakeState(is_initiator=True)
        resp = NoiseHandshakeState(is_initiator=False)
        m1 = init.write_msg1(p1)
        self.assertEqual(resp.read_msg1(m1), p1)
        m2 = resp.write_msg2(p2)
        self.assertEqual(init.read_msg2(m2), p2)
        m3, (c_send, c_recv) = init.write_msg3(p3)
        res3, (s_send, s_recv) = resp.read_msg3(m3)
        self.assertEqual(res3, p3)
        self.assertTrue(init.completed and resp.completed)
        return (c_send, c_recv), (s_send, s_recv)

    def test_full_xx_handshake(self):
        self._handshake()

    def test_transport_both_directions(self):
        (c_send, c_recv), (s_send, s_recv) = self._handshake()
        ct = c_send.encrypt_with_ad(b"ad", b"ping")
        self.assertEqual(s_recv.decrypt_with_ad(b"ad", ct), b"ping")
        ct2 = s_send.encrypt_with_ad(b"ad", b"pong")
        self.assertEqual(c_recv.decrypt_with_ad(b"ad", ct2), b"pong")

    def test_wrong_stage_raises(self):
        init = NoiseHandshakeState(is_initiator=True)
        with self.assertRaises(RuntimeError):
            init.write_msg2()
        resp = NoiseHandshakeState(is_initiator=False)
        with self.assertRaises(RuntimeError):
            resp.write_msg1()

    def test_symmetric_state_mix(self):
        s1, s2 = SymmetricState(), SymmetricState()
        s1.mix_hash(b"hello")
        s2.mix_hash(b"hello")
        self.assertEqual(s1.h, s2.h)
        s1.mix_key(b"ikm")
        s2.mix_key(b"ikm")
        self.assertEqual(s1.ck, s2.ck)


class TestFraming(unittest.TestCase):
    def test_pack_unpack_roundtrip(self):
        data = b"frame payload"
        packed = frame_pack(data)
        frame, rest = frame_unpack(packed)
        self.assertEqual(frame, data)
        self.assertEqual(rest, b"")

    def test_partial_buffer(self):
        packed = frame_pack(b"abc")
        frame, rest = frame_unpack(packed[:2])
        self.assertIsNone(frame)
        self.assertEqual(rest, packed[:2])

    def test_oversize_rejected(self):
        with self.assertRaises(ValueError):
            frame_pack(b"x" * 65536)


if __name__ == "__main__":
    unittest.main()
