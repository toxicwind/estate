#!/usr/bin/env python3
"""Squawk WebSocket push client (stdlib only).

Connects to the Squawk WS server on awrawr-pc through the Tailscale Funnel
(wss://github-mcp-host.tailc9ac71.ts.net/squawk-ws), subscribes to channels,
and appends every message envelope as one JSON line to the local spool file.

Tolerates the funnel edge's mangled 101 (it rewrites `Connection: Upgrade`
to `Connection: close` but passes frames through fine): we validate the
101 status + Sec-WebSocket-Accept and ignore the Connection header value.

Reconnects with exponential backoff; deduplicates by server seq.
"""
import base64
import hashlib
import json
import os
import socket
import ssl
import struct
import subprocess
import sys
import time
import urllib.parse

WS_HOST = "github-mcp-host.tailc9ac71.ts.net"
WS_PATH = "/squawk-ws"
TOKEN_FILE = os.path.expanduser("~/hooks/state/squawk-ws.token")
SPOOL = os.path.expanduser("~/workspace/squawk-ws-spool.jsonl")
CURSOR = os.path.expanduser("~/hooks/state/squawk-ws.cursor")
CHANNELS = ["fleet", "leads"]
PING_EVERY = 20
STALE_AFTER = 60

# 401 handling: the bearer token rotates server-side, so a stale local copy
# 401s forever. After AUTH_FAILS_BEFORE_REFRESH consecutive HTTP 401
# handshake rejections, re-fetch the token and retry. Refresh attempts are
# spaced by REFRESH_COOLDOWN (never a hot infinite refresh loop), but unlike
# a fixed per-streak cap the client never permanently gives up: a token that
# rotates again hours later still gets picked up on the next 401 streak.
AUTH_FAILS_BEFORE_REFRESH = 3
REFRESH_COOLDOWN = 600
TOKEN_FETCH_SCRIPT = os.path.expanduser("~/workspace/squawk-ws-token-fetch.py")

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def log(*a):
    print("[squawk-ws-client]", *a, flush=True)


def load_token():
    with open(TOKEN_FILE) as f:
        return f.read().strip()


def is_401_handshake(msg):
    return (msg.startswith("handshake rejected: HTTP/1.1 401")
            or msg.startswith("handshake rejected: HTTP/1.0 401"))


def refresh_token():
    """Re-run the token fetch script and reload the token file.

    Returns the fresh token string, or None when the refresh failed.
    The token value itself is never logged."""
    try:
        p = subprocess.run(
            [sys.executable, TOKEN_FETCH_SCRIPT],
            capture_output=True, text=True, timeout=180)
    except Exception as e:
        log("token refresh error: %s" % e)
        return None
    if p.returncode != 0:
        log("token refresh failed (exit %d): %.200s"
            % (p.returncode, p.stderr.strip()))
        return None
    try:
        return load_token()
    except OSError as e:
        log("token refresh failed: cannot reload token file: %s" % e)
        return None


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


def proxy_tunnel(host, port):
    proxy_url = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY")
    if not proxy_url:
        return socket.create_connection((host, port), timeout=15)
    pu = urllib.parse.urlparse(proxy_url)
    s = socket.create_connection((pu.hostname, pu.port), timeout=15)
    creds = base64.b64encode(
        ("%s:%s" % (pu.username, pu.password)).encode()).decode()
    s.sendall(
        ("CONNECT %s:%d HTTP/1.1\r\nHost: %s:%d\r\n"
         "Proxy-Authorization: Basic %s\r\n\r\n"
         % (host, port, host, port, creds)).encode())
    resp = b""
    while b"\r\n\r\n" not in resp:
        chunk = s.recv(4096)
        if not chunk:
            raise ConnectionError("proxy CONNECT failed: no response")
        resp += chunk
    if not resp.split(b"\r\n", 1)[0].startswith(b"HTTP/1.1 200"):
        raise ConnectionError("proxy CONNECT refused: %r" % resp[:60])
    return s


def ws_connect(token):
    s = proxy_tunnel(WS_HOST, 443)
    ctx = ssl._create_unverified_context()
    ts = ctx.wrap_socket(s, server_hostname=WS_HOST)
    key = base64.b64encode(os.urandom(16)).decode()
    req = (
        "GET %s HTTP/1.1\r\nHost: %s\r\n"
        "Upgrade: websocket\r\nConnection: Upgrade\r\n"
        "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n"
        "Authorization: Bearer %s\r\n\r\n"
        % (WS_PATH, WS_HOST, key, token))
    ts.sendall(req.encode())
    resp = b""
    while b"\r\n\r\n" not in resp:
        chunk = ts.recv(4096)
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
    return ts


