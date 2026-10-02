import socket, ssl, os, base64, urllib.parse

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
print("CONNECT:", resp.split(b"\r\n")[0].decode())

ctx = ssl._create_unverified_context()
ts = ctx.wrap_socket(s, server_hostname="github-mcp-host.tailc9ac71.ts.net")

key = base64.b64encode(os.urandom(16)).decode()
req = (
    "GET /squawk-ws HTTP/1.1\r\n"
    "Host: github-mcp-host.tailc9ac71.ts.net\r\n"
    "Upgrade: websocket\r\n"
    "Connection: Upgrade\r\n"
    "Sec-WebSocket-Key: %s\r\n"
    "Sec-WebSocket-Version: 13\r\n"
    "Authorization: Bearer %s\r\n"
    "\r\n" % (key, token))
ts.sendall(req.encode())
r = ts.recv(4096).decode("latin-1", "replace")
print("GET response head:")
print(r.split("\r\n\r\n")[0])
ts.close()
