import socket, ssl, os, base64, urllib.parse, struct, json, hashlib

proxy_url = os.environ["https_proxy"]
pu = urllib.parse.urlparse(proxy_url)
token = open(os.path.expanduser("~/hooks/state/squawk-ws.token")).read().strip()

s = socket.create_connection((pu.hostname, pu.port), timeout=15)
creds = base64.b64encode(("%s:%s" % (pu.username, pu.password)).encode()).decode()
s.sendall(("CONNECT github-mcp-host.tailc9ac71.ts.net:443 HTTP/1.1\r\n"
           "Host: github-mcp-host.tailc9ac71.ts.net:443\r\n"
           "Proxy-Authorization: Basic %s\r\n\r\n" % creds).encode())
resp = b""
while b"\r\n\r\n" not in resp:
    resp += s.recv(4096)
ctx = ssl._create_unverified_context()
ts = ctx.wrap_socket(s, server_hostname="github-mcp-host.tailc9ac71.ts.net")
key = base64.b64encode(os.urandom(16)).decode()
ts.sendall(("GET /squawk-ws HTTP/1.1\r\nHost: github-mcp-host.tailc9ac71.ts.net\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n"
            "Authorization: Bearer %s\r\n\r\n" % (key, token)).encode())
r = b""
while b"\r\n\r\n" not in r:
    r += ts.recv(4096)
print("handshake:", r.split(b"\r\n")[0].decode())

def send_text(ts, payload: bytes):
    mask = os.urandom(4)
    hdr = bytes([0x81, 0x80 | len(payload)]) + mask
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    ts.sendall(hdr + masked)

def recv_frame(ts):
    ts.settimeout(12)
    h = ts.recv(2)
    if len(h) < 2:
        return ("CLOSED/EOF", b"")
    b1, b2 = h
    ln = b2 & 0x7F
    if ln == 126:
        ln = struct.unpack(">H", ts.recv(2))[0]
    elif ln == 127:
        ln = struct.unpack(">Q", ts.recv(8))[0]
    data = b""
    while len(data) < ln:
        chunk = ts.recv(ln - len(data))
        if not chunk:
            break
        data += chunk
    return (b1 & 0x0F, data)

send_text(ts, json.dumps({"subscribe": ["fleet"]}).encode())
for _ in range(3):
    try:
        op, data = recv_frame(ts)
        print("frame op=%s len=%d head=%.120s" % (op, len(data), data[:120]))
        if op == 1 and b"history_end" in data:
            break
    except Exception as e:
        print("recv error:", e)
        break
ts.close()
