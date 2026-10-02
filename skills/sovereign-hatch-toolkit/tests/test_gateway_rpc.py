"""Tests for hatch_core/gateway_rpc.py -- Noise_XX gateway RPC client."""
import os
import socket
import sys
import threading
import unittest

from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hatch_core import gateway_rpc as gr
from hatch_core.gateway_rpc import (
    GatewayClient,
    RpcResponse,
    app_request_encode,
    app_response_decode,
    build_url,
    frame_decode,
    frame_encode,
    load_config,
    pb_decode_fields,
    pb_decode_varint,
    pb_encode_field,
    pb_encode_varint,
    redact_url,
    service_request_encode,
    service_response_decode,
)
from hatch_core.noise_protocol import NoiseHandshakeState


class FakeSock:
    """In-memory connected pair end."""

    def __init__(self):
        self._a, self._b = socket.socketpair()
        self._a.settimeout(5)
        self._b.settimeout(5)

    def client_end(self):
        return _SockEnd(self._a)

    def server_end(self):
        return _SockEnd(self._b)

    def close(self):
        self._a.close()
        self._b.close()


class _SockEnd:
    def __init__(self, s):
        self._s = s

    def send(self, data: bytes) -> None:
        self._s.sendall(len(data).to_bytes(4, "big") + data)

    def recv(self) -> bytes:
        n = int.from_bytes(self._recvn(4), "big")
        return self._recvn(n)

    def _recvn(self, n):
        buf = b""
        while len(buf) < n:
            ch = self._s.recv(n - len(buf))
            if not ch:
                raise ConnectionError("peer closed")
            buf += ch
        return buf


def do_handshake(mode):
    """Run a full initiator<->responder handshake in-process for mode."""
    fs = FakeSock()
    ce, se = fs.client_end(), fs.server_end()
    init = NoiseHandshakeState(is_initiator=True, mode=mode)
    resp = NoiseHandshakeState(is_initiator=False, mode=mode)
    ce.send(init.write_msg1(b""))
    resp.read_msg1(se.recv())
    se.send(resp.write_msg2(b""))
    init.read_msg2(ce.recv())
    m3, (cs, cr) = init.write_msg3(b"")
    ce.send(m3)
    _, (ss, sr) = resp.read_msg3(se.recv())
    fs.close()
    return (cs, cr), (ss, sr)


class TestProtobufCodec(unittest.TestCase):
    def test_varint_vectors(self):
        self.assertEqual(pb_encode_varint(0), b"\x00")
        self.assertEqual(pb_encode_varint(1), b"\x01")
        self.assertEqual(pb_encode_varint(300), b"\xac\x02")
        self.assertEqual(pb_encode_varint(2**64 - 1), b"\xff" * 9 + b"\x01")

    def test_varint_roundtrip(self):
        for n in (0, 1, 127, 128, 300, 65535, 2**63 - 1):
            v, pos = pb_decode_varint(pb_encode_varint(n), 0)
            self.assertEqual((v, pos), (n, len(pb_encode_varint(n))))

    def test_field_tag_encoding(self):
        # field 1, varint -> tag 0x08; value 150 -> 0x96 0x01 (protobuf spec example)
        self.assertEqual(pb_encode_field(1, 0, 150), b"\x08\x96\x01")

    def test_decode_fields_roundtrip(self):
        buf = (pb_encode_field(1, 0, 7)
               + pb_encode_field(2, 0, 300)
               + pb_encode_field(4, 2, b"hello"))
        self.assertEqual(pb_decode_fields(buf),
                         [(1, 0, 7), (2, 0, 300), (4, 2, b"hello")])

    def test_truncated_raises(self):
        with self.assertRaises(ValueError):
            pb_decode_varint(b"\x80", 0)


class TestTransportFrame(unittest.TestCase):
    def test_frame_roundtrip(self):
        payload = os.urandom(1000)
        enc = frame_encode(123456789, 2, 5, payload)
        cid, idx, total, out = frame_decode(enc)
        self.assertEqual((cid, idx, total, out), (123456789, 2, 5, payload))

    def test_frame_field_order_matches_doc(self):
        # NoiseTransportFrame{chunk_id, chunk_index, total_chunks, payload}:
        # first tag must be field 1 varint (0x08), last field tag 0x22 (field 4, LEN)
        enc = frame_encode(1, 0, 1, b"x")
        self.assertEqual(enc[0], 0x08)
        self.assertIn(b"\x22", enc)


class TestServiceEnvelope(unittest.TestCase):
    def test_request_response_roundtrip(self):
        body = b'{"hello": "world"}'
        req = service_request_encode(3, 9, app_request_encode(
            "POST", "/api/auth/check", b"", body))
        fields = {n: v for n, w, v in pb_decode_fields(req)}
        self.assertEqual(fields[1], 3)  # service id passes through
        # response side: build a synthetic ServiceResponse and decode
        app_resp = (pb_encode_field(1, 0, 200) + pb_encode_field(3, 2, b"ok")
                    + pb_encode_field(4, 0, 1))
        frame = pb_encode_field(1, 0, 9) + pb_encode_field(3, 2, app_resp)
        sresp = pb_encode_field(1, 2, frame)
        sid, app = service_response_decode(sresp)
        self.assertEqual(sid, 9)
        status, hd, rbody, end = app_response_decode(app)
        self.assertEqual((status, rbody, end), (200, b"ok", 1))


