#!/usr/bin/env python3
"""ws_daemon.py — persistent local daemon holding ONE websocket connection to
the awrawr-pc exec bridge (wss://.../exec-ws), multiplexing local commands.

Borrowed framing/handshake pattern from squawk-ws (stdlib-only asyncio).

Local protocol: Unix socket ~/.cache/awrawr-ws-bridge.sock, newline JSON:
  client -> {"cmd": "...", "workdir": "..."}
  daemon -> {"type":"chunk","stream":"stdout"|"stderr","data":"..."}  (streamed)
  daemon -> {"type":"done","code":N,"truncated":bool}
  daemon -> {"type":"error","message":"..."}   (bridge down; caller falls back)

The daemon re-fetches the auth surrogate on every (re)connect. If the bridge
is unreachable it keeps retrying with backoff and fails local requests fast
so callers can fall back to the HTTPS path.
"""
import asyncio
import base64
import hashlib
import json
import os
import secrets
import socket
import ssl
import sys
import time
import urllib.parse

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(SKILL_DIR, "..", "skill-creator", "bin"))
sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import dynamic_credential_entry  # noqa: E402

CRED = "custom.awrawr-mcp"
HOSTS = {"github-mcp-host.tailc9ac71.ts.net"}
WS_HOST = "github-mcp-host.tailc9ac71.ts.net"
WS_PATH = "/exec-ws"
from wsframe import WS_GUID, read_frame, send_frame  # noqa: E402

CACHE = os.path.expanduser("~/.cache")
SOCK_PATH = os.path.join(CACHE, "awrawr-ws-bridge.sock")
LOG_PATH = os.path.join(CACHE, "awrawr-ws-bridge.log")
PING_INTERVAL = 25


def log(*a):
    line = "[ws-daemon %s] %s\n" % (
        time.strftime("%H:%M:%S"), " ".join(str(x) for x in a))
    try:
        with open(LOG_PATH, "a") as f:
            f.write(line)
    except OSError:
        pass


# --- websocket framing lives in wsframe.py (shared with xfer.py) -----------
# (read_frame / send_frame imported above)


def proxy_target():
    for k in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
        v = os.environ.get(k, "")
        if v:
            u = urllib.parse.urlparse(v)
            return u.hostname, u.port or 8080
    raise RuntimeError("no proxy configured")


