#!/usr/bin/env python3
"""awrawr-ws-exec: persistent websocket exec bridge for awrawr-pc.

Borrowed pattern: /home/toxic/squawk-ws/squawk_ws_server.py (stdlib-only
asyncio websocket: raw HTTP Upgrade handshake + minimal framing). No new
dependencies — runs on system python3... except it reuses the command
policy and audit log from awrawr_mcp, so it runs under the same venv.

Security layers (same as the HTTPS bridge):
 1. Tailscale funnel: TLS, outbound-only (route /exec-ws -> 127.0.0.1:8379).
 2. X-MCP-Token checked per handshake against ~/.awrawr_mcp_token (else 401).
    Token file is re-read on EVERY handshake so rotation needs no restart.
 3. Command policy + audit: imported from awrawr_mcp (single policy/audit impl).
 4. Limits: 90 s default timeout, 200000-char total output cap, same as exec().

Protocol (JSON text messages, multiplexed by client-chosen "id"):
  C->S  {"id": "<id>", "cmd": "...", "workdir": "/home/toxic",
         "timeout": 120}                       # timeout optional, cap 1800s
  C->S  {"id": "<id>", "argv": ["printf","%s","a`b"], "workdir": "..."}
                                               # shell-free exec, no quoting
  S->C  {"id": "<id>", "type": "chunk", "stream": "stdout"|"stderr", "data": "..."}
  S->C  {"id": "<id>", "type": "denied", "reason": "..."}
  S->C  {"id": "<id>", "type": "exit", "code": N, "truncated": bool}

File transfer ops (binary-safe, resumable, no shell, no 90s ceiling):
  # upload cell -> awrawr-pc
  C->S  {"id": "<id>", "op": "put", "path": "/home/toxic/x.bin",
         "size": 12345, "sha256": "<hex>", "mode": "0644"}
  S->C  {"id": "<id>", "type": "put-ready", "offset": K}   # resume offset
  C->S  binary frames (opcode 0x2) with raw bytes
  C->S  {"id": "<id>", "op": "put-end"}
  S->C  {"id": "<id>", "type": "put-done", "path": "...", "size": N}
  S->C  {"id": "<id>", "type": "put-error", "message": "..."}
  # download awrawr-pc -> cell
  C->S  {"id": "<id>", "op": "get", "path": "/home/toxic/x.bin"}
  S->C  {"id": "<id>", "type": "get-meta", "size": N, "sha256": "<hex>"}
  S->C  binary frames with raw bytes
  S->C  {"id": "<id>", "type": "get-done", "path": "...", "size": N}
  S->C  {"id": "<id>", "type": "get-error", "message": "..."}
  Either side may send WS ping/pong frames (answered at frame level).
  Transfers are processed inline per connection (one op per connection);
  idle 120s without a frame aborts, total cap 3600s.

Managed by pitchfork as daemon `awrawr-ws-exec` (see sovereign/pitchfork.toml).
Tracked copy: sovereign/bridge/awrawr_ws_exec.py (sovereign-projects).
"""
import asyncio
import base64
import hashlib
import hmac
import json
import os
import shlex
import shutil
import signal
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.expanduser("~"))
from awrawr_mcp import _policy_check, _audit  # noqa: E402  (single policy/audit impl)

WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
WS_PATH = "/exec-ws"
PORT = int(os.environ.get("WS_EXEC_PORT", "8379"))
TOKEN_FILE = os.path.expanduser("~/.awrawr_mcp_token")
MAX_OUT = 200000
TIMEOUT_S = 90
MAX_TIMEOUT_S = 1800
XFER_IDLE_S = 120
XFER_TOTAL_S = 3600
XFER_CHUNK = 262144
XFER_MAX_FRAME = 4 * 1024 * 1024
# Command-path frames larger than this are rejected and the connection closed.
# Xfer chunks are 256 KiB, well under this cap.
CMD_MAX_FRAME = 16 * 1024 * 1024
XFER_ROOTS = ("/home/toxic", "/tmp")
_ACTIVE_PUTS = set()  # paths with a live put op; second put -> clean "busy"
_ACTIVE_PUTS_LOCK = asyncio.Lock()