def send_frame(ts, opcode, payload=b""):
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
    ts.sendall(hdr + mask + masked)


def send_text(ts, data: bytes):
    send_frame(ts, 0x1, data)


def send_ping(ts):
    send_frame(ts, 0x9, b"squawk")


def send_pong(ts, payload):
    send_frame(ts, 0xA, payload)


def send_close(ts):
    try:
        send_frame(ts, 0x8, b"")
    except OSError:
        pass


def recv_exact(ts, n):
    data = b""
    while len(data) < n:
        chunk = ts.recv(n - len(data))
        if not chunk:
            raise ConnectionError("connection closed by peer")
        data += chunk
    return data


def recv_frame(ts):
    b1, b2 = recv_exact(ts, 2)
    fin = bool(b1 & 0x80)
    opcode = b1 & 0x0F
    masked = bool(b2 & 0x80)
    ln = b2 & 0x7F
    if ln == 126:
        ln = struct.unpack(">H", recv_exact(ts, 2))[0]
    elif ln == 127:
        ln = struct.unpack(">Q", recv_exact(ts, 8))[0]
    mask = recv_exact(ts, 4) if masked else None
    data = recv_exact(ts, ln) if ln else b""
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
    ts = ws_connect(token)
    log("connected")
    send_text(ts, json.dumps({"subscribe": CHANNELS}).encode())
    buf = b""
    last_io = time.time()
    next_ping = last_io + PING_EVERY
    while True:
        now = time.time()
        if now - last_io > STALE_AFTER:
            raise ConnectionError("stale: no data for %ds" % STALE_AFTER)
        if now >= next_ping:
            send_ping(ts)
            next_ping = now + PING_EVERY
        ts.settimeout(max(1.0, next_ping - now))
        try:
            fin, opcode, data = recv_frame(ts)
        except socket.timeout:
            continue
        last_io = time.time()
        if opcode == 0x8:
            send_close(ts)
            raise ConnectionError("server sent close")
        elif opcode == 0x9:
            send_pong(ts, data)
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
    # Gentle backoff: the egress path throttles rapid re-TLS to one
    # destination (ClientHello blackhole). Start at 15s, cap at 5m,
    # jitter to avoid synchronized storms.
    import random
    backoff = 15
    auth_fails = 0      # consecutive HTTP 401 handshake rejections
    last_refresh = 0.0  # monotonic time of the last token refresh attempt
    while True:
        try:
            session(token, cursor)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            msg = str(e)
            if is_401_handshake(msg):
                auth_fails += 1
                since_refresh = time.monotonic() - last_refresh
                if (auth_fails >= AUTH_FAILS_BEFORE_REFRESH
                        and since_refresh >= REFRESH_COOLDOWN):
                    # Stale token: re-fetch, reload from the token file,
                    # and retry the handshake on the next loop iteration.
                    log("handshake 401 x%d; refreshing token "
                        "(%.0fs since last refresh)"
                        % (auth_fails, since_refresh))
                    new_token = refresh_token()
                    last_refresh = time.monotonic()
                    auth_fails = 0
                    if new_token and new_token != token:
                        token = new_token
                        log("TOKEN_STALE_REFRESHED")
                    else:
                        log("TOKEN_STALE_STILL_FAILING")
                else:
                    if auth_fails >= AUTH_FAILS_BEFORE_REFRESH:
                        reason = ("refresh cooldown %.0fs remaining"
                                  % (REFRESH_COOLDOWN - since_refresh))
                    else:
                        reason = ("need %d more consecutive 401s"
                                  % (AUTH_FAILS_BEFORE_REFRESH - auth_fails))
                    log("handshake 401 x%d (%s); reconnecting in %ds"
                        % (auth_fails, reason, backoff))
            else:
                # Any non-401 outcome (a successful connect, or a different
                # failure) ends the 401 streak and clears the counter.
                auth_fails = 0
                log("session ended: %s; reconnecting in %ds" % (msg, backoff))
        time.sleep(backoff + random.uniform(0, 5))
        backoff = min(backoff * 2, 300)


if __name__ == "__main__":
    main()
