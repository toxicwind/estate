#!/usr/bin/env python3
"""Verify the dashboard /ws/fleet feed end to end.

Connects, expects `hello` then `fleet:init` (roster + recent messages),
then publishes a GENUINE new squawk message file and requires it to arrive
as a pushed `squawk` frame with exact from/title/body/seq — no restart,
no polling. Exit 0 on pass, 1 on fail.

Usage: python3 scripts/ws-verify.py [--host 127.0.0.1] [--port 25201]
"""
import argparse
import base64
import glob
import json
import os
import re
import socket
import struct
import sys
import time

FLEET_DIR = "/home/toxic/.shingle/squawk-root/fleet"
PROBE_FROM = "ws-verify"
PROBE_TITLE = "ws-verify liveness probe"
PROBE_BODY = "genuine new squawk message; must arrive via /ws/fleet push"


def ws_connect(host, port):
    s = socket.create_connection((host, port), timeout=10)
    key = base64.b64encode(os.urandom(16)).decode()
    req = (
        "GET /ws/fleet HTTP/1.1\r\nHost: %s:%d\r\nUpgrade: websocket\r\n"
        "Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\n"
        "Sec-WebSocket-Version: 13\r\n\r\n" % (host, port, key)
    )
    s.sendall(req.encode())
    resp = b""
    while b"\r\n\r\n" not in resp:
        chunk = s.recv(4096)
        if not chunk:
            raise RuntimeError("handshake: connection closed")
        resp += chunk
    status = resp.split(b"\r\n", 1)[0].decode()
    print("handshake:", status, flush=True)
    if "101" not in status:
        raise RuntimeError("expected 101, got: " + status)
    return s


def read_frame(s):
    hdr = b""
    while len(hdr) < 2:
        hdr += s.recv(2 - len(hdr))
    b1, b2 = hdr
    opcode = b1 & 0x0F
    ln = b2 & 0x7F
    if ln == 126:
        ln = struct.unpack(">H", s.recv(2))[0]
    elif ln == 127:
        ln = struct.unpack(">Q", s.recv(8))[0]
    data = b""
    while len(data) < ln:
        data += s.recv(ln - len(data))
    if opcode == 8:
        raise RuntimeError("server closed the socket")
    if opcode != 1:
        return None
    return json.loads(data.decode())


def next_seq():
    files = glob.glob(os.path.join(FLEET_DIR, "*.md"))
    seqs = []
    for f in files:
        m = re.match(r"(\d+)-", os.path.basename(f))
        if m:
            seqs.append(int(m.group(1)))
    return max(seqs, default=0) + 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=25201)
    args = ap.parse_args()

    s = ws_connect(args.host, args.port)

    hello = read_frame(s)
    assert hello and hello.get("type") == "hello", "missing hello frame"
    print("frame: hello", flush=True)

    init = read_frame(s)
    assert init and init.get("type") == "fleet:init", "missing fleet:init frame"
    roster, messages = init.get("roster", []), init.get("messages", [])
    print("frame: fleet:init roster=%d messages=%d" % (len(roster), len(messages)), flush=True)
    assert roster, "fleet:init roster empty"

    seq = next_seq()
    ts = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    fm = (
        "---\nseq: %d\nfrom: %s\nto: all\nchannel: fleet\nts: %s\n"
        "status: discussion\ntitle: %s\n---\n%s\n"
        % (seq, PROBE_FROM, ts, PROBE_TITLE, PROBE_BODY)
    )
    path = os.path.join(FLEET_DIR, "%d-%s-msg.md" % (seq, PROBE_FROM))
    with open(path, "w") as f:
        f.write(fm)
    print("published squawk file: %s (seq=%d)" % (path, seq), flush=True)

    s.settimeout(10)
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            m = read_frame(s)
        except socket.timeout:
            break
        if not m or m.get("type") != "squawk":
            continue
        msg = m.get("message", {})
        if msg.get("seq") != seq:
            continue
        ok = (
            msg.get("from") == PROBE_FROM
            and msg.get("title") == PROBE_TITLE
            and msg.get("body") == PROBE_BODY
        )
        print(
            "frame: squawk exact=%s seq=%d from=%r title=%r"
            % (ok, seq, msg.get("from"), msg.get("title")),
            flush=True,
        )
        if ok:
            print("WS-VERIFY: PASS", flush=True)
            return 0
        print("WS-VERIFY: FAIL (content mismatch)", flush=True)
        return 1

    print("WS-VERIFY: FAIL (probe message never arrived)", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
