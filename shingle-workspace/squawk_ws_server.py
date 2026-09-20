#!/usr/bin/env python3
"""squawk-ws: stdlib-only asyncio websocket push feed for Squawk channels.

Watches Squawk message sources and broadcasts new messages as JSON
{seq, channel, sender, text, ts, sealed} over websockets.

Sources:
  - <CHAT_ROOT>/fleet/*.md and <CHAT_ROOT>/leads/*.md (chat.py channel files)
  - zipfs-vault local zip manifest aliases <channel>/<NNNNNN> (unsealed relay lane)

Protocol:
  - HTTP GET /squawk-ws with Upgrade: websocket and
    Authorization: Bearer <token> (constant-time compare; token file re-read
    on every handshake so rotation needs no restart).
  - Client sends {"subscribe": ["fleet", "leads"]} -> server replays the last
    ~20 messages per channel from history, then streams live broadcasts.
  - Server-assigned global seqs are persisted; clients dedup on reconnect.

Sealed messages are broadcast as {"sealed": true} with NO text content, ever.
"""
import asyncio
import base64
import hashlib
import hmac
import json
import os
import re
import signal
import time
import zipfile
from datetime import datetime
from pathlib import Path

WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
WS_PATH = "/squawk-ws"

PORT = int(os.environ.get("SQUAWK_WS_PORT", "25147"))
WS_DIR = Path(os.environ.get("SQUAWK_WS_DIR", "/home/toxic/squawk-ws"))
TOKEN_FILE = Path(os.environ.get("SQUAWK_WS_TOKEN_FILE", str(WS_DIR / "token")))
STATE_FILE = WS_DIR / "state.json"
HISTORY_FILE = WS_DIR / "history.jsonl"
CHAT_ROOT = Path(os.environ.get("SQUAWK_CHAT_ROOT", "/home/toxic/.shingle/squawk-root"))
VAULT_ZIP = Path(os.environ.get("SQUAWK_VAULT_ZIP",
                                "/home/toxic/workspace/skills/zipfs-vault/store/vault.zip"))
CHANNELS = [c for c in os.environ.get("SQUAWK_WS_CHANNELS", "fleet,leads").split(",") if c]

ALIAS_RE = re.compile(r"^([A-Za-z0-9_-]+)/(\d+)$")
HISTORY_KEEP = 2000
HISTORY_TRIM_AT = 2500
SEEN_KEEP = 5000

subscribers = {c: set() for c in CHANNELS}  # channel -> set of asyncio.Queue
seen = {}          # dedup_key -> True (insertion ordered)
next_seq = 1


def log(*a):
    print("[squawk-ws]", *a, flush=True)


def read_token():
    try:
        return TOKEN_FILE.read_text().strip()
    except OSError:
        return ""


def load_state():
    global next_seq, seen
    try:
        s = json.loads(STATE_FILE.read_text())
        next_seq = int(s.get("next_seq", 1))
        for k in s.get("seen", [])[-SEEN_KEEP:]:
            seen[k] = True
        log("state loaded: next_seq=%d seen=%d" % (next_seq, len(seen)))
    except (OSError, ValueError):
        log("no state file, starting fresh")


def save_state():
    try:
        keys = list(seen.keys())[-SEEN_KEEP:]
        STATE_FILE.write_text(json.dumps({"next_seq": next_seq, "seen": keys}))
    except OSError as e:
        log("state save failed:", e)


def norm_ts(ts):
    ts = (ts or "").strip()
    try:
        return datetime.fromisoformat(ts).isoformat()
    except ValueError:
        return ts


def dkey(channel, sender, ts, text):
    h = hashlib.sha1()
    h.update(("%s\x00%s\x00%s\x00%s" % (channel, sender, norm_ts(ts), text)).encode("utf-8"))
    return h.hexdigest()[:16]


# ---------------- message sources ----------------

