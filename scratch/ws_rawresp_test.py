import socket, ssl, os, base64, urllib.parse

proxy_url = os.environ["https_proxy"]
pu = urllib.parse.urlparse(proxy_url)
token = open(os.path.expanduser("~/hooks/state/squawk-ws.token")).read().strip()

def attempt(with_auth):
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
    h = ("GET /squawk-ws HTTP/1.1\r\nHost: github-mcp-host.tailc9ac71.ts.net\r\n"
         "Upgrade: websocket\r\nConnection: Upgrade\r\n"
         "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n" % key)
    if with_auth:
        h += "Authorization: Bearer %s\r\n" % token
    h += "\r\n"
    ts.sendall(h.encode())
    r = b""
    ts.settimeout(10)
    try:
        while True:
            chunk = ts.recv(4096)
            if not chunk:
                break
            r += chunk
            if b"\r\n\r\n" in r and b"101" not in r.split(b"\r\n")[0]:
                break
    except socket.timeout:
        pass
    print("=== with_auth=%s ===" % with_auth)
    print(r.decode("latin-1", "replace")[:800])
    ts.close()

attempt(False)
attempt(True)
