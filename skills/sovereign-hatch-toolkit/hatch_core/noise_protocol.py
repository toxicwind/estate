"""
Noise Protocol & Notary Endorsement Implementation.
Reverse-engineered from Meta AI / Hatch Gateway network telemetry.
Supports Noise_XX_25519_AESGCM_SHA256 (live gateway suite) and
Noise_XX_25519_ChaChaPoly_SHA256 (legacy), plus Ed25519 Notary Tokens.

Live-gateway wire profile (AESGCM suite):
  - suite string: Noise_XX_25519_AESGCM_SHA256
  - AEAD: AES-256-GCM, 32-byte keys
  - nonce: 12 bytes = 32 zero bits + big-endian 64-bit counter
    (nonstandard; Noise spec uses little-endian)
  - msg3 variant: initiator sends a FRESH ephemeral e2 instead of its
    static key (-> encrypt(e2), DH(e2,re), payload). Wire-compatible
    with textbook XX msg3: identical byte layout (48-byte encrypted key
    + encrypted payload) and identical DH pairing, so a standard peer
    still completes the handshake; only the key choice differs.
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
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305, AESGCM
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat


PROTOCOL_NAME_CHACHAPOLY = b"Noise_XX_25519_ChaChaPoly_SHA256"
PROTOCOL_NAME_AESGCM = b"Noise_XX_25519_AESGCM_SHA256"
# Live gateway suite (hatch.metaaivm.com). ChaChaPoly kept for tests/legacy.
PROTOCOL_NAME = PROTOCOL_NAME_AESGCM


def _nonce_le(n: int) -> bytes:
    # Noise spec: 96-bit nonce = 32 zero bits + little-endian 64-bit counter.
    return b"\x00\x00\x00\x00" + struct.pack("<Q", n)


def _nonce_be(n: int) -> bytes:
    # Meta gateway wire variant: 32 zero bits + big-endian 64-bit counter.
    return b"\x00\x00\x00\x00" + struct.pack(">Q", n)


# Suite table: protocol name -> AEAD backend, nonce layout, msg3 variant flag.
_SUITES: Dict[bytes, Dict[str, Any]] = {
    PROTOCOL_NAME_CHACHAPOLY: {
        "aead": ChaCha20Poly1305,
        "nonce_fn": _nonce_le,
        "meta_msg3": False,
    },
    PROTOCOL_NAME_AESGCM: {
        "aead": AESGCM,
        "nonce_fn": _nonce_be,
        "meta_msg3": True,
    },
}


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
    """AEAD CipherState with 64-bit counter. Backend and nonce layout come from the suite."""

    def __init__(self, key: Optional[bytes] = None, *, aead=ChaCha20Poly1305, nonce_fn=_nonce_le):
        self._aead = aead
        self._nonce_fn = nonce_fn
        self.key = key
        self.nonce = 0
        if key is not None and len(key) != 32:
            raise ValueError("AEAD key must be exactly 32 bytes")

    def has_key(self) -> bool:
        return self.key is not None

    def set_key(self, key: bytes):
        if len(key) != 32:
            raise ValueError("AEAD key must be exactly 32 bytes")
        self.key = key
        self.nonce = 0

    def _nonce_bytes(self) -> bytes:
        return self._nonce_fn(self.nonce)

    def encrypt_with_ad(self, ad: bytes, plaintext: bytes) -> bytes:
        if not self.has_key():
            return plaintext
        cipher = self._aead(self.key)
        nonce_bytes = self._nonce_bytes()
        ciphertext = cipher.encrypt(nonce_bytes, plaintext, ad)
        self.nonce += 1
        return ciphertext

    def decrypt_with_ad(self, ad: bytes, ciphertext: bytes) -> bytes:
        if not self.has_key():
            return ciphertext
        cipher = self._aead(self.key)
        nonce_bytes = self._nonce_bytes()
        plaintext = cipher.decrypt(nonce_bytes, ciphertext, ad)
        self.nonce += 1
        return plaintext


class SymmetricState:
    """Manages chaining key, handshake hash, and cipher state."""

    def __init__(self, protocol_name: bytes = PROTOCOL_NAME):
        try:
            suite = _SUITES[protocol_name]
        except KeyError:
            raise ValueError(f"Unsupported Noise protocol: {protocol_name!r}")
        self._aead = suite["aead"]
        self._nonce_fn = suite["nonce_fn"]
        self.cipher_state = CipherState(aead=self._aead, nonce_fn=self._nonce_fn)
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
        c1 = CipherState(t1[:32], aead=self._aead, nonce_fn=self._nonce_fn)
        c2 = CipherState(t2[:32], aead=self._aead, nonce_fn=self._nonce_fn)
        return c1, c2


class NoiseHandshakeState:
    """
    Noise_XX Handshake State Machine:
      -> e
      <- e, ee, s, es
      -> s, se            (textbook)
      -> e2, dh(e2,re)    (Meta gateway wire variant when meta_msg3=True)
    """

    def __init__(self, is_initiator: bool, static_key: Optional[x25519.X25519PrivateKey] = None,
                 protocol_name: bytes = PROTOCOL_NAME):
        try:
            suite = _SUITES[protocol_name]
        except KeyError:
            raise ValueError(f"Unsupported Noise protocol: {protocol_name!r}")
        self.is_initiator = is_initiator
        self.static_key = static_key or x25519.X25519PrivateKey.generate()
        self.ephemeral_key = x25519.X25519PrivateKey.generate()
        self.symmetric_state = SymmetricState(protocol_name)
        self.meta_msg3 = suite["meta_msg3"]
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
        """Initiator sends -> s, se (textbook) or -> e2, dh(e2,re) (Meta variant).
        Completes handshake and splits ciphers."""
        if not self.is_initiator or self.stage != 2:
            raise RuntimeError("write_msg3 only valid for initiator at stage 2")
        if self.meta_msg3:
            # Meta gateway wire variant: fresh ephemeral e2 instead of static s.
            msg3_priv = x25519.X25519PrivateKey.generate()
        else:
            msg3_priv = self.static_key
        s_pub = msg3_priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        s_enc = self.symmetric_state.encrypt_and_hash(s_pub)

        # se (textbook) / dh(e2, re) (Meta variant) -- wire-identical
        dh_se = msg3_priv.exchange(x25519.X25519PublicKey.from_public_bytes(self.remote_ephemeral))
        self.symmetric_state.mix_key(dh_se)

        payload_enc = self.symmetric_state.encrypt_and_hash(payload)
        self.stage = 3
        self.completed = True
        c_send, c_recv = self.symmetric_state.split()
        return s_enc + payload_enc, (c_send, c_recv)

    def read_msg3(self, msg: bytes) -> Tuple[bytes, Tuple[CipherState, CipherState]]:
        """Responder reads -> s, se (or the Meta e2 variant -- wire-identical).
        Completes handshake and splits ciphers."""
        if self.is_initiator or self.stage != 2:
            raise RuntimeError("read_msg3 only valid for responder at stage 2")
        if len(msg) < 48:
            raise ValueError("Message 3 too short")
        s_enc = msg[:48]
        self.remote_static = self.symmetric_state.decrypt_and_hash(s_enc)

        # se
        dh_se = self.ephemeral_key.exchange(x25519.X25519PublicKey.from_public_bytes(self.remote_static))
        self.symmetric_state.mix_key(dh_se)

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