def parse_md(path):
    """Parse a chat.py channel .md file -> message dict (no seq) or None."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    if not lines or lines[0].strip() != "---":
        return None
    fm = {}
    i = 1
    while i < len(lines) and lines[i].strip() != "---":
        if ":" in lines[i]:
            k, v = lines[i].split(":", 1)
            fm[k.strip().lower()] = v.strip()
        i += 1
    body = "\n".join(lines[i + 1:]).strip()
    channel = fm.get("channel", "")
    if channel not in CHANNELS:
        return None
    sealed = fm.get("sealed", "").lower() == "true" or fm.get("status", "").lower() == "sealed"
    return {
        "channel": channel,
        "sender": fm.get("from", "?"),
        "text": "" if sealed else body[:500],
        "ts": fm.get("ts", ""),
        "sealed": sealed,
    }


def scan_channel_files():
    out = []
    for channel in CHANNELS:
        d = CHAT_ROOT / channel
        if not d.is_dir():
            continue
        files = sorted(d.glob("*.md"), key=lambda p: p.name)
        for p in files:
            m = parse_md(p)
            if m:
                out.append(m)
    return out


def scan_vault():
    out = []
    try:
        z = zipfile.ZipFile(VAULT_ZIP)
    except Exception:
        return out
    try:
        manifest = json.loads(z.read("manifest.json"))
    except Exception:
        return out
    items = []
    for alias, meta in manifest.items():
        m = ALIAS_RE.match(alias)
        if not m or m.group(1) not in CHANNELS:
            continue
        items.append((m.group(1), int(m.group(2)), meta.get("blob", "")))
    items.sort(key=lambda t: (t[0], t[1]))
    for channel, _n, blob in items:
        try:
            env = json.loads(z.read("blobs/" + blob).decode("utf-8"))
        except Exception:
            continue
        sealed = bool(env.get("sealed"))
        out.append({
            "channel": channel,
            "sender": str(env.get("sender", "?")),
            "text": "" if sealed else str(env.get("text", ""))[:500],
            "ts": str(env.get("ts", "")),
            "sealed": sealed,
        })
    return out


# ---------------- history + broadcast ----------------

def history_append(m):
    try:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(m, ensure_ascii=True) + "\n")
    except OSError as e:
        log("history append failed:", e)
    try:
        if HISTORY_FILE.stat().st_size > 0:
            with open(HISTORY_FILE, encoding="utf-8") as f:
                lines = f.readlines()
            if len(lines) > HISTORY_TRIM_AT:
                with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                    f.writelines(lines[-HISTORY_KEEP:])
    except OSError:
        pass


def backfill(channels, per_channel=20):
    out = []
    try:
        with open(HISTORY_FILE, encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return out
    by_ch = {c: [] for c in channels}
    for ln in lines:
        try:
            m = json.loads(ln)
        except ValueError:
            continue
        if m.get("channel") in by_ch:
            by_ch[m["channel"]].append(m)
    for c in channels:
        out.extend(by_ch[c][-per_channel:])
    out.sort(key=lambda m: m.get("seq", 0))
    return out


def broadcast(m):
    data = json.dumps(m, ensure_ascii=True)
    for q in list(subscribers.get(m["channel"], ())):
        try:
            q.put_nowait(data)
        except asyncio.QueueFull:
            pass


def ingest(messages, quiet=False):
    """Assign seqs to unseen messages; broadcast unless quiet. Returns count."""
    global next_seq
    new = 0
    for m in messages:
        key = dkey(m["channel"], m["sender"], m["ts"], m["text"])
        if key in seen:
            continue
        seen[key] = True
        m = dict(m)
        m["seq"] = next_seq
        next_seq += 1
        history_append(m)
        if not quiet:
            broadcast(m)
            log("broadcast seq=%d ch=%s from=%s sealed=%s" %
                (m["seq"], m["channel"], m["sender"], m["sealed"]))
        new += 1
    if len(seen) > SEEN_KEEP + 1000:
        for k in list(seen.keys())[:1000]:
            del seen[k]
    if new:
        save_state()
    return new


async def rescan(kind):
    if kind == "files":
        n = ingest(scan_channel_files())
    else:
        n = ingest(scan_vault())
    if n:
        log("rescan %s: %d new" % (kind, n))


# ---------------- websocket framing (stdlib) ----------------

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


async def read_text_message(reader, writer, timeout=30):
    """Assemble one complete text message, answering pings. Returns str or None on close."""
    buf = bytearray()
    while True:
        fin, opcode, payload = await asyncio.wait_for(read_frame(reader), timeout)
        if opcode == 0x8:  # close
            return None
        if opcode == 0x9:  # ping -> pong
            try:
                await send_frame(writer, 0xA, payload)
            except OSError:
                return None
            continue
        if opcode == 0x1:
            buf = bytearray(payload)
        elif opcode == 0x0:
            buf += payload
        else:
            continue
        if fin:
            return bytes(buf).decode("utf-8", "replace")


async def pump(writer, q):
    try:
        while True:
            try:
                data = await asyncio.wait_for(q.get(), timeout=25)
            except asyncio.TimeoutError:
                await send_frame(writer, 0x9, b"squawk")  # ping
                continue
            await send_frame(writer, 0x1, data.encode("utf-8"))
    except (ConnectionResetError, BrokenPipeError, asyncio.IncompleteReadError):
        pass


async def read_loop(reader, writer):
    try:
        while True:
            _fin, opcode, payload = await read_frame(reader)
            if opcode == 0x8:
                try:
                    await send_frame(writer, 0x8, payload)
                except OSError:
                    pass
                return
            if opcode == 0x9:
                try:
                    await send_frame(writer, 0xA, payload)
                except OSError:
                    return
    except (asyncio.IncompleteReadError, ConnectionResetError):
        pass


async def handle_client(reader, writer):
    peer = writer.get_extra_info("peername")
    try:
        try:
            raw = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), timeout=10)
        except (asyncio.TimeoutError, asyncio.LimitOverrunError, asyncio.IncompleteReadError):
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
        auth = headers.get("authorization", "")
        provided = auth[7:] if auth[:7].lower() == "bearer " else ""
        if not token or not hmac.compare_digest(provided.encode(), token.encode()):
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

        raw_sub = await read_text_message(reader, writer, timeout=30)
        if raw_sub is None:
            writer.close()
            return
        try:
            doc = json.loads(raw_sub)
        except ValueError:
            writer.close()
            return
        ch = doc.get("subscribe")
        if not (isinstance(ch, list) and ch and all(c in CHANNELS for c in ch)):
            writer.close()
            return

        q = asyncio.Queue(maxsize=100)
        for c in ch:
            subscribers[c].add(q)
        for m in backfill(ch):
            q.put_nowait(json.dumps(m, ensure_ascii=True))
        log("client %s subscribed %s (backfill sent)" % (peer, ch))
        sender = asyncio.create_task(pump(writer, q))
        try:
            await read_loop(reader, writer)
        finally:
            sender.cancel()
            for c in ch:
                subscribers[c].discard(q)
            log("client %s disconnected" % (peer,))
    except (ConnectionResetError, asyncio.IncompleteReadError, BrokenPipeError):
        pass
    finally:
        try:
            writer.close()
        except Exception:
            pass


# ---------------- watching ----------------

async def watch_loop(stop):
    # initial scan: prime seen+history, never broadcast
    ingest(scan_channel_files(), quiet=True)
    ingest(scan_vault(), quiet=True)
    log("initial scan done")

    fleet_dir = str(CHAT_ROOT / "fleet")
    leads_dir = str(CHAT_ROOT / "leads")
    vault_dir = str(VAULT_ZIP.parent)
    last = {"files": 0.0, "vault": 0.0}

    async def trigger(kind):
        now = time.monotonic()
        if now - last[kind] < 2.0:
            return
        last[kind] = now
        await rescan(kind)

    async def inotify_task():
        try:
            proc = await asyncio.create_subprocess_exec(
                "inotifywait", "-m", "-q",
                "-e", "close_write", "-e", "moved_to", "-e", "create",
                "--format", "%w%f",
                fleet_dir, leads_dir, vault_dir,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
        except FileNotFoundError:
            log("inotifywait missing, periodic rescan only")
            return
        async for line in proc.stdout:
            p = line.decode().strip()
            if p.startswith(vault_dir):
                await trigger("vault")
            else:
                await trigger("files")
            if stop.is_set():
                break

    async def periodic_task():
        while not stop.is_set():
            await asyncio.sleep(30)
            await rescan("files")
            await rescan("vault")
            save_state()

    await asyncio.gather(inotify_task(), periodic_task())


async def main():
    WS_DIR.mkdir(parents=True, exist_ok=True)
    load_state()
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:
            pass
    server = await asyncio.start_server(handle_client, "127.0.0.1", PORT)
    log("listening on 127.0.0.1:%d path %s" % (PORT, WS_PATH))
    await watch_loop(stop)
    server.close()
    save_state()


if __name__ == "__main__":
    asyncio.run(main())