def log(*a):
    print("[ws-exec]", *a, flush=True)


def read_token():
    try:
        with open(TOKEN_FILE) as f:
            return f.read().strip()
    except OSError:
        return ""


# --- websocket framing (borrowed from squawk-ws) ---------------------------
async def read_frame(reader):
    hdr = await reader.readexactly(2)
    fin = bool(hdr[0] & 0x80)
    opcode = hdr[0] & 0x0F
    masked = bool(hdr[1] & 0x80)
    length = hdr[1] & 0x7F
    if length == 126:
        length = int.from_bytes(await reader.readexactly(2), "big")
    elif length == 127:
        length = int.from_bytes(await reader.readexactly(8), "big")
    mask = await reader.readexactly(4) if masked else None
    if length > CMD_MAX_FRAME:
        # Killer-feature hardening: never buffer an unbounded command-path
        # frame. Callers treat this as fatal and close the connection.
        raise ValueError("frame too large: %d > %d" % (length, CMD_MAX_FRAME))
    payload = await reader.readexactly(length) if length else b""
    if mask:
        payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    return fin, opcode, payload


async def send_frame(writer, opcode, payload=b""):
    hdr = bytes([0x80 | opcode])
    n = len(payload)
    if n < 126:
        hdr += bytes([n])
    elif n < 65536:
        hdr += bytes([126]) + n.to_bytes(2, "big")
    else:
        hdr += bytes([127]) + n.to_bytes(8, "big")
    writer.write(hdr + payload)
    await writer.drain()


async def read_message(reader, writer, send_lock, timeout=120):
    """One complete WS message. Returns (is_text, bytes), or None on close."""
    buf = bytearray()
    is_text = True
    while True:
        fin, opcode, payload = await asyncio.wait_for(read_frame(reader),
                                                      timeout)
        if opcode == 0x8:  # close
            return None
        if opcode == 0x9:  # ping -> pong
            try:
                async with send_lock:
                    await send_frame(writer, 0xA, payload)
            except OSError:
                return None
            continue
        if opcode in (0x1, 0x2):
            is_text = (opcode == 0x1)
            buf = bytearray(payload)
        elif opcode == 0x0:
            buf += payload
        else:
            continue
        if fin:
            return (is_text, bytes(buf))


async def read_text_message(reader, writer, send_lock, timeout=120):
    """Assemble one complete text message, answering pings. None on close."""
    msg = await read_message(reader, writer, send_lock, timeout)
    if msg is None:
        return None
    is_text, payload = msg
    if not is_text:
        return ""  # binary outside a transfer: ignore
    return payload.decode("utf-8", "replace")


async def send_json(writer, send_lock, doc):
    async with send_lock:
        await send_frame(writer, 0x1, json.dumps(doc).encode("utf-8"))


async def send_binary(writer, send_lock, data):
    async with send_lock:
        await send_frame(writer, 0x2, data)


# --- transfer path policy ---------------------------------------------------
def _xfer_path(path):
    """Resolve a transfer path; must stay inside XFER_ROOTS.

    realpath (not abspath): a symlink planted under /home/toxic that
    points outside must not escape the permitted roots.
    """
    p = os.path.expanduser(path or "")
    if not p:
        return None, "empty path"
    ap = os.path.abspath(p)
    # resolve symlinks; for a not-yet-existing put destination, resolve
    # the parent dir and re-append the leaf name
    if os.path.lexists(ap):
        rp = os.path.realpath(ap)
    else:
        parent = os.path.dirname(ap) or os.sep
        rp = os.path.join(os.path.realpath(parent), os.path.basename(ap))
    for r in XFER_ROOTS:
        rr = os.path.realpath(r)
        if rp == rr or rp.startswith(rr + os.sep):
            return rp, None
    return None, "path escapes /home/toxic and /tmp: %s" % rp


