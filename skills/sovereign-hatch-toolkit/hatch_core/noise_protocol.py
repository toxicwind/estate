"""
Noise Protocol & Notary Endorsement Implementation.
Reverse-engineered from Meta AI / Hatch Gateway network telemetry.

Implements Noise_XX_25519_AESGCM_SHA256 with the muse.ai client's custom
msg3 variant (second ephemeral instead of static key) and non-standard
nonce construction. Plus Ed25519 Notary Endorsement token parser.

CORRECTION (2026-09-30): two independent REs (nikships/muse-cli,
bytehola/muse-guardian) confirm AES-256-GCM, not ChaChaPoly.
"""
from __future__ import annotations
import base64
import hashlib
import hmac
import json
import struct
import time
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any

from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat


PROTOCOL_NAME = b"Noise_XX_25519_AESGCM_SHA256"


def b64url_decode(s: str) -> bytes:
    """Decode base64url string with padding restoration."""
    s = s.replace("-", "+").replace("_", "/")
    pad = len(s) % 4
    if pad:
        s += "=" * (4 - pad)
    return base64.b64decode(s)


def b64url_encode(b: bytes) -> str:
    """Encode bytes to base64url string without padding."""
    return base64.b64encode(b).decode("ascii").replace("+", "-").replace("/", "_").rstrip("=")


@dataclass
class NotaryEndorsement:
    """Parsed Ed25519 notary endorsement token."""
    version: str
    identity: str
    public_key_b64: str
    hostname: str
    timeout_ts: int
    uri_prefix: str
    raw_payload1: str
    signature1: bytes
    raw_payload2: str
    signature2: bytes

    @classmethod
    def parse(cls, token_str: str) -> "NotaryEndorsement":
        """
        Parse endorsement token of format:
        endorsement.v1.<payload1>.<sig1>.<payload2>.<sig2>
        """
        parts = token_str.split(".")
        if len(parts) < 6:
            raise ValueError(f"Invalid notary token structure: expected at least 6 parts, got {len(parts)}")
        
        prefix = f"{parts[0]}.{parts[1]}"
        payload1_raw = parts[2]
        sig1_raw = parts[3]
        payload2_raw = parts[4]
        sig2_raw = parts[5]

        p1_bytes = b64url_decode(payload1_raw)
        p1 = json.loads(p1_bytes.decode("utf-8"))

        identity = p1.get("identity", "")
        pubkey = p1.get("public_key", {}).get("key", "")
        
        hostname = ""
        timeout_ts = 0
        uri_prefix = ""

        for r in p1.get("restrictions", []):
            if r.startswith("hostname:"):
                hostname = r.split(":", 1)[1]
            elif r.startswith("timeout:"):
                timeout_ts = int(r.split(":", 1)[1])
            elif r.startswith("uri-handle-prefix:"):
                uri_prefix = r.split(":", 1)[1]

        return cls(
            version=prefix,
            identity=identity,
            public_key_b64=pubkey,
            hostname=hostname,
            timeout_ts=timeout_ts,
            uri_prefix=uri_prefix,
            raw_payload1=payload1_raw,
            signature1=b64url_decode(sig1_raw),
            raw_payload2=payload2_raw,
            signature2=b64url_decode(sig2_raw),
        )

    def is_expired(self, current_time: Optional[int] = None) -> bool:
        now = int(time.time()) if current_time is None else current_time
        return self.timeout_ts > 0 and now > self.timeout_ts


class CipherState:
    """AES-256-GCM CipherState with 64-bit counter.

    Nonce is NON-STANDARD (replicated byte-for-byte from the muse.ai client):
        nonce12(n) = [0x00]*4 || u32be(n >> 32) || u32be(n & 0xffffffff)
    A stock Noise implementation (4 zero bytes + 64-bit little-endian) will
    NOT interoperate.
    """

    def __init__(self, key: Optional[bytes] = None):
        self.key = key
        self.nonce = 0

    def has_key(self) -> bool:
        return self.key is not None

    def set_key(self, key: bytes):
        if len(key) != 32:
            raise ValueError("AESGCM key must be exactly 32 bytes")
        self.key = key
        self.nonce = 0

    @staticmethod
    def _nonce_bytes(n: int) -> bytes:
        return b"\x00\x00\x00\x00" + struct.pack(">I", (n >> 32) & 0xFFFFFFFF) + struct.pack(">I", n & 0xFFFFFFFF)

    def encrypt_with_ad(self, ad: bytes, plaintext: bytes) -> bytes:
        if not self.has_key():
            return plaintext
        cipher = AESGCM(self.key)
        nonce_bytes = self._nonce_bytes(self.nonce)
        ciphertext = cipher.encrypt(nonce_bytes, plaintext, ad)
        self.nonce += 1
        return ciphertext

    def decrypt_with_ad(self, ad: bytes, ciphertext: bytes) -> bytes:
        if not self.has_key():
            return ciphertext
        cipher = AESGCM(self.key)
        nonce_bytes = self._nonce_bytes(self.nonce)
        plaintext = cipher.decrypt(nonce_bytes, ciphertext, ad)
        self.nonce += 1
        return plaintext


