#!/usr/bin/env python3
"""E2E test for squawk-ws: auth rejection, backfill, live delivery."""
import asyncio
import inspect
import json
import os
import ssl
import sys

sys.path.insert(0, "/home/hatch/workspace/skills/.venv/lib/python3.12/site-packages")
import websockets

WS_URL = "wss://github-mcp-host.tailc9ac71.ts.net/squawk-ws"
TOKEN = open(os.path.expanduser("~/hooks/state/squawk-ws.token")).read().strip()
PROXY = os.environ.get("https_proxy")
SSL_CTX = ssl._create_unverified_context()


def kwargs(token=None):
    kw = dict(proxy=PROXY, ssl=SSL_CTX, open_timeout=25,
              ping_interval=20, ping_timeout=20, max_size=2 ** 20)
    if token:
        hdr = {"Authorization": "Bearer " + token}
        params = inspect.signature(websockets.connect).parameters
        if "additional_headers" in params:
            kw["additional_headers"] = hdr
        else:
            kw["extra_headers"] = hdr
    return kw


async def main():
    # 1. no token -> expect 401
    try:
        async with websockets.connect(WS_URL, **kwargs(None)) as ws:
            await ws.send(json.dumps({"subscribe": ["fleet"]}))
            print("FAIL: unauthenticated handshake accepted")
            return 1
    except Exception as e:
        s = str(e)
        if "401" in s:
            print("PASS: no-token handshake rejected (401)")
        else:
            print("FAIL: unexpected error without token: %.150s" % s)
            return 1

    # 2. with token -> subscribe, collect backfill
    async with websockets.connect(WS_URL, **kwargs(TOKEN)) as ws:
        print("PASS: authenticated wss handshake")
        await ws.send(json.dumps({"subscribe": ["fleet", "leads"]}))
        backfill = []
        try:
            while True:
                raw = await asyncio.wait_for(ws.recv(), timeout=6)
                backfill.append(json.loads(raw))
        except asyncio.TimeoutError:
            pass
        print("PASS: backfill received: %d messages" % len(backfill))
        for m in backfill:
            print("  seq=%d ch=%s from=%s sealed=%s text=%.60r" %
                  (m.get("seq"), m.get("channel"), m.get("sender"),
                   m.get("sealed"), m.get("text", "")))
        # 3. live delivery: wait for the test message (posted separately)
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=25)
            m = json.loads(raw)
            if "ws-e2e-probe" in m.get("text", ""):
                print("PASS: live delivery seq=%d ch=%s from=%s" %
                      (m.get("seq"), m.get("channel"), m.get("sender")))
                return 0
            print("FAIL: live message mismatch: %.120r" % m.get("text", ""))
            return 1
        except asyncio.TimeoutError:
            print("FAIL: no live message within 25s")
            return 1


sys.exit(asyncio.run(main()))