# --- command execution ------------------------------------------------------
# The daemon is usually started by a supervisor (pitchfork) whose inherited
# PATH can contain unexpanded shell placeholders (e.g. fish's literal
# "%h/.local/bin") — a bare argv[0] then fails lookup with
# "[Errno 2] No such file or directory: 'git'". _spawn_env() rebuilds a
# sane PATH once per spawn: drop unexpanded placeholders, expand "~",
# keep the core dirs, dedupe. argv[0] is resolved up front with
# shutil.which so a missing executable fails with a clear message
# instead of an opaque -2.
_CORE_PATH_DIRS = ("/usr/local/sbin", "/usr/local/bin", "/usr/sbin",
                   "/usr/bin", "/sbin", "/bin")


def _spawn_env():
    raw = os.environ.get("PATH", "") or ""
    seen, parts = set(), []
    for seg in raw.split(os.pathsep):
        seg = seg.strip()
        if not seg or "%" in seg:  # unexpanded placeholder, unusable
            continue
        seg = os.path.expanduser(seg)
        if seg and seg not in seen:
            seen.add(seg)
            parts.append(seg)
    for d in _CORE_PATH_DIRS:
        if d not in seen:
            seen.add(d)
            parts.append(d)
    env = dict(os.environ)
    env["PATH"] = os.pathsep.join(parts)
    return env


def _kill_tree(proc):
    """SIGKILL the child's whole process group, then the child itself.

    Children are spawned with start_new_session=True, so the group contains
    only this command's subtree (shell wrappers and their children included).
    """
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        pass
    try:
        proc.kill()
    except ProcessLookupError:
        pass


async def run_command(writer, send_lock, msg_id, cmd, workdir,
                      argv=None, timeout=TIMEOUT_S):
    t0 = time.monotonic()
    env = _spawn_env()
    exe = None
    if argv is not None:
        # shell-free exec: no quoting, no substitution, ever
        display = shlex.join([str(a) for a in argv])[:500]
        orig_cmd = "argv: " + display
        yolo = False
        denied = _policy_check(display)
        use_shell = False
        base = {"cmd": orig_cmd[:500], "workdir": workdir, "yolo": yolo,
                "transport": "ws", "msg_id": msg_id}
        first = str(argv[0]) if argv else ""
        if "/" not in first:
            exe = shutil.which(first, path=env["PATH"])
            if exe is None:
                reason = ("executable not found: %r (PATH=%s)"
                          % (first, env["PATH"]))
                _audit(**base, status="error", reason=reason[:200],
                       elapsed_ms=int((time.monotonic() - t0) * 1000))
                await send_json(writer, send_lock,
                                {"id": msg_id, "type": "exit", "code": -2,
                                 "error": reason[:200]})
                return
    else:
        orig_cmd = cmd
        yolo = cmd.startswith("#yolo ")
        if yolo:
            cmd = cmd[len("#yolo "):].lstrip()
        denied = None if yolo else _policy_check(cmd)
        use_shell = True
        base = {"cmd": orig_cmd[:500], "workdir": workdir, "yolo": yolo,
                "transport": "ws", "msg_id": msg_id}

    if denied:
        _audit(**base, status="denied", reason=denied,
               elapsed_ms=int((time.monotonic() - t0) * 1000))
        await send_json(writer, send_lock,
                        {"id": msg_id, "type": "denied", "reason": denied})
        return

    async def pump(stream, proc, kind, state):
        while True:
            chunk = await stream.read(65536)
            if not chunk:
                return
            text = chunk.decode("utf-8", "replace")
            if state["total"] < MAX_OUT:
                room = MAX_OUT - state["total"]
                send_text = text[:room]
                state["total"] += len(send_text)
                if len(text) > room:
                    state["truncated"] = True
                await send_json(writer, send_lock, {
                    "id": msg_id, "type": "chunk",
                    "stream": kind, "data": send_text})
            else:
                state["truncated"] = True

    try:
        if use_shell:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workdir or "/home/toxic",
                env=env,
                start_new_session=True,  # own process group: _kill_tree reaps all
            )
        else:
            resolved = [exe] + [str(a) for a in argv[1:]] \
                if exe else [str(a) for a in argv]
            proc = await asyncio.create_subprocess_exec(
                *resolved,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workdir or "/home/toxic",
                env=env,
                start_new_session=True,
            )
        state = {"total": 0, "truncated": False}
        try:
            await asyncio.wait_for(asyncio.gather(
                pump(proc.stdout, proc, "stdout", state),
                pump(proc.stderr, proc, "stderr", state),
                proc.wait(),
            ), timeout=timeout)
            code = proc.returncode
            status, extra = "ok", {}
        except asyncio.TimeoutError:
            _kill_tree(proc)
            code, status = -1, "timeout"
            extra = {"reason": "TIMEOUT after %ds" % timeout}
            await send_json(writer, send_lock, {
                "id": msg_id, "type": "chunk", "stream": "stderr",
                "data": "TIMEOUT after %ds" % timeout})
        except asyncio.CancelledError:
            # Disconnect mid-command: kill the whole tree or it leaks on the box.
            _kill_tree(proc)
            raise
        _audit(**base, status=status, exit=code, out_chars=state["total"],
               truncated=state["truncated"],
               elapsed_ms=int((time.monotonic() - t0) * 1000), **extra)
        await send_json(writer, send_lock, {
            "id": msg_id, "type": "exit", "code": code,
            "truncated": state["truncated"]})
    except Exception as e:
        _audit(**base, status="error", reason=str(e)[:200],
               elapsed_ms=int((time.monotonic() - t0) * 1000))
        await send_json(writer, send_lock,
                        {"id": msg_id, "type": "exit", "code": -2,
                         "error": str(e)[:200]})