class TestHandshakeModes(unittest.TestCase):
    def test_custom_mode_interop(self):
        (cs, cr), (ss, sr) = do_handshake("custom")
        ct = cs.encrypt_with_ad(b"", b"ping")
        self.assertEqual(sr.decrypt_with_ad(b"", ct), b"ping")
        ct2 = ss.encrypt_with_ad(b"", b"pong")
        self.assertEqual(cr.decrypt_with_ad(b"", ct2), b"pong")

    def test_standard_mode_interop(self):
        (cs, cr), (ss, sr) = do_handshake("standard")
        ct = cs.encrypt_with_ad(b"", b"ping")
        self.assertEqual(sr.decrypt_with_ad(b"", ct), b"ping")
        ct2 = ss.encrypt_with_ad(b"", b"pong")
        self.assertEqual(cr.decrypt_with_ad(b"", ct2), b"pong")

    def test_modes_do_not_interop(self):
        # standard initiator vs custom responder must fail (different msg3)
        fs = FakeSock()
        ce, se = fs.client_end(), fs.server_end()
        init = NoiseHandshakeState(is_initiator=True, mode="standard")
        resp = NoiseHandshakeState(is_initiator=False, mode="custom")
        ce.send(init.write_msg1(b""))
        resp.read_msg1(se.recv())
        se.send(resp.write_msg2(b""))
        init.read_msg2(ce.recv())
        m3, _ = init.write_msg3(b"")
        ce.send(m3)
        with self.assertRaises(Exception):
            resp.read_msg3(se.recv())
        fs.close()

    def test_standard_msg3_carries_static_key(self):
        init = NoiseHandshakeState(is_initiator=True, mode="standard")
        resp = NoiseHandshakeState(is_initiator=False, mode="standard")
        m1 = init.write_msg1(b"")
        resp.read_msg1(m1)
        m2 = resp.write_msg2(b"")
        init.read_msg2(m2)
        m3, _ = init.write_msg3(b"")
        # s_enc (32+16) + empty payload tag (16) = 64 bytes
        self.assertEqual(len(m3), 64)
        # responder learns the initiator's static key in standard mode
        _, (ss, sr) = resp.read_msg3(m3)
        self.assertEqual(resp.remote_static,
                         init.static_key.public_key().public_bytes(
                             Encoding.Raw, PublicFormat.Raw))


class TestClientChunking(unittest.TestCase):
    def _paired_clients(self, mode="standard"):
        fs = FakeSock()
        ce, se = fs.client_end(), fs.server_end()
        cli = GatewayClient(config={"gateway_url": "wss://x", "default_vm_id": "v",
                                    "noise_protocol": {"frame_max_bytes": 128}},
                            handshake_mode=mode, sock=ce)
        # server side: minimal responder driving the same handshake
        resp = NoiseHandshakeState(is_initiator=False, mode=mode)
        init = NoiseHandshakeState(is_initiator=True, mode=mode)
        # drive handshake manually over the pair
        ce.send(init.write_msg1(b""))
        resp.read_msg1(se.recv())
        se.send(resp.write_msg2(b""))
        init.read_msg2(ce.recv())
        m3, (cs, cr) = init.write_msg3(b"")
        ce.send(m3)
        _, (ss, sr) = resp.read_msg3(se.recv())
        cli._send_cipher, cli._recv_cipher = cs, cr
        return cli, se, ss, sr, fs

    def test_multichunk_roundtrip(self):
        cli, se, ss, sr, fs = self._paired_clients()
        try:
            big = os.urandom(500)  # > frame_max 128 -> multiple chunks
            t = threading.Thread(target=cli._send_frame_plaintext, args=(big,))
            t.start()
            # server: reassemble raw frames like _recv_frame_plaintext does
            parts, total, cid = {}, None, None
            while True:
                n = int.from_bytes(se._recvn(4), "big")
                ct = se._recvn(n)
                f = frame_decode(sr.decrypt_with_ad(b"", ct))
                if cid is None:
                    cid, total = f[0], f[2]
                parts[f[1]] = f[3]
                if len(parts) == total:
                    break
            t.join()
            self.assertEqual(b"".join(parts[i] for i in range(total)), big)
        finally:
            fs.close()

    def test_concurrent_reads_stay_serialized(self):
        # Regression for the PROTOCOL.md BAD_DECRYPT quirk: two threads
        # reading through the client's lock must each get intact messages.
        cli, se, ss, sr, fs = self._paired_clients()
        try:
            msgs = [os.urandom(40) for _ in range(8)]
            def server_send():
                for m in msgs:
                    f = frame_encode(777, 0, 1, m)
                    se.send(ss.encrypt_with_ad(b"", f))
            st = threading.Thread(target=server_send)
            st.start()
            got = []
            def reader():
                for _ in range(4):
                    got.append(cli._recv_frame_plaintext())
            r1 = threading.Thread(target=reader)
            r2 = threading.Thread(target=reader)
            r1.start(); r2.start(); r1.join(); r2.join(); st.join()
            self.assertEqual(sorted(got), sorted(msgs))
        finally:
            fs.close()


class TestConfigAndUrl(unittest.TestCase):
    def test_load_config(self):
        cfg = load_config()
        self.assertIn("gateway_url", cfg)
        self.assertTrue(cfg["gateway_url"].startswith("wss://"))
        self.assertIn("rpc_methods", cfg)
        self.assertIn("noise_protocol", cfg)

    def test_redact_url(self):
        url = build_url({"gateway_url": "wss://h.example/v1/noise",
                         "default_vm_id": "vm1"}, auth_token="sekrit")
        self.assertIn("auth_token=sekrit", url)
        red = redact_url(url)
        self.assertNotIn("sekrit", red)
        self.assertIn("auth_token=%3Credacted%3E", red)


if __name__ == "__main__":
    unittest.main()
