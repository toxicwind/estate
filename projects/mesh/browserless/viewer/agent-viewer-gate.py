#!/usr/bin/env python3
# agent-viewer-gate.py — token-gated front door for the noVNC agent viewer.
#
# Forge 2026-09-21: Chris corrected "view only is no point, user should be
# able to interact" — the noVNC viewer is INTERACTIVE, and :6080 binds
# loopback-only. This gate is the token-gated external route: the funnel
# mounts this port at /agent-browser, and every request needs
# ?token=<viewer-token> (or the `aview` cookie a successful token check
# issues). After auth it transparently proxies bytes to websockify on
# 127.0.0.1:6080 — HTTP and websocket upgrades alike — so noVNC's relative
# asset URLs and its ./websockify WS path all work under the subpath mount.
#
# Token: /home/toxic/.browserless/viewer-token (0600, generated once).
# VNC auth itself is untouched: noVNC still prompts for the Xvnc password,
# which is Chris's and is never stored here.
#
# Endpoints:
#   GET /healthz            200 ok, no token (pitchfork ready_cmd)
#   anything else           403 unless ?token= matches or aview cookie valid
import hashlib
import hmac
import os
import select
import socket
import threading
import urllib.parse

LISTEN = ("127.0.0.1", 6081)
UPSTREAM = ("127.0.0.1", 6080)
TOKEN_FILE = "/home/toxic/.browserless/viewer-token"
COOKIE_NAME = "aview"
MAX_HEAD = 65536
IDLE_TIMEOUT = 300


def log(*args):
    print("gate:", *args, flush=True)


def load_token():
    try:
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()
    except OSError:
        return ""


def cookie_value(token):
    return hashlib.sha256(token.encode()).hexdigest()


def authorized(target, headers, token):
    """Returns (ok, issue_cookie)."""
    if not token:
        return False, False
    qs = urllib.parse.parse_qs(urllib.parse.urlsplit(target).query)
    presented = qs.get("token", [""])[0]
    if presented and hmac.compare_digest(presented, token):
        return True, True
    want = cookie_value(token)
    for chunk in headers.get("cookie", "").split(";"):
        name, _, val = chunk.strip().partition("=")
        if name == COOKIE_NAME and hmac.compare_digest(val.strip(), want):
            return True, False
    return False, False


def read_head(conn):
    data = b""
    while b"\r\n\r\n" not in data:
        try:
            chunk = conn.recv(4096)
        except OSError:
            break
        if not chunk:
            break
        data += chunk
        if len(data) > MAX_HEAD:
            break
    return data


def pipe(a, b):
    try:
        while True:
            r, _, _ = select.select([a, b], [], [], IDLE_TIMEOUT)
            if not r:
                break
            for s in r:
                try:
                    chunk = s.recv(65536)
                except OSError:
                    return
                if not chunk:
                    return
                try:
                    (b if s is a else a).sendall(chunk)
                except OSError:
                    return
    finally:
        for s in (a, b):
            try:
                s.close()
            except OSError:
                pass


def handle(conn, addr):
    up = None
    try:
        head = read_head(conn)
        if not head or b"\r\n\r\n" not in head:
            conn.close()
            return
        lines = head.split(b"\r\n\r\n", 1)[0].decode("latin1").split("\r\n")
        try:
            method, target = lines[0].split(" ", 2)[:2]
        except ValueError:
            conn.close()
            return
        headers = {}
        for line in lines[1:]:
            k, _, v = line.partition(":")
            headers[k.strip().lower()] = v.strip()

        path = urllib.parse.urlsplit(target).path
        if path == "/healthz":
            conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n"
                         b"Connection: close\r\n\r\nok")
            conn.close()
            return

        token = load_token()
        ok, issue_cookie = authorized(target, headers, token)
        if not ok:
            body = b"forbidden: viewer token required"
            conn.sendall(b"HTTP/1.1 403 Forbidden\r\nContent-Type: text/plain\r\n"
                         b"Content-Length: " + str(len(body)).encode() +
                         b"\r\nConnection: close\r\n\r\n" + body)
            conn.close()
            return

        up = socket.create_connection(UPSTREAM, timeout=10)
        up.sendall(head)

        # Read the upstream response head so we can inject Set-Cookie.
        resp = b""
        while b"\r\n\r\n" not in resp:
            chunk = up.recv(4096)
            if not chunk:
                break
            resp += chunk
            if len(resp) > MAX_HEAD:
                break
        if issue_cookie and b"\r\n\r\n" in resp:
            rhead, _, rrest = resp.partition(b"\r\n\r\n")
            cookie_hdr = ("Set-Cookie: %s=%s; Path=/; HttpOnly; "
                          "SameSite=Lax\r\n" % (COOKIE_NAME, cookie_value(token)))
            resp = rhead + cookie_hdr.encode("latin1") + b"\r\n\r\n" + rrest
        conn.sendall(resp)
        pipe(conn, up)
    except OSError:
        pass
    finally:
        for s in (conn, up):
            if s is not None:
                try:
                    s.close()
                except OSError:
                    pass


def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(LISTEN)
    srv.listen(64)
    log("listening on %s:%d -> %s:%d" % (LISTEN + UPSTREAM))
    while True:
        conn, addr = srv.accept()
        t = threading.Thread(target=handle, args=(conn, addr), daemon=True)
        t.start()


if __name__ == "__main__":
    main()
