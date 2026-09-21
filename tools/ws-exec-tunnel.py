#!/usr/bin/env python3
"""tunnel_asyncio.py (candidate A): stdlib-asyncio TCP forwarder.

Listens on 127.0.0.1:25379, forwards every byte both ways to 127.0.0.1:25204.
Fully transparent to the WS protocol (handshake + frames pass through untouched).
"""
import asyncio
import os
import sys

LISTEN_PORT = int(os.environ.get("TUNNEL_LISTEN_PORT", "25379"))
TARGET_HOST = os.environ.get("TUNNEL_TARGET_HOST", "127.0.0.1")
TARGET_PORT = int(os.environ.get("TUNNEL_TARGET_PORT", "25204"))


async def pipe(reader, writer):
    try:
        while True:
            data = await reader.read(65536)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except (ConnectionResetError, BrokenPipeError, asyncio.IncompleteReadError):
        pass
    finally:
        try:
            writer.close()
        except Exception:
            pass


async def handle(client_r, client_w):
    try:
        target_r, target_w = await asyncio.open_connection(TARGET_HOST, TARGET_PORT)
    except OSError:
        try:
            client_w.close()
        except Exception:
            pass
        return
    await asyncio.gather(pipe(client_r, target_w), pipe(target_r, client_w))


async def main():
    server = await asyncio.start_server(handle, "127.0.0.1", LISTEN_PORT)
    print("[tunnel] listening 127.0.0.1:%d -> %s:%d" % (LISTEN_PORT, TARGET_HOST, TARGET_PORT), flush=True)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
