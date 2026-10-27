#!/usr/bin/env python3
"""chaos-ws-router — multiplexes :25204 entrypoint connections across lanes.

GREEN-BLUE: the real ws-exec daemon moved to :25214; this router owns :25204
(the address every existing caller/probe already knows) and sends each NEW
connection to a DIFFERENT route, round-robin, while logging the first
payload bytes from both sides. Zero-byte probes cost nothing (they FIN
instantly); any client that actually SPEAKS gets its route + payload logged,
which answers: are we receiving the full request, and on which lane?

Routes:
  real    -> 127.0.0.1:25214  (the actual awrawr-ws-exec; transparent)
  edge    -> 127.0.0.1:25217  (doorbell oauth-edge /exec-ws WS fast-lane)
  funnel  -> github-mcp-host:443 /exec-ws over TLS h1.1 with x-mcp-token
  honey   -> log-only black hole (client bytes logged, connection held)

Run: python3 chaos-ws-router.py  (owns 25204; real daemon must be on 25214)
"""
import asyncio, json, os, socket, ssl, time, uuid

LISTEN_PORT = 25204
REAL_PORT = 25214
EDGE_PORT = 25217
FUNNEL_HOST = "github-mcp-host.tailc9ac71.ts.net"
FUNNEL_PORT = 443
TOK = ""
for p in ("/home/toxic/.yote_connector_token", "/home/toxic/.shim_connector_token"):
    try:
        TOK = open(p).read().strip()
        break
    except OSError:
        pass

ROUTES = ["real", "edge", "funnel", "honey"]
LOG = "/tmp/chaos-ws-router.log"
_state = {"i": 0}


def log(msg):
    line = "%s %s" % (time.strftime("%H:%M:%S"), msg)
    with open(LOG, "a") as fh:
        fh.write(line + "\n")


def next_route():
    _state["i"] = (_state["i"] + 1) % len(ROUTES)
    return ROUTES[_state["i"]]


async def pipe(src, dst, tag, first_blob, blob_ref, limit=512):
    """Copy src->dst; capture first payload bytes once."""
    try:
        while True:
            data = await src.read(65536)
            if not data:
                break
            if first_blob[0] is None and data:
                first_blob[0] = data[:limit]
                blob_ref.set()
            dst.write(data)
            await dst.drain()
    except Exception:
        pass
    finally:
        try:
            dst.close()
        except Exception:
            pass


async def relay(creader, cwriter, route):
    cid = uuid.uuid4().hex[:8]
    peer = cwriter.get_extra_info("peername")
    blob = [None]
    blob_evt = asyncio.Event()
    log("CONN %s route=%s peer=%s" % (cid, route, peer))

    try:
        if route == "real":
            ur, uw = await asyncio.open_connection("127.0.0.1", REAL_PORT)
        elif route == "edge":
            req = ("GET /exec-ws HTTP/1.1\r\nHost: 127.0.0.1:%d\r\n"
                   "x-mcp-token: %s\r\nConnection: Upgrade\r\nUpgrade: websocket\r\n"
                   "Sec-WebSocket-Version: 13\r\nSec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n\r\n"
                   % (EDGE_PORT, TOK)).encode()
            ur, uw = await asyncio.open_connection("127.0.0.1", EDGE_PORT)
            uw.write(req)
            await uw.drain()
        elif route == "funnel":
            req = ("GET /exec-ws HTTP/1.1\r\nHost: %s\r\n"
                   "x-mcp-token: %s\r\nConnection: Upgrade\r\nUpgrade: websocket\r\n"
                   "Sec-WebSocket-Version: 13\r\nSec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n\r\n"
                   % (FUNNEL_HOST, TOK)).encode()
            ctx = ssl.create_default_context()
            ur, uw = await asyncio.open_connection(FUNNEL_HOST, FUNNEL_PORT, ssl=ctx, server_hostname=FUNNEL_HOST)
            uw.write(req)
            await uw.drain()
        else:  # honey
            await blob_evt.wait()
            log("HONEY %s first_payload=%r" % (cid, blob[0]))
            await asyncio.sleep(30)
            return

        # both directions, capture first bytes each way
        async def c2u():
            await pipe(creader, uw, cid, blob, blob_evt)
        async def u2c():
            ublob = [None]
            await pipe(ur, cwriter, cid, ublob, asyncio.Event())
        done = asyncio.gather(c2u(), u2c(), return_exceptions=True)
        # if the client spoke before routing completed (honey edge), record it
        try:
            await asyncio.wait_for(blob_evt.wait(), timeout=5)
            log("PAYLOAD %s route=%s client_first=%r" % (cid, route, blob[0]))
        except asyncio.TimeoutError:
            log("NOPAYLOAD %s route=%s (zero bytes within 5s)" % (cid, route))
        await done
        log("DONE %s route=%s" % (cid, route))
    except Exception as e:
        log("ERR %s route=%s %s" % (cid, route, e))


async def main():
    srv = await asyncio.start_server(handler, "0.0.0.0", LISTEN_PORT)
    log("chaos-ws-router listening on :%d routes=%s real=%d" % (LISTEN_PORT, ROUTES, REAL_PORT))
    async with srv:
        await srv.serve_forever()


async def handler(creader, cwriter):
    route = next_route()
    await relay(creader, cwriter, route)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
