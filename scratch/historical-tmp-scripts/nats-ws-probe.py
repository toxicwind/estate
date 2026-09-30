"""Prove the browser NATS path: wss://<funnel>/nats-ws -> nats-server :4223.
Raw TLS + WebSocket handshake + minimal NATS protocol (INFO/CONNECT/SUB/MSG).
Run on yote.
"""
import base64, hashlib, json, os, socket, ssl, sys

HOST = "github-mcp-host.tailc9ac71.ts.net"
PORT = 443
PATH = "/nats-ws"

token = open("/home/toxic/.shingle/squawk-relay/feed-token").read().strip()

key = base64.b64encode(os.urandom(16)).decode()
req = (
    f"GET {PATH} HTTP/1.1\r\n"
    f"Host: {HOST}\r\n"
    "Upgrade: websocket\r\n"
    "Connection: Upgrade\r\n"
    f"Sec-WebSocket-Key: {key}\r\n"
    "Sec-WebSocket-Version: 13\r\n"
    "\r\n"
)

ctx = ssl.create_default_context()
raw = socket.create_connection((HOST, PORT), timeout=20)
tls = ctx.wrap_socket(raw, server_hostname=HOST)
tls.sendall(req.encode())

# read HTTP response headers
resp = b""
while b"\r\n\r\n" not in resp:
    chunk = tls.recv(4096)
    if not chunk:
        break
    resp += chunk
head = resp.split(b"\r\n\r\n", 1)[0].decode()
print("HTTP:", head.split("\r\n")[0])
assert "101" in head.split("\r\n")[0], f"no 101: {head[:200]}"
accept = [l for l in head.split("\r\n") if l.lower().startswith("sec-websocket-accept")]
print("WS upgrade accepted:", accept[0].split(": ", 1)[1][:20] + "...")


def ws_send(payload: bytes, opcode=0x1):
    hdr = bytes([0x80 | opcode])
    n = len(payload)
    if n < 126:
        hdr += bytes([0x80 | n])
    elif n < 65536:
        hdr += bytes([0x80 | 126]) + n.to_bytes(2, "big")
    else:
        hdr += bytes([0x80 | 127]) + n.to_bytes(8, "big")
    mask = os.urandom(4)
    hdr += mask
    tls.sendall(hdr + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))


def ws_recv():
    h = tls.recv(2)
    if len(h) < 2:
        return None, None
    op = h[0] & 0x0F
    ln = h[1] & 0x7F
    if ln == 126:
        ln = int.from_bytes(tls.recv(2), "big")
    elif ln == 127:
        ln = int.from_bytes(tls.recv(8), "big")
    data = b""
    while len(data) < ln:
        data += tls.recv(ln - len(data))
    return op, data


buf = b""
got_info = False
got_msg = False
tls.settimeout(15)
try:
    while not got_msg:
        op, data = ws_recv()
        if op is None:
            break
        if op == 0x8:
            print("WS close received")
            break
        if op == 0x9:  # ping -> pong
            ws_send(b"", opcode=0xA)
            continue
        buf += data
        while b"\r\n" in buf:
            ln, buf = buf.split(b"\r\n", 1)
            t = ln.decode()
            if t.startswith("INFO"):
                info = json.loads(t[4:])
                print("NATS INFO: version", info.get("version"), "auth_required", info.get("auth_required"))
                ws_send(('CONNECT {"verbose":false,"pedantic":false,"tls_required":false,'
                         f'"auth_token":"{token}","protocol":1,"echo":true,"name":"funnel-probe"}}'
                         ).encode() + b"\r\nSUB fleet.messages probe1\r\nPING\r\n")
                got_info = True
                # trigger a live message now that we're subscribed
                import subprocess
                probe = "funnel-ws-probe-live"
                subprocess.run(["/home/toxic/shingle/bin/squawk", "post", "fleet",
                                "--from", "taps", "--title", "taps-e2e",
                                "--body", probe],
                               capture_output=True, timeout=30)
                print("probe posted, waiting for it on the socket...")
            elif t == "PING":
                ws_send(b"PONG\r\n")
            elif t.startswith("MSG "):
                # payload is the next CRLF-terminated line
                if b"\r\n" not in buf:
                    buf = ln + b"\r\n" + buf
                    break
                payload, buf = buf.split(b"\r\n", 1)
                env = json.loads(payload.decode())
                print("MSG on fleet.messages: seq", env.get("seq"), "from", env.get("from"))
                got_msg = True
                break
            elif t.startswith("-ERR"):
                print("NATS -ERR:", t)
                sys.exit(1)
finally:
    tls.close()

assert got_info, "never got INFO"
print("wss:// funnel -> nats-ws -> NATS OK (live MSG received)" if got_msg
      else "connected + subscribed (no live traffic during window)")