# --- file transfer ops ------------------------------------------------------
async def _handle_put(reader, writer, send_lock, msg_id, doc):
    t0 = time.monotonic()
    path, err = _xfer_path(doc.get("path"))
    size = doc.get("size")
    sha256 = str(doc.get("sha256") or "")
    mode = doc.get("mode")
    base = {"cmd": "put %s" % (path or doc.get("path")),
            "workdir": "/home/toxic", "yolo": False,
            "transport": "ws", "msg_id": msg_id}

    async def fail(reason):
        _audit(**base, status="put-error", reason=reason[:200],
               elapsed_ms=int((time.monotonic() - t0) * 1000))
        await send_json(writer, send_lock,
                        {"id": msg_id, "type": "put-error",
                         "message": reason[:300]})

    if err:
        await fail(err)
        return
    if not isinstance(size, int) or size < 0 or len(sha256) != 64:
        await fail("bad size/sha256")
        return
    # one live put per path: a second concurrent put gets a clean "busy"
    # instead of two writers interleaving into the same .part file
    async with _ACTIVE_PUTS_LOCK:
        if path in _ACTIVE_PUTS:
            await fail("transfer busy: another put to this path is active")
            return
        _ACTIVE_PUTS.add(path)
    try:
        await _put_body(reader, writer, send_lock, msg_id, doc, path,
                        size, sha256, mode, base, t0, fail)
    finally:
        async with _ACTIVE_PUTS_LOCK:
            _ACTIVE_PUTS.discard(path)


