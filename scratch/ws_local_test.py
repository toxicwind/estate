import socket, ssl, base64, os, hashlib

# raw HTTP upgrade test against the LOCAL server (bypasses funnel)
token = open('/home/toxic/squawk-ws/token').read().strip()
print('token len:', len(token))

key = base64.b64encode(os.urandom(16)).decode()
req = (
    "GET /squawk-ws HTTP/1.1\r\n"
    "Host: 127.0.0.1:25147\r\n"
    "Upgrade: websocket\r\n"
    "Connection: Upgrade\r\n"
    "Sec-WebSocket-Key: %s\r\n"
    "Sec-WebSocket-Version: 13\r\n"
    "Authorization: Bearer %s\r\n"
    "\r\n" % (key, token)
)
s = socket.create_connection(('127.0.0.1', 25147), timeout=10)
s.sendall(req.encode())
resp = s.recv(4096).decode('latin-1', 'replace')
print('LOCAL handshake response:')
print(resp.split('\r\n\r\n')[0])
s.close()