class SymmetricState:
    """Manages chaining key, handshake hash, and cipher state."""

    def __init__(self, protocol_name: bytes = PROTOCOL_NAME):
        self.cipher_state = CipherState()
        self.ck = b""
        self.h = b""
        self.initialize_symmetric(protocol_name)

    def initialize_symmetric(self, protocol_name: bytes):
        if len(protocol_name) <= 32:
            self.h = protocol_name.ljust(32, b"\x00")
        else:
            self.h = hashlib.sha256(protocol_name).digest()
        self.ck = self.h

    def mix_key(self, input_key_material: bytes):
        prk = hmac.new(self.ck, input_key_material, hashlib.sha256).digest()
        t1 = hmac.new(prk, b"\x01", hashlib.sha256).digest()
        t2 = hmac.new(prk, t1 + b"\x02", hashlib.sha256).digest()
        self.ck = t1
        temp_k = t2[:32]
        self.cipher_state.set_key(temp_k)

    def mix_hash(self, data: bytes):
        self.h = hashlib.sha256(self.h + data).digest()

    def mix_key_and_hash(self, input_key_material: bytes):
        prk = hmac.new(self.ck, input_key_material, hashlib.sha256).digest()
        t1 = hmac.new(prk, b"\x01", hashlib.sha256).digest()
        t2 = hmac.new(prk, t1 + b"\x02", hashlib.sha256).digest()
        t3 = hmac.new(prk, t2 + b"\x03", hashlib.sha256).digest()
        self.ck = t1
        self.mix_hash(t2)
        self.cipher_state.set_key(t3[:32])

    def encrypt_and_hash(self, plaintext: bytes) -> bytes:
        ciphertext = self.cipher_state.encrypt_with_ad(self.h, plaintext)
        self.mix_hash(ciphertext)
        return ciphertext

    def decrypt_and_hash(self, ciphertext: bytes) -> bytes:
        plaintext = self.cipher_state.decrypt_with_ad(self.h, ciphertext)
        self.mix_hash(ciphertext)
        return plaintext

    def split(self) -> Tuple[CipherState, CipherState]:
        prk = hmac.new(self.ck, b"", hashlib.sha256).digest()
        t1 = hmac.new(prk, b"\x01", hashlib.sha256).digest()
        t2 = hmac.new(prk, t1 + b"\x02", hashlib.sha256).digest()
        c1 = CipherState(t1[:32])
        c2 = CipherState(t2[:32])
        return c1, c2