class Bridge:
    """Owns the single WS connection; multiplexes commands by id."""

    def __init__(self):
        self.reader = None
        self.writer = None
        self.send_lock = asyncio.Lock()
        self.pending = {}  # id -> asyncio.Queue
        self.connected = asyncio.Event()
        self._reader_task = None

    def _surrogate(self):
        host = WS_HOST.lower()
        if host not in HOSTS:
            raise RuntimeError("host not allowlisted: " + host)
        entry = dynamic_credential_entry(CRED)
        placement = entry.get("placement") or {}
        header = placement.get("custom_header", "X-MCP-Token")
        return header, str(entry["surrogate"]).strip()

    async def _connect_once(self):
        header_name, surrogate = await asyncio.to_thread(self._surrogate)
        phost, pport = proxy_target()
        raw = socket.create_connection((phost, pport), timeout=15)
        try:
            raw.sendall(("CONNECT %s:443 HTTP/1.1\r\nHost: %s:443\r\n\r\n"
                         % (WS_HOST, WS_HOST)).encode())
            resp = b""
            while b"\r\n\r\n" not in resp:
                blk = raw.recv(4096)
                if not blk:
                    break
                resp += blk
            if b" 200" not in resp.split(b"\r\n", 1)[0]:
                raise RuntimeError(
                    "proxy CONNECT failed: " +
                    resp.split(b"\r\n", 1)[0][:60].decode("latin-1"))
            ctx = ssl.create_default_context()
            reader, writer = await asyncio.open_connection(
                sock=raw, ssl=ctx, server_hostname=WS_HOST)
        except Exception:
            raw.close()
            raise
        key = base64.b64encode(secrets.token_bytes(16)).decode()
        writer.write((
            "GET %s HTTP/1.1\r\nHost: %s\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n"
            "%s: %s\r\n\r\n" % (WS_PATH, WS_HOST, key, header_name, surrogate)
        ).encode())
        await writer.drain()
        hs = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), 15)
        if b"101" not in hs.split(b"\r\n", 1)[0]:
            writer.close()
            raise RuntimeError("ws handshake failed: " +
                               hs.split(b"\r\n", 1)[0][:60].decode("latin-1"))
        return reader, writer

    async def _reader_loop(self):
        try:
            while True:
                fin, opcode, payload = await read_frame(self.reader)
                if opcode == 0x8:
                    break
                if opcode == 0x9:  # ping -> pong
                    async with self.send_lock:
                        await send_frame(self.writer, 0xA, payload)
                    continue
                if opcode != 0x1:
                    continue
                try:
                    doc = json.loads(payload.decode("utf-8", "replace"))
                except ValueError:
                    continue
                q = self.pending.get(str(doc.get("id", "")))
                if q is not None:
                    q.put_nowait(doc)
        except (asyncio.IncompleteReadError, ConnectionResetError,
                BrokenPipeError, asyncio.TimeoutError):
            pass
        finally:
            self.connected.clear()

    async def maintain(self):
        backoff = 1.0
        while True:
            try:
                reader, writer = await self._connect_once()
                self.reader, self.writer = reader, writer
                self._reader_task = asyncio.create_task(self._reader_loop())
                self.connected.set()
                log("bridge connected")
                backoff = 1.0
                await self._reader_task  # ends when connection drops
                log("bridge disconnected, reconnecting")
            except Exception as e:
                log("connect failed:", str(e)[:120])
            self.connected.clear()
            # fail fast: tell waiters the bridge is down
            for q in list(self.pending.values()):
                q.put_nowait({"type": "error",
                              "message": "bridge reconnecting"})
            self.pending.clear()
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30)

    async def pinger(self):
        while True:
            await asyncio.sleep(PING_INTERVAL)
            if self.connected.is_set():
                try:
                    async with self.send_lock:
                        await send_frame(self.writer, 0x9, b"ws-daemon")
                except OSError:
                    pass

    async def run_command(self, cmd_id, cmd, workdir, argv=None,
                          timeout=None):
        """Async generator of response docs for one command."""
        q = asyncio.Queue()
        self.pending[cmd_id] = q
        try:
            await self.connected.wait()
            frame = {"id": cmd_id, "workdir": workdir or "/home/toxic"}
            if argv is not None:
                frame["argv"] = argv
            else:
                frame["cmd"] = cmd
            if timeout is not None:
                frame["timeout"] = timeout
            async with self.send_lock:
                await send_frame(self.writer, 0x1,
                                 json.dumps(frame).encode())
            # Silent stretches (quiet long commands) must survive up to the
            # requested command timeout; the per-doc ceiling derives from it.
            doc_ceiling = max(150, (timeout or 0) + 60)
            while True:
                doc = await asyncio.wait_for(q.get(), doc_ceiling)
                yield doc
                if doc.get("type") in ("done", "error", "denied"):
                    return
        finally:
            self.pending.pop(cmd_id, None)


async def handle_local(reader, writer, bridge):
    try:
        raw = await asyncio.wait_for(reader.readline(), 10)
        if not raw:
            return
        try:
            req = json.loads(raw.decode())
        except ValueError:
            return
        cmd = req.get("cmd", "")
        argv = req.get("argv")
        timeout = req.get("timeout")
        workdir = req.get("workdir", "/home/toxic")
        if not bridge.connected.is_set():
            writer.write((json.dumps(
                {"type": "error",
                 "message": "bridge not connected"}) + "\n").encode())
            await writer.drain()
            return
        cmd_id = secrets.token_hex(8)
        async for doc in bridge.run_command(cmd_id, cmd, workdir, argv,
                                            timeout):
            t = doc.get("type")
            if t == "chunk":
                out = {"type": "chunk", "stream": doc.get("stream"),
                       "data": doc.get("data", "")}
            elif t == "denied":
                out = {"type": "done", "code": 126,
                       "error": "POLICY DENIED: " + str(doc.get("reason", ""))}
            elif t == "exit":
                out = {"type": "done", "code": doc.get("code", -1),
                       "truncated": doc.get("truncated", False)}
                if doc.get("error"):
                    out["error"] = doc["error"]
            else:  # error
                out = {"type": "error",
                       "message": str(doc.get("message", "bridge error"))}
                writer.write((json.dumps(out) + "\n").encode())
                await writer.drain()
                return
            writer.write((json.dumps(out) + "\n").encode())
            await writer.drain()
            if out["type"] == "done":
                return
    except (asyncio.TimeoutError, ConnectionResetError, BrokenPipeError):
        pass
    finally:
        try:
            writer.close()
        except Exception:
            pass


async def main():
    os.makedirs(CACHE, exist_ok=True)
    try:
        os.unlink(SOCK_PATH)
    except OSError:
        pass
    bridge = Bridge()
    asyncio.create_task(bridge.maintain())
    asyncio.create_task(bridge.pinger())

    async def on_client(r, w):
        await handle_local(r, w, bridge)

    server = await asyncio.start_unix_server(on_client, path=SOCK_PATH)
    os.chmod(SOCK_PATH, 0o600)
    log("listening on", SOCK_PATH)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