async def _put_body(reader, writer, send_lock, msg_id, doc, path,
                    size, sha256, mode, base, t0, fail):
    part = path + ".part"
    try:
        os.makedirs(os.path.dirname(path) or "/", exist_ok=True)
    except OSError as e:
        await fail("mkdir: %s" % e)
        return
    # resume: existing .part tail continues the upload
    offset = 0
    try:
        if os.path.exists(part):
            offset = os.path.getsize(part)
            if offset > size:
                os.unlink(part)
                offset = 0
    except OSError as e:
        await fail("stat .part: %s" % e)
        return
    await send_json(writer, send_lock,
                    {"id": msg_id, "type": "put-ready", "offset": offset})
    received = offset
    try:
        f = open(part, "ab")
    except OSError as e:
        await fail("open .part: %s" % e)
        return
    try:
        with f:
            while True:
                try:
                    msg = await read_message(reader, writer, send_lock,
                                             timeout=XFER_IDLE_S)
                except asyncio.TimeoutError:
                    await fail("idle timeout: no frame for %ds" % XFER_IDLE_S)
                    return
                if msg is None:
                    await fail("connection closed mid-transfer")
                    return
                is_text, payload = msg
                if is_text:
                    try:
                        end = json.loads(payload.decode("utf-8", "replace"))
                    except ValueError:
                        continue
                    if end.get("op") == "put-end" and \
                            str(end.get("id")) == msg_id:
                        break
                    continue
                if len(payload) > XFER_MAX_FRAME:
                    await fail("frame too large")
                    return
                f.write(payload)
                received += len(payload)
                if received > size:
                    await fail("overrun: more bytes than declared size")
                    return
    except OSError as e:
        await fail("write: %s" % e)
        return
    if received != size:
        await fail("short transfer: got %d of %d bytes" % (received, size))
        return
    # verify + atomic install
    h = hashlib.sha256()
    try:
        with open(part, "rb") as f:
            while True:
                blk = f.read(1048576)
                if not blk:
                    break
                h.update(blk)
    except OSError as e:
        await fail("verify read: %s" % e)
        return
    if h.hexdigest() != sha256.lower():
        try:
            os.unlink(part)
        except OSError:
            pass
        await fail("sha256 mismatch: transfer corrupt, .part removed")
        return
    try:
        if mode:
            os.chmod(part, int(str(mode), 8))
        os.replace(part, path)
    except (OSError, ValueError) as e:
        await fail("install: %s" % e)
        return
    _audit(**base, status="put-ok", size=size, sha256=sha256,
           elapsed_ms=int((time.monotonic() - t0) * 1000))
    await send_json(writer, send_lock,
                    {"id": msg_id, "type": "put-done",
                     "path": path, "size": size})


async def _handle_get(reader, writer, send_lock, msg_id, doc):
    t0 = time.monotonic()
    path, err = _xfer_path(doc.get("path"))
    base = {"cmd": "get %s" % (path or doc.get("path")),
            "workdir": "/home/toxic", "yolo": False,
            "transport": "ws", "msg_id": msg_id}

    async def fail(reason):
        _audit(**base, status="get-error", reason=reason[:200],
               elapsed_ms=int((time.monotonic() - t0) * 1000))
        await send_json(writer, send_lock,
                        {"id": msg_id, "type": "get-error",
                         "message": reason[:300]})

    if err:
        await fail(err)
        return
    try:
        size = os.path.getsize(path)
    except OSError as e:
        await fail("stat: %s" % e)
        return
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while True:
                blk = f.read(1048576)
                if not blk:
                    break
                h.update(blk)
    except OSError as e:
        await fail("hash: %s" % e)
        return
    await send_json(writer, send_lock,
                    {"id": msg_id, "type": "get-meta",
                     "size": size, "sha256": h.hexdigest()})
    try:
        with open(path, "rb") as f:
            while True:
                blk = f.read(XFER_CHUNK)
                if not blk:
                    break
                await send_binary(writer, send_lock, blk)
    except OSError as e:
        await fail("send: %s" % e)
        return
    _audit(**base, status="get-ok", size=size,
           elapsed_ms=int((time.monotonic() - t0) * 1000))
    await send_json(writer, send_lock,
                    {"id": msg_id, "type": "get-done",
                     "path": path, "size": size})


async def handle_transfer(reader, writer, send_lock, doc):
    """Inline per-connection transfer op (one op per connection)."""
    msg_id = str(doc.get("id"))
    op = doc.get("op")
    try:
        if op == "put":
            await asyncio.wait_for(
                _handle_put(reader, writer, send_lock, msg_id, doc),
                timeout=XFER_TOTAL_S)
        elif op == "get":
            await asyncio.wait_for(
                _handle_get(reader, writer, send_lock, msg_id, doc),
                timeout=XFER_TOTAL_S)
        else:
            await send_json(writer, send_lock,
                            {"id": msg_id, "type": "put-error",
                             "message": "unknown op: %s" % op})
    except asyncio.TimeoutError:
        await send_json(writer, send_lock,
                        {"id": msg_id, "type": "put-error",
                         "message": "total transfer timeout"})


