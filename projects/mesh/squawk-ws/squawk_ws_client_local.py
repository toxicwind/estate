#!/usr/bin/env python3
"""squawk-ws local push client (stdlib only) — runs ON awrawr-pc.

Connects directly to the squawk-ws server at 127.0.0.1:25147 (plain WS,
no TLS, no proxy, no funnel), subscribes to channels, and appends every
message envelope as one JSON line to the local spool file.

Cell-proof by construction: it runs as a pitchfork daemon on awrawr-pc,
so cell death cannot touch it. The spool and cursor live on awrawr-pc disk.

Reconnect policy: there is NO internal sleep/backoff loop. On any session
failure the process exits non-zero and pitchfork (retry=true) restarts it
with its own backoff. The server replays the last ~20 messages per channel
on subscribe, so transient drops lose nothing (cursor dedupes).

No `sleep` anywhere in this file.
"""
import base64
import hashlib
import json
import os
import socket
import struct
import time

HOST = os.environ.get("SQUAWK_WS_HOST", "127.0.0.1")
PORT = int(os.environ.get("SQUAWK_WS_PORT", "25147"))
WS_PATH = "/squawk-ws"
TOKEN_FILE = os.environ.get("SQUAWK_WS_TOKEN_FILE", "/home/toxic/.squawk-ws-token")
SPOOL = os.environ.get("SQUAWK_WS_CLIENT_SPOOL",
                       "/home/toxic/squawk-ws/client-spool.jsonl")
CURSOR = os.environ.get("SQUAWK_WS_CLIENT_CURSOR",
                        "/home/toxic/squawk-ws/client-cursor.json")
HEARTBEAT = os.environ.get("SQUAWK_WS_CLIENT_HEARTBEAT",
                           "/home/toxic/squawk-ws/client-heartbeat")
CHANNELS = [c for c in os.environ.get("SQUAWK_WS_CHANNELS", "fleet,leads").split(",") if c]
PING_EVERY = 20
STALE_AFTER = 60

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def log(*a):
    print("[squawk-ws-local-client]", *a, flush=True)


def load_token():
    with open(TOKEN_FILE) as f:
        tok = f.read().strip()
    if not tok:
        raise RuntimeError("empty token in %s" % TOKEN_FILE)
    return tok


def load_cursor():
    try:
        with open(CURSOR) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_cursor(cur):
    tmp = CURSOR + ".tmp"
    with open(tmp, "w") as f:
        json.dump(cur, f)
    os.replace(tmp, CURSOR)


def spool_append(env):
    with open(SPOOL, "a") as f:
        f.write(json.dumps(env, ensure_ascii=True) + "\n")


def touch_heartbeat():
    with open(HEARTBEAT, "w") as f:
        f.write("%.3f\n" % time.time())


def ws_connect(token):
    s = socket.create_connection((HOST, PORT), timeout=15)
    key = base64.b64encode(os.urandom(16)).decode()
    req = (
        "GET %s HTTP/1.1\r\nHost: %s:%d\r\n"
        "Upgrade: websocket\r\nConnection: Upgrade\r\n"
        "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n"
        "Authorization: Bearer %s\r\n\r\n"
        % (WS_PATH, HOST, PORT, key, token))
    s.sendall(req.encode())
    resp = b""
    while b"\r\n\r\n" not in resp:
        chunk = s.recv(4096)
        if not chunk:
            raise ConnectionError("handshake: connection closed")
        resp += chunk
    head = resp.split(b"\r\n\r\n", 1)[0].decode("latin-1")
    lines = head.split("\r\n")
    if not lines[0].startswith("HTTP/1.1 101"):
        raise ConnectionError("handshake rejected: %s" % lines[0])
    accept = None
    for ln in lines[1:]:
        if ln.lower().startswith("sec-websocket-accept:"):
            accept = ln.split(":", 1)[1].strip()
    expect = base64.b64encode(
        hashlib.sha1((key + GUID).encode()).digest()).decode()
    if accept != expect:
        raise ConnectionError("handshake: bad Sec-WebSocket-Accept")
    return s


def send_frame(s, opcode, payload=b""):
    mask = os.urandom(4)
    n = len(payload)
    hdr = bytes([0x80 | opcode])
    if n < 126:
        hdr += bytes([0x80 | n])
    elif n < 65536:
        hdr += bytes([0x80 | 126]) + struct.pack(">H", n)
    else:
        hdr += bytes([0x80 | 127]) + struct.pack(">Q", n)
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    s.sendall(hdr + mask + masked)


def recv_exact(s, n):
    data = b""
    while len(data) < n:
        chunk = s.recv(n - len(data))
        if not chunk:
            raise ConnectionError("connection closed by peer")
        data += chunk
    return data


def recv_frame(s):
    b1, b2 = recv_exact(s, 2)
    fin = bool(b1 & 0x80)
    opcode = b1 & 0x0F
    masked = bool(b2 & 0x80)
    ln = b2 & 0x7F
    if ln == 126:
        ln = struct.unpack(">H", recv_exact(s, 2))[0]
    elif ln == 127:
        ln = struct.unpack(">Q", recv_exact(s, 8))[0]
    mask = recv_exact(s, 4) if masked else None
    data = recv_exact(s, ln) if ln else b""
    if mask:
        data = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
    return fin, opcode, data


def handle_message(env, cursor):
    ch = env.get("channel")
    seq = env.get("seq")
    if ch not in CHANNELS or not isinstance(seq, int):
        return
    if seq <= cursor.get(ch, -1):
        return
    cursor[ch] = seq
    spool_append(env)
    save_cursor(cursor)
    log("spooled seq=%d ch=%s from=%s" % (seq, ch, env.get("sender")))


def session(token, cursor):
    s = ws_connect(token)
    log("connected to %s:%d" % (HOST, PORT))
    touch_heartbeat()
    send_frame(s, 0x1, json.dumps({"subscribe": CHANNELS}).encode())
    buf = b""
    last_io = time.time()
    next_ping = last_io + PING_EVERY
    while True:
        now = time.time()
        if now - last_io > STALE_AFTER:
            raise ConnectionError("stale: no data for %ds" % STALE_AFTER)
        if now >= next_ping:
            send_frame(s, 0x9, b"squawk")
            touch_heartbeat()
            next_ping = now + PING_EVERY
        s.settimeout(max(1.0, next_ping - now))
        try:
            fin, opcode, data = recv_frame(s)
        except socket.timeout:
            continue
        last_io = time.time()
        if opcode == 0x8:
            raise ConnectionError("server sent close")
        elif opcode == 0x9:
            send_frame(s, 0xA, data)
        elif opcode == 0xA:
            pass
        elif opcode in (0x1, 0x0):
            buf += data
            if not fin:
                continue
            payload, buf = buf, b""
            try:
                env = json.loads(payload.decode("utf-8"))
            except ValueError:
                continue
            if isinstance(env, dict):
                if env.get("type") == "history_end":
                    log("backfill complete")
                elif "seq" in env:
                    handle_message(env, cursor)


def main():
    token = load_token()
    cursor = load_cursor()
    try:
        session(token, cursor)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        # No sleep/backoff here: exit and let pitchfork retry with backoff.
        log("session ended: %s; exiting for supervisor retry" % e)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