class NoiseHandshakeState:
    """
    Noise_XX Handshake State Machine (muse.ai custom variant):
      -> e
      <- e, ee, s, es
      -> e2 (second ephemeral), DH(e2, re)     # NOT standard -> s, se
    """

    def __init__(self, is_initiator: bool, static_key: Optional[x25519.X25519PrivateKey] = None):
        self.is_initiator = is_initiator
        self.static_key = static_key or x25519.X25519PrivateKey.generate()
        self.ephemeral_key = x25519.X25519PrivateKey.generate()
        self.symmetric_state = SymmetricState()
        self.remote_static: Optional[bytes] = None
        self.remote_ephemeral: Optional[bytes] = None
        self.stage = 0
        self.completed = False

    def write_msg1(self, payload: bytes = b"") -> bytes:
        """Initiator sends -> e."""
        if not self.is_initiator or self.stage != 0:
            raise RuntimeError("write_msg1 only valid for initiator at stage 0")
        e_pub = self.ephemeral_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        self.symmetric_state.mix_hash(e_pub)
        msg = e_pub + self.symmetric_state.encrypt_and_hash(payload)
        self.stage = 1
        return msg

    def read_msg1(self, msg: bytes) -> bytes:
        """Responder reads -> e."""
        if self.is_initiator or self.stage != 0:
            raise RuntimeError("read_msg1 only valid for responder at stage 0")
        if len(msg) < 32:
            raise ValueError("Message 1 too short for X25519 public key")
        self.remote_ephemeral = msg[:32]
        self.symmetric_state.mix_hash(self.remote_ephemeral)
        payload = self.symmetric_state.decrypt_and_hash(msg[32:])
        self.stage = 1
        return payload

    def write_msg2(self, payload: bytes = b"") -> bytes:
        """Responder sends <- e, ee, s, es."""
        if self.is_initiator or self.stage != 1:
            raise RuntimeError("write_msg2 only valid for responder at stage 1")
        e_pub = self.ephemeral_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        self.symmetric_state.mix_hash(e_pub)

        # ee
        dh_ee = self.ephemeral_key.exchange(x25519.X25519PublicKey.from_public_bytes(self.remote_ephemeral))
        self.symmetric_state.mix_key(dh_ee)

        # s (encrypted static)
        s_pub = self.static_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        s_enc = self.symmetric_state.encrypt_and_hash(s_pub)

        # es
        dh_es = self.static_key.exchange(x25519.X25519PublicKey.from_public_bytes(self.remote_ephemeral))
        self.symmetric_state.mix_key(dh_es)

        payload_enc = self.symmetric_state.encrypt_and_hash(payload)
        self.stage = 2
        return e_pub + s_enc + payload_enc

    def read_msg2(self, msg: bytes) -> bytes:
        """Initiator reads <- e, ee, s, es."""
        if not self.is_initiator or self.stage != 1:
            raise RuntimeError("read_msg2 only valid for initiator at stage 1")
        if len(msg) < 80:  # 32 (e) + 48 (s encrypted: 32 + 16 tag)
            raise ValueError("Message 2 too short")
        self.remote_ephemeral = msg[:32]
        self.symmetric_state.mix_hash(self.remote_ephemeral)

        # ee
        dh_ee = self.ephemeral_key.exchange(x25519.X25519PublicKey.from_public_bytes(self.remote_ephemeral))
        self.symmetric_state.mix_key(dh_ee)

        # s
        s_enc = msg[32:80]
        self.remote_static = self.symmetric_state.decrypt_and_hash(s_enc)

        # es
        dh_es = self.ephemeral_key.exchange(x25519.X25519PublicKey.from_public_bytes(self.remote_static))
        self.symmetric_state.mix_key(dh_es)

        payload = self.symmetric_state.decrypt_and_hash(msg[80:])
        self.stage = 2
        return payload

    def write_msg3(self, payload: bytes = b"") -> Tuple[bytes, Tuple[CipherState, CipherState]]:
        """Initiator sends custom msg3: second ephemeral e2, DH(e2, re).

        DEVIATION FROM STANDARD NOISE XX: the muse.ai client does NOT send
        the static key here. It generates a fresh second ephemeral e2, sends
        e2_pub encrypted, mixes DH(e2, re), then encrypts the payload.
        Byte-for-byte replica of the RE'd client (msg3 = 64 bytes typical).
        Completes handshake and splits ciphers.
        """
        if not self.is_initiator or self.stage != 2:
            raise RuntimeError("write_msg3 only valid for initiator at stage 2")
        e2 = x25519.X25519PrivateKey.generate()
        e2_pub = e2.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        e2_enc = self.symmetric_state.encrypt_and_hash(e2_pub)

        # DH(e2, re)
        dh_e2re = e2.exchange(x25519.X25519PublicKey.from_public_bytes(self.remote_ephemeral))
        self.symmetric_state.mix_key(dh_e2re)

        payload_enc = self.symmetric_state.encrypt_and_hash(payload)
        self.stage = 3
        self.completed = True
        c_send, c_recv = self.symmetric_state.split()
        return e2_enc + payload_enc, (c_send, c_recv)

    def read_msg3(self, msg: bytes) -> Tuple[bytes, Tuple[CipherState, CipherState]]:
        """Responder reads custom msg3: decrypt e2_pub, DH(s, e2_pub).

        Completes handshake and splits ciphers.
        """
        if self.is_initiator or self.stage != 2:
            raise RuntimeError("read_msg3 only valid for responder at stage 2")
        if len(msg) < 48:
            raise ValueError("Message 3 too short")
        e2_pub = self.symmetric_state.decrypt_and_hash(msg[:48])

        # DH(e_priv, e2_pub) — matches initiator's DH(e2_priv, re_pub)
        dh_e2re = self.ephemeral_key.exchange(x25519.X25519PublicKey.from_public_bytes(e2_pub))
        self.symmetric_state.mix_key(dh_e2re)

        payload = self.symmetric_state.decrypt_and_hash(msg[48:])
        self.stage = 3
        self.completed = True
        c_recv, c_send = self.symmetric_state.split()
        return payload, (c_send, c_recv)


def frame_pack(data: bytes) -> bytes:
    """Pack data with 2-byte big-endian length prefix."""
    if len(data) > 65535:
        raise ValueError(f"Payload exceeds maximum frame size: {len(data)} > 65535")
    return struct.pack("!H", len(data)) + data


def frame_unpack(buffer: bytes) -> Tuple[Optional[bytes], bytes]:
    """Unpack first 2-byte prefixed frame from buffer. Returns (frame, remaining_buffer)."""
    if len(buffer) < 2:
        return None, buffer
    frame_len = struct.unpack("!H", buffer[:2])[0]
    if len(buffer) < 2 + frame_len:
        return None, buffer
    frame = buffer[2:2 + frame_len]
    return frame, buffer[2 + frame_len:]