# --- connection handling (borrowed from squawk-ws) --------------------------
async def handle_client(reader, writer):
    peer = writer.get_extra_info("peername")
    send_lock = asyncio.Lock()
    tasks = set()
    try:
        try:
            raw = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), timeout=10)
        except (asyncio.TimeoutError, asyncio.LimitOverrunError,
                asyncio.IncompleteReadError):
            writer.close()
            return
        head = raw.decode("latin-1")
        lines = head.split("\r\n")
        parts = lines[0].split(" ", 2)
        headers = {}
        for ln in lines[1:]:
            if ":" in ln:
                k, v = ln.split(":", 1)
                headers[k.strip().lower()] = v.strip()
        ok = (len(parts) == 3 and parts[0] == "GET" and parts[1] == WS_PATH
              and "websocket" in headers.get("upgrade", "").lower()
              and "upgrade" in headers.get("connection", "").lower()
              and headers.get("sec-websocket-version") == "13"
              and "sec-websocket-key" in headers)
        if not ok:
            writer.write(b"HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n"
                         b"Connection: close\r\n\r\n")
            await writer.drain()
            writer.close()
            return
        token = read_token()
        provided = headers.get("x-mcp-token", "")
        if not token or not hmac.compare_digest(provided.encode(),
                                                token.encode()):
            writer.write(b"HTTP/1.1 401 Unauthorized\r\nContent-Length: 0\r\n"
                         b"Connection: close\r\n\r\n")
            await writer.drain()
            writer.close()
            log("rejected unauthorized handshake from %s" % (peer,))
            return
        accept = base64.b64encode(hashlib.sha1(
            (headers["sec-websocket-key"] + WS_GUID).encode()).digest()).decode()
        writer.write(("HTTP/1.1 101 Switching Protocols\r\n"
                      "Upgrade: websocket\r\n"
                      "Connection: Upgrade\r\n"
                      "Sec-WebSocket-Accept: %s\r\n\r\n" % accept).encode())
        await writer.drain()
        log("client %s connected" % (peer,))

        while True:
            msg = await read_message(reader, writer, send_lock)
            if msg is None:
                break
            is_text, payload = msg
            if not is_text:
                continue  # binary frames only valid inside a transfer
            try:
                doc = json.loads(payload.decode("utf-8", "replace"))
            except ValueError:
                continue
            if not isinstance(doc, dict) or "id" not in doc:
                continue
            if "op" in doc:
                # transfers run inline: the connection is dedicated to the op
                await handle_transfer(reader, writer, send_lock, doc)
                continue
            if "argv" not in doc and "cmd" not in doc:
                continue
            argv = doc.get("argv")
            try:
                timeout = int(doc.get("timeout", TIMEOUT_S))
            except (TypeError, ValueError):
                timeout = TIMEOUT_S
            timeout = max(1, min(timeout, MAX_TIMEOUT_S))
            t = asyncio.create_task(run_command(
                writer, send_lock, str(doc["id"]),
                str(doc.get("cmd") or ""), str(doc.get("workdir") or "/home/toxic"),
                argv=argv, timeout=timeout))
            tasks.add(t)
            t.add_done_callback(tasks.discard)
    except (ConnectionResetError, asyncio.IncompleteReadError, BrokenPipeError):
        pass
    finally:
        for t in list(tasks):
            t.cancel()
        try:
            writer.close()
        except Exception:
            pass
        log("client %s disconnected" % (peer,))


async def main():
    try:
        server = await asyncio.start_server(handle_client, "127.0.0.1", PORT)
    except OSError as e:
        log("FATAL: cannot bind 127.0.0.1:%d: %s (port busy — stale holder?)" % (PORT, e))
        raise SystemExit(1)
    log("listening on 127.0.0.1:%d%s" % (PORT, WS_PATH))
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
