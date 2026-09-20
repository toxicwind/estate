import asyncio, inspect, json, os, ssl, sys

sys.path.insert(0, "/home/hatch/workspace/skills/.venv/lib/python3.12/site-packages")
import websockets

CAPTURED = []

async def fake_server(reader, writer):
    try:
        data = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), timeout=10)
    except Exception as e:
        data = b"<read error: %s>" % str(e).encode()
    CAPTURED.append(data)
    # respond 101 so the client proceeds
    key = None
    for ln in data.decode("latin-1", "replace").split("\r\n"):
        if ln.lower().startswith("sec-websocket-key:"):
            key = ln.split(":", 1)[1].strip()
    import hashlib, base64
    accept = base64.b64encode(hashlib.sha1(
        (key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
    writer.write(("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\n"
                  "Connection: Upgrade\r\nSec-WebSocket-Accept: %s\r\n\r\n" % accept).encode())
    await writer.drain()
    await asyncio.sleep(1)
    writer.close()

async def main():
    # self-signed cert for the fake server
    os.system("openssl req -x509 -newkey rsa:2048 -keyout /tmp/fakews.key -out /tmp/fakews.crt "
              "-days 1 -nodes -subj /CN=localhost 2>/dev/null")
    sctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    sctx.load_cert_chain("/tmp/fakews.crt", "/tmp/fakews.key")
    server = await asyncio.start_server(fake_server, "127.0.0.1", 18923, ssl=sctx)

    token = open(os.path.expanduser("~/hooks/state/squawk-ws.token")).read().strip()
    cctx = ssl._create_unverified_context()
    kw = dict(proxy=None, ssl=cctx, open_timeout=10)
    params = inspect.signature(websockets.connect).parameters
    hdr = {"Authorization": "Bearer " + token}
    if "additional_headers" in params:
        kw["additional_headers"] = hdr
    else:
        kw["extra_headers"] = hdr
    try:
        async with websockets.connect("wss://127.0.0.1:18923/squawk-ws", **kw) as ws:
            await ws.send(json.dumps({"subscribe": ["fleet"]}))
            print("client: connected ok")
    except Exception as e:
        print("client error: %.150s" % e)
    server.close()
    print("=== bytes the client actually sent ===")
    print(CAPTURED[0].decode("latin-1", "replace") if CAPTURED else "NOTHING CAPTURED")

asyncio.run(main())
