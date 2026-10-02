"""Noise_XX gateway RPC client for the Hatch personal gateway.

What this is
------------
The missing ``hatch_core.gateway_rpc`` subsystem (``verify_all.py`` listed it
as "not built"): a client that performs the ``Noise_XX_25519_AESGCM_SHA256``
handshake over a WebSocket to the gateway, then exchanges protobuf-framed
service RPCs over the Noise transport.

Protocol sources
----------------
* ``docs/PROTOCOL.md`` (nikships/muse-cli @ bcd5ee14, derived from the web
  client's own bundle and verified live):
  ``wss://hatch.metaaivm.com/v1/noise?vm_id=..&auth_token=..``,
  standard Noise XX with empty payloads both ways, ``NoiseTransportFrame``
  protobuf chunked frames, ``ServiceRequest``/``ServiceResponse`` envelopes,
  services daemon 0 / sentinel 1 / vault 2 / authd 3, stream ids from 1,
  subscriptions stream ``application/x-ndjson``.
* ``hatch_core/noise_protocol.py`` in this repo: handshake state machine with
  two modes -- ``custom`` (the RE'd muse.ai client variant: msg3 carries a
  second ephemeral, non-standard big-endian nonce) and ``standard`` (Noise
  XX per the framework spec: msg3 carries the static key, stock
  4-zero-bytes + u64-LE nonce).

Handshake variant status (2026-10-02): the two sources disagree on msg3.
This client defaults to ``standard`` per the independently verified doc and
keeps ``custom`` as a fallback. The variant is NOT resolved by a live test
here: a credentialed handshake needs the account auth token, which is
Chris's to provide -- see ``scripts/gateway_diagnose.py`` for the
no-credentials transport probe that establishes how far the path goes.

MITM finding (2026-10-02, verified live from the hatch cell): all egress
TLS goes through the sandbox egress proxy, which terminates TLS and
presents its own CA (``CN=Hatch Sandbox Egress CA``). The Noise_XX handshake
runs *inside* the TLS tunnel at the WebSocket layer, so its bytes are
unaffected -- but the client MUST trust the proxy CA at the TLS layer
(system trust store, which includes it) and MUST tunnel via HTTP CONNECT.
``websocket-client`` is configured accordingly below.

Threading (from PROTOCOL.md): concurrent frame reads from two threads split
frames and corrupt the stateful Noise decrypt (fatal BAD_DECRYPT). All
receives are serialized with a lock; callers keep exactly one consumer.
"""

from __future__ import annotations

import json
import os
import socket
import ssl
import struct
import threading
import time
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

try:
    import websocket  # websocket-client (sync)
except ImportError:  # pragma: no cover
    websocket = None

from hatch_core.noise_protocol import NoiseHandshakeState, PROTOCOL_NAME

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CONFIG_PATH = Path(__file__).parent.parent / "config" / "gateway_config.json"

SERVICES = {"daemon": 0, "sentinel": 1, "vault": 2, "authd": 3}


def load_config(path: Optional[Path] = None) -> dict:
    """Load gateway_config.json. Never logs or returns credential values."""
    p = Path(path) if path else CONFIG_PATH
    return json.loads(p.read_text(encoding="utf-8"))


def build_url(cfg: dict, vm_id: Optional[str] = None,
              auth_token: Optional[str] = None) -> str:
    """Build the wss URL. The token is used, never logged -- callers must
    redact it before printing."""
    vm = vm_id or cfg.get("default_vm_id", "")
    q = {"vm_id": vm}
    if auth_token:
        q["auth_token"] = auth_token
    return cfg["gateway_url"] + "?" + urllib.parse.urlencode(q)


def redact_url(url: str) -> str:
    """Replace the auth_token query value for safe logging."""
    parts = urllib.parse.urlsplit(url)
    q = urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
    q = [(k, "<redacted>" if k == "auth_token" else v) for k, v in q]
    return urllib.parse.urlunsplit(
        (parts.scheme, parts.hostname or "", parts.path,
         urllib.parse.urlencode(q), ""))


# ---------------------------------------------------------------------------
# Minimal protobuf codec (varint + length-delimited only)
# ---------------------------------------------------------------------------
# Field numbers below are DERIVED from the field order documented in
# PROTOCOL.md (NoiseTransportFrame{chunk_id, chunk_index, total_chunks,
# payload}, etc.). They are the doc's order, not a verified descriptor --
# treat as provisional until a credentialed session confirms the wire bytes.

def pb_encode_varint(n: int) -> bytes:
    if n < 0:
        n &= 0xFFFFFFFFFFFFFFFF
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            break
    return bytes(out)


def pb_decode_varint(buf: bytes, pos: int) -> Tuple[int, int]:
    result = 0
    shift = 0
    while True:
        if pos >= len(buf):
            raise ValueError("truncated varint")
        b = buf[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, pos
        shift += 7
        if shift >= 64:
            raise ValueError("varint overflow")


def pb_encode_field(num: int, wire: int, value) -> bytes:
    tag = pb_encode_varint((num << 3) | wire)
    if wire == 0:
        return tag + pb_encode_varint(value)
    if wire == 2:
        if isinstance(value, str):
            value = value.encode("utf-8")
        return tag + pb_encode_varint(len(value)) + value
    raise ValueError(f"unsupported wire type {wire}")


def pb_decode_fields(buf: bytes) -> List[Tuple[int, int, object]]:
    """Decode protobuf fields -> [(field_number, wire_type, value)]."""
    out = []
    pos = 0
    while pos < len(buf):
        tag, pos = pb_decode_varint(buf, pos)
        num, wire = tag >> 3, tag & 0x07
        if wire == 0:
            v, pos = pb_decode_varint(buf, pos)
            out.append((num, wire, v))
        elif wire == 2:
            ln, pos = pb_decode_varint(buf, pos)
            out.append((num, wire, buf[pos:pos + ln]))
            pos += ln
        else:
            raise ValueError(f"unsupported wire type {wire} in decode")
    return out


# --- NoiseTransportFrame{chunk_id(i64)=1, chunk_index=2, total_chunks=3, payload=4}

def frame_encode(chunk_id: int, chunk_index: int, total_chunks: int,
                 payload: bytes) -> bytes:
    return (pb_encode_field(1, 0, chunk_id)
            + pb_encode_field(2, 0, chunk_index)
            + pb_encode_field(3, 0, total_chunks)
            + pb_encode_field(4, 2, payload))


def frame_decode(buf: bytes) -> Tuple[int, int, int, bytes]:
    d = {n: v for n, w, v in pb_decode_fields(buf)}
    return int(d[1]), int(d[2]), int(d[3]), bytes(d[4])


# --- ApplicationRequest{verb=1, path=2, headers=3, body=4, end_body=5}
# --- ApplicationResponse{status=1, headers=2, body=3, end_body=4}
# --- ServiceFrame{stream_id=1, request=2, response=3}
# --- ServiceRequest{service=1, payload=2} / ServiceResponse{payload=1}

def app_request_encode(verb: str, path: str, headers: bytes,
                       body: bytes) -> bytes:
    return (pb_encode_field(1, 2, verb)
            + pb_encode_field(2, 2, path)
            + pb_encode_field(3, 2, headers)
            + pb_encode_field(4, 2, body)
            + pb_encode_field(5, 0, 1))


def app_response_decode(buf: bytes) -> Tuple[int, bytes, bytes, int]:
    d = {n: v for n, w, v in pb_decode_fields(buf)}
    return int(d[1]), bytes(d.get(2, b"")), bytes(d.get(3, b"")), int(d.get(4, 0))


def service_request_encode(service: int, stream_id: int,
                           app_request: bytes) -> bytes:
    frame = pb_encode_field(1, 0, stream_id) + pb_encode_field(2, 2, app_request)
    return pb_encode_field(1, 0, service) + pb_encode_field(2, 2, frame)


def service_response_decode(buf: bytes) -> Tuple[int, bytes]:
    """ServiceResponse -> (stream_id, application_response_bytes)."""
    d = {n: v for n, w, v in pb_decode_fields(buf)}
    frame = {n: v for n, w, v in pb_decode_fields(bytes(d[1]))}
    stream_id = int(frame[1])
    resp_fields = {n: v for n, w, v in pb_decode_fields(bytes(frame[3]))}
    return stream_id, bytes(resp_fields[3]) if 3 in resp_fields else b""


# ---------------------------------------------------------------------------
# Gateway client
# ---------------------------------------------------------------------------

@dataclass
class RpcResponse:
    stream_id: int
    status: int
    headers: bytes
    body: bytes


class GatewayClient:
    """Noise_XX WebSocket RPC client.

    ``sock`` may be injected (an object with ``send(bytes)`` and
    ``recv() -> bytes``) for tests; otherwise a real WebSocket is opened in
    :meth:`connect`.
    """

    def __init__(self, config: Optional[dict] = None,
                 vm_id: Optional[str] = None,
                 auth_token: Optional[str] = None,
                 handshake_mode: str = "standard",
                 sock=None):
        self.cfg = config or load_config()
        self.vm_id = vm_id or self.cfg.get("default_vm_id", "")
        self.auth_token = auth_token or os.environ.get("HATCH_AUTH_TOKEN", "")
        if handshake_mode not in ("standard", "custom"):
            raise ValueError("handshake_mode must be 'standard' or 'custom'")
        self.handshake_mode = handshake_mode
        self._sock = sock
        self._ws = None
        self._send_cipher = None
        self._recv_cipher = None
        self._read_lock = threading.Lock()
        self._stream_id = 0
        self._chunk_id = 0
        self.frame_max = int(self.cfg.get("noise_protocol", {})
                             .get("frame_max_bytes", 65535))

    # -- transport ------------------------------------------------------

    @staticmethod
    def _proxy_opts() -> dict:
        """Explicit proxy wiring: honor the sandbox egress proxy env."""
        opts: dict = {}
        proxy = (os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY")
                 or os.environ.get("http_proxy") or os.environ.get("HTTP_PROXY"))
        if proxy:
            p = urllib.parse.urlsplit(proxy)
            opts["http_proxy_host"] = p.hostname
            opts["http_proxy_port"] = p.port or 8080
            if p.username:
                opts["http_proxy_auth"] = (
                    urllib.parse.unquote(p.username),
                    urllib.parse.unquote(p.password or ""))
        return opts

    def connect(self, timeout: float = 20.0) -> "GatewayClient":
        if websocket is None:
            raise RuntimeError("websocket-client is not installed")
        url = build_url(self.cfg, self.vm_id, self.auth_token)
        sslopt = {"cert_reqs": ssl.CERT_REQUIRED}
        self._ws = websocket.create_connection(
            url, timeout=timeout, sslopt=sslopt, **self._proxy_opts())
        self._sock = _WsAdapter(self._ws)
        self._handshake()
        return self

    def _handshake(self) -> None:
        """Noise XX with empty payloads both ways (PROTOCOL.md)."""
        hs = NoiseHandshakeState(is_initiator=True, mode=self.handshake_mode)
        self._sock.send(hs.write_msg1(b""))
        msg2 = self._sock.recv()
        hs.read_msg2(msg2)
        msg3, (send_c, recv_c) = hs.write_msg3(b"")
        self._sock.send(msg3)
        self._send_cipher, self._recv_cipher = send_c, recv_c

    # -- framing --------------------------------------------------------

    def _send_frame_plaintext(self, plaintext: bytes) -> None:
        # plaintext chunks sized so ciphertext stays within frame_max
        chunk_size = self.frame_max - 32
        chunks = [plaintext[i:i + chunk_size]
                  for i in range(0, len(plaintext), chunk_size)] or [b""]
        self._chunk_id += 1
        cid = self._chunk_id
        total = len(chunks)
        for idx, ch in enumerate(chunks):
            frame = frame_encode(cid, idx, total, ch)
            ct = self._send_cipher.encrypt_with_ad(b"", frame)
            self._sock.send(ct)

    def _recv_frame_plaintext(self) -> bytes:
        """Read and reassemble one full chunked message. Serialized:
        concurrent reads corrupt the stateful Noise decrypt."""
        with self._read_lock:
            parts: Dict[int, bytes] = {}
            total = None
            cid = None
            while True:
                ct = self._sock.recv()
                frame = self._recv_cipher.decrypt_with_ad(b"", ct)
                fcid, idx, ftotal, payload = frame_decode(frame)
                if cid is None:
                    cid, total = fcid, ftotal
                if fcid != cid:
                    raise RuntimeError(
                        f"chunk stream interleave: {fcid} != {cid}")
                parts[idx] = payload
                if len(parts) == total:
                    return b"".join(parts[i] for i in range(total))

    # -- RPC ------------------------------------------------------------

    def call(self, service: str, verb: str, path: str,
             body: bytes = b"", headers: bytes = b"",
             timeout: float = 30.0) -> RpcResponse:
        """Unary RPC: one ServiceRequest, collect ServiceResponse frames
        until end_body."""
        if isinstance(service, str):
            service = SERVICES[service]
        self._stream_id += 1
        sid = self._stream_id
        req = service_request_encode(
            service, sid, app_request_encode(verb, path, headers, body))
        self._send_frame_plaintext(req)
        deadline = time.time() + timeout
        resp_body = b""
        status, resp_headers = 0, b""
        while True:
            if time.time() > deadline:
                raise TimeoutError(f"RPC {verb} {path} timed out")
            plaintext = self._recv_frame_plaintext()
            rsid, app_resp = service_response_decode(plaintext)
            if rsid != sid:
                raise RuntimeError(
                    f"stream id mismatch: {rsid} != {sid}")
            st, hd, chunk, end = app_response_decode(app_resp)
            status, resp_headers = st, hd
            resp_body += chunk
            if end:
                return RpcResponse(sid, status, resp_headers, resp_body)

    def subscribe(self, service: str, verb: str, path: str,
                  body: bytes = b"") -> Iterator[bytes]:
        """Server-streaming RPC: yields body chunks until end_body."""
        if isinstance(service, str):
            service = SERVICES[service]
        self._stream_id += 1
        sid = self._stream_id
        req = service_request_encode(
            service, sid, app_request_encode(verb, path, b"", body))
        self._send_frame_plaintext(req)
        while True:
            plaintext = self._recv_frame_plaintext()
            rsid, app_resp = service_response_decode(plaintext)
            if rsid != sid:
                raise RuntimeError(
                    f"stream id mismatch: {rsid} != {sid}")
            _, _, chunk, end = app_response_decode(app_resp)
            if chunk:
                yield chunk
            if end:
                return

    def close(self) -> None:
        try:
            if self._ws is not None:
                self._ws.close()
        finally:
            self._ws = None
            self._sock = None


class _WsAdapter:
    """Adapt websocket-client to the send/recv interface used in tests."""

    def __init__(self, ws):
        self._ws = ws

    def send(self, data: bytes) -> None:
        self._ws.send_binary(data)

    def recv(self) -> bytes:
        data = self._ws.recv()
        if isinstance(data, str):
            data = data.encode("utf-8")
        return data


# ---------------------------------------------------------------------------
# No-credentials transport diagnostic
# ---------------------------------------------------------------------------

def diagnose_transport(gateway_url: str = "wss://hatch.metaaivm.com/v1/noise",
                       vm_id: str = "", timeout: float = 10.0) -> dict:
    """Probe how far the gateway path goes WITHOUT any auth token.

    Stages: tcp -> proxy CONNECT -> TLS (report issuer CN) -> WS upgrade
    (report HTTP status). Returns an ordered stage report; never touches
    credentials. A 401/403 at the upgrade stage is the EXPECTED healthy
    result: it proves the MITM proxy path is intact and the gate is auth.
    """
    stages: List[Tuple[str, bool, str]] = []
    host, port = "hatch.metaaivm.com", 443

    proxy = (os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY")
             or os.environ.get("http_proxy") or os.environ.get("HTTP_PROXY"))
    raw = socket.create_connection(
        (urllib.parse.urlsplit(proxy).hostname,
         urllib.parse.urlsplit(proxy).port or 8080) if proxy else (host, port),
        timeout=timeout)
    stages.append(("tcp", True,
                   f"connected via {'proxy ' + proxy.split('@')[-1] if proxy else 'direct'}"))
    try:
        if proxy:
            raw.sendall(f"CONNECT {host}:{port} HTTP/1.1\r\nHost: {host}\r\n\r\n"
                        .encode())
            resp = raw.recv(4096).decode("latin1")
            line = resp.split("\r\n", 1)[0]
            ok = " 200" in line
            stages.append(("proxy_connect", ok, line.strip()))
            if not ok:
                return {"stages": stages}
        ctx = ssl.create_default_context()
        tls = ctx.wrap_socket(raw, server_hostname=host)
        issuer = dict(x[0] for x in tls.getpeercert().get("issuer", ()))
        stages.append(("tls", True,
                       f"issuer CN={issuer.get('commonName', '?')}"))
        # Minimal WS upgrade WITHOUT auth token: expect 401/403.
        key = "dGhlIHNhbXBsZSBub25jZQ=="
        path = "/v1/noise?vm_id=" + urllib.parse.quote(vm_id)
        req = (f"GET {path} HTTP/1.1\r\nHost: {host}\r\nUpgrade: websocket\r\n"
               f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
               f"Sec-WebSocket-Version: 13\r\n\r\n")
        tls.sendall(req.encode())
        resp = tls.recv(4096).decode("latin1", "replace")
        line = resp.split("\r\n", 1)[0]
        # 101 without a token would be surprising; anything else is the
        # auth gate doing its job.
        stages.append(("ws_upgrade_no_token", True,
                       f"no-token upgrade -> {line.strip()} (expected non-101)"))
        tls.close()
    except Exception as e:  # noqa: BLE001 - diagnostic must not raise
        stages.append(("error", False, f"{type(e).__name__}: {e}"))
    return {"stages": stages}
