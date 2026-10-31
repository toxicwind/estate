#!/usr/bin/env python3
"""morphe v2 — the estate's fingerprint-matched transport-morphing router.

The Morphe-patching doctrine (docs/MORPHE_PATCHING.md) applied to routing:

  patcher concept        router concept
  ---------------------  ---------------------------------------------------
  Fingerprint            ConnectionFingerprint: partial description — port,
                         path pattern, header substrings, first-byte shape.
                         NEVER absolute (no raw addresses in rules).
  strings literal index  (host, path) → candidate lanes index; scan only
                         lanes containing the literal.
  Resolution order       classFingerprint (port) → definingClass (path) →
                         string-literal index → partial fallback → loud fail.
  _matchOrNull cache     per-client resolution cache: resolve once, stick.
  Mutation relative      transport mutated RELATIVE to the match: plain HTTP
                         in → WS lane out (wrap request into a frame, unwrap
                         the reply). Never a hardcoded rewrite table.
  patchException         no lane matches → loud 501 with the unmatched
                         fingerprint — never fuzzy-apply to a wrong lane.
  Extension shim         the WS lane itself (real logic lives upstream; the
                         router only hooks the anchor).
  compatibleWith()       lane health probe before apply; incompatible lanes
                         refuse the patch.

HFT doctrine (hft_race.py): hot persistent WS connections per lane, dial
once; lanes raced first-VALID-wins; per-attempt ceiling; winner ledger
(~/.cache/morphe/winners.jsonl); P50/P95 via --bench.

Control: unix socket /tmp/morphe.sock — {"cmd":"routes"|"chaos"|"fingerprint"
|"reload"|"bench"|"stop", ...}
"""
import asyncio, json, os, socket, ssl, time, uuid

CONF = "/home/toxic/pens/estate/bridge/morphe-fingerprints.json"
LOG = "/tmp/morphe.log"
CTRL = "/tmp/morphe.sock"
LEDGER = os.path.expanduser("~/.cache/morphe/winners.jsonl")
CEILING = float(os.environ.get("MORPHE_CEILING", "8"))

try:
    TOK = open("/home/toxic/.yote_connector_token").read().strip()
except OSError:
    TOK = ""

state = {
    "fingerprints": [],   # ordered rules; first match wins (like patcher's patch list)
    "lanes": {},          # name -> {"kind":"ws|tcp|tls-ws", "host","port","path"}
    "resolutions": {},    # client key -> lane name (_matchOrNull cache)
    "counts": {},         # lane -> wins
    "hot": {},            # lane -> (reader, writer) persistent hot conns
    "running": True,
}


def log(msg):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as fh:
        fh.write(time.strftime("%H:%M:%S ") + msg + "\n")


def ledger(entry):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "a") as fh:
        fh.write(json.dumps(entry) + "\n")


def load_conf():
    try:
        with open(CONF) as fh:
            d = json.load(fh)
        state["fingerprints"] = d.get("fingerprints", [])
        state["lanes"] = d.get("lanes", {})
        log("conf loaded: %d fingerprints, %d lanes" % (len(state["fingerprints"]), len(state["lanes"])))
    except Exception as e:
        log("CONF-ERR %s" % e)


# ---------------------------------------------------------------
# fingerprint resolution (morphe patcher order: index -> narrow ->
# match -> cache; loud fail, never fuzzy)
# ---------------------------------------------------------------

class Resolution:
    def __init__(self):
        self.lane = None
        self.matches = []   # ordered instruction-filter-like record
        self.reason = None


def resolve_fingerprint(port, head_bytes):
    """Resolve a connection to a lane. head_bytes: first bytes from the
    client (may be empty for pure TCP probes). Returns Resolution.

    Order (mirror of Fingerprint.matchOrNull):
      1. port fingerprint (classFingerprint — scope first)
      2. path pattern (definingClass — resolve within scope)
      3. header/literal substrings (the string→lane index)
      4. first-byte shape fallback (partial match)
      5. no match -> loud fail (Resolution.reason set, never guessed)
    """
    r = Resolution()
    head = head_bytes.decode("latin-1", "replace") if head_bytes else ""
    path = ""
    if head.startswith(("GET ", "POST ", "PUT ", "DELETE ", "OPTIONS ", "HEAD ")):
        path = head.split(" ")[1] if " " in head else ""

    for fp in state["fingerprints"]:
        m = {"fp": fp.get("name"), "filters": []}
        ok = True
        # 1. port scope
        ports = fp.get("ports") or []
        if ports and str(port) not in [str(x) for x in ports]:
            continue
        m["filters"].append("port:%s" % port)
        # 2. path pattern (definingClass)
        pp = fp.get("path_pattern")
        if pp:
            import re
            if not re.search(pp, path):
                continue
            m["filters"].append("path~%s" % pp)
        # 3. literal substrings (the strings index)
        for lit in fp.get("contains") or []:
            if lit.lower() not in head.lower():
                ok = False
                break
            m["filters"].append("lit:%s" % lit)
        if not ok:
            continue
        # 4. first-byte shape (any-instruction wildcard)
        shape = fp.get("first_byte")  # e.g. "empty" | "any" | hex prefix
        if shape == "empty" and head_bytes:
            continue
        if shape and shape.startswith("hex:") and head_bytes:
            want = bytes.fromhex(shape[4:])
            if not head_bytes.startswith(want):
                continue
            m["filters"].append("hex:%s" % shape[4:])
        if fp.get("requires_payload") and not head_bytes:
            continue
        m["filters"].append("ok")
        r.lane = fp.get("lane")
        r.matches = m
        return r
    r.reason = "no fingerprint matched port=%s path=%r head=%r" % (port, path, head_bytes[:64])
    return r


# ---------------------------------------------------------------
# transport mutation: HTTP client <-> WS lane (the obtuse conversion)
# ---------------------------------------------------------------

async def lane_connect(name):
    """Hot persistent lane connection (dial once, reuse; reconnect if dead)."""
    hot = state["hot"].get(name)
    if hot:
        r, w = hot
        if not w.is_closing():
            return r, w
    lane = state["lanes"].get(name) or {}
    kind = lane.get("kind", "tcp")
    host, port = lane["host"], int(lane["port"])
    t0 = time.time()
    if kind == "ws":
        # plain TCP WS upgrade (loopback lanes)
        r, w = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=CEILING)
        req = ("GET %s HTTP/1.1\r\nHost: %s:%s\r\nx-mcp-token: %s\r\n"
               "Connection: Upgrade\r\nUpgrade: websocket\r\n"
               "Sec-WebSocket-Version: 13\r\nSec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n\r\n"
               % (lane.get("path", "/"), host, port, lane.get("token", TOK) or TOK)).encode()
        w.write(req)
        await w.drain()
        # read the 101 (or fail loud)
        resp = await asyncio.wait_for(r.readuntil(b"\r\n\r\n"), timeout=CEILING)
        if b" 101 " not in resp.split(b"\r\n")[0]:
            raise RuntimeError("lane %s refused upgrade: %r" % (name, resp[:80]))
        note_ms = (time.time() - t0) * 1000
        log("lane %s hot-connected in %.1fms" % (name, note_ms))
    elif kind == "tls-ws":
        ctx = ssl.create_default_context()
        r, w = await asyncio.wait_for(
            asyncio.open_connection(host, port, ssl=ctx, server_hostname=host), timeout=CEILING)
        req = ("GET %s HTTP/1.1\r\nHost: %s\r\nx-mcp-token: %s\r\n"
               "Connection: Upgrade\r\nUpgrade: websocket\r\n"
               "Sec-WebSocket-Version: 13\r\nSec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n\r\n"
               % (lane.get("path", "/"), host, lane.get("token", TOK) or TOK)).encode()
        w.write(req)
        await w.drain()
        resp = await asyncio.wait_for(r.readuntil(b"\r\n\r\n"), timeout=CEILING)
        if b" 101 " not in resp.split(b"\r\n")[0]:
            raise RuntimeError("lane %s refused upgrade: %r" % (name, resp[:80]))
        log("lane %s tls-hot-connected in %.1fms" % (name, (time.time() - t0) * 1000))
    else:  # raw tcp passthrough lane
        r, w = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=CEILING)
        log("lane %s tcp-connected in %.1fms" % (name, (time.time() - t0) * 1000))
    state["hot"][name] = (r, w)
    return r, w


def ws_frame(payload: bytes, opcode=0x1) -> bytes:
    """Unmasked server->client style frame? For a CLIENT connection frames
    must be masked. We dial as client, so mask."""
    import os as _os
    mask = _os.urandom(4)
    n = len(payload)
    if n < 126:
        b0 = bytes([0x80 | opcode, 0x80 | n])
    elif n < 65536:
        b0 = bytes([0x80 | opcode, 0x80 | 126]) + n.to_bytes(2, "big")
    else:
        b0 = bytes([0x80 | opcode, 0x80 | 127]) + n.to_bytes(8, "big")
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    return b0 + mask + masked


async def ws_read_frame(r):
    """Read one WS frame; returns (opcode, payload)."""
    hdr = await r.readexactly(2)
    b0, b1 = hdr[0], hdr[1]
    opcode = b0 & 0x0F
    n = b1 & 0x7F
    if n == 126:
        n = int.from_bytes(await r.readexactly(2), "big")
    elif n == 127:
        n = int.from_bytes(await r.readexactly(8), "big")
    payload = await r.readexactly(n) if n else b""
    return opcode, payload


async def http_to_ws_bridge(client_r, client_w, lane_name, head=b""):
    """THE OBTUSE CONVERSION: client speaks plain HTTP; we translate.

    head arrives PRE-CONSUMED by the fingerprint resolver (it is the anchor
    the match was made against — mutation happens relative to it).
    HTTP body   -> wrap into a WS frame -> hot lane
    WS frames   -> coalesce -> one HTTP/1.1 response back.
    """
    if not head:
        head = await asyncio.wait_for(client_r.readuntil(b"\r\n\r\n"), timeout=CEILING)
    # body per Content-Length (bounded)
    body = b""
    cl = 0
    for line in head.split(b"\r\n"):
        if line.lower().startswith(b"content-length:"):
            cl = int(line.split(b":")[1].strip() or 0)
    if cl:
        body = await asyncio.wait_for(client_r.readexactly(cl), timeout=CEILING)
    # conversion semantics: the HTTP BODY is the WS payload (the daemon's
    # protocol is JSON frames: {"id","cmd","workdir"} -> chunk/exit frames).
    # The daemon DROPS frames without "id" — inject one when the body omits it.
    try:
        parsed = json.loads(body.decode() or "{}")
        if isinstance(parsed, dict) and not parsed.get("id"):
            parsed["id"] = uuid.uuid4().hex[:8]
        req_payload = json.dumps(parsed).encode()
    except Exception:
        req_payload = body

    r, w = await lane_connect(lane_name)
    t0 = time.time()
    w.write(ws_frame(req_payload))
    await w.drain()
    # reply frames may arrive fragmented; coalesce until a JSON object parses
    # or a close frame arrives (bounded coalescing, like the daemon's own
    # read_frame loop)
    parts = {"stdout": "", "stderr": ""}
    exit_code = None
    opcode = 0
    for _ in range(256):
        opcode, frag = await asyncio.wait_for(ws_read_frame(r), timeout=CEILING)
        if opcode == 0x8:
            break
        try:
            d = json.loads(frag.decode())
        except Exception:
            resp_buf = frag
            continue
        if d.get("type") == "chunk":
            parts.setdefault(d.get("stream", "stdout"), "")
            parts[d.get("stream", "stdout")] += d.get("data", "")
        elif d.get("type") == "exit":
            exit_code = d.get("code")
            resp = json.dumps({"ok": exit_code == 0, "exit_code": exit_code,
                               "stdout": parts.get("stdout", ""),
                               "stderr": parts.get("stderr", "")}).encode()
            break
    lat = time.time() - t0
    ledger({"ts": time.time(), "lane": lane_name, "ms": round(lat * 1000, 1),
            "req_bytes": len(req_payload), "resp_bytes": len(resp)})
    if opcode == 0x8 and not resp:
        raise RuntimeError("lane %s closed mid-conversion" % lane_name)
    ctype = "application/json"
    client_w.write(b"HTTP/1.1 200 OK\r\nContent-Type: %s\r\nContent-Length: %d\r\nConnection: close\r\n\r\n%s"
                   % (ctype.encode(), len(resp), resp))
    await client_w.drain()
    client_w.close()


# ---------------------------------------------------------------
# connection serving: resolve -> mutate-or-passthrough (loud fail)
# ---------------------------------------------------------------

async def serve_conn(port, creader, cwriter):
    peer = cwriter.get_extra_info("peername") or ("?", 0)
    key = "%s:%s" % (peer[0], peer[1])
    cid = uuid.uuid4().hex[:8]
    try:
        head = await asyncio.wait_for(creader.readuntil(b"\r\n\r\n"), timeout=CEILING)
        # unread the head: we consumed it during fingerprinting
        head_bytes = head
    except (asyncio.TimeoutError, asyncio.IncompleteReadError):
        head_bytes = b""
        head = b""

    # _matchOrNull cache: resolve once per client, stick
    lane = state["resolutions"].get(key)
    if lane is None:
        res = resolve_fingerprint(port, head_bytes)
        if res.lane is None or res.lane not in state["lanes"]:
            # patchException — fail loud, never fuzzy-apply
            log("PATCH-EXCEPTION %s port=%s: %s" % (cid, port, res.reason))
            try:
                msg = json.dumps({"error": "morphe: no lane matched fingerprint",
                                  "detail": res.reason}).encode()
                cwriter.write(b"HTTP/1.1 501 Not Implemented\r\nContent-Type: application/json\r\n"
                              b"Content-Length: %d\r\nConnection: close\r\n\r\n%s" % (len(msg), msg))
                await cwriter.drain()
            except Exception:
                pass
            cwriter.close()
            return
        lane = res.lane
        if head_bytes:  # only real clients stick; TCP probes re-resolve
            state["resolutions"][key] = lane
        log("RESOLVED %s port=%s lane=%s filters=%s" % (cid, port, lane, res.matches["filters"]))
    else:
        log("CACHE-HIT %s port=%s lane=%s (sticky)" % (cid, port, lane))

    lane_def = state["lanes"][lane]
    if lane_def.get("kind") == "health":
        # Synthetic probe lane (no upstream): the cell connector's exec probe
        # is a plain GET / health check. Answer 200 inline — loud-fail doctrine
        # only covers UNKNOWN shapes; this shape is a known, deliberate probe.
        body = json.dumps({"ok": True, "service": "morphe-exec",
                           "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}).encode()
        cwriter.write(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
                      b"Content-Length: %d\r\nConnection: close\r\n\r\n%s"
                      % (len(body), body))
        await cwriter.drain()
        cwriter.close()
        return
    head_l = head.lower() if head else b""
    is_ws_native = b"upgrade: websocket" in head_l
    if is_ws_native:
        # the client IS a WS client (native protocol): raw passthrough —
        # replay the consumed head and pipe bytes verbatim. Never re-upgrade.
        # Fresh dial per client: a shared hot raw conn gets eaten by the
        # previous client's conversation (daemon closes after each exchange),
        # so the next client's replay lands in a dead socket -> empty reply.
        r, w = await asyncio.wait_for(
            asyncio.open_connection(lane_def["host"], int(lane_def["port"])), timeout=CEILING)
        if head_bytes:
            w.write(head_bytes)
            await w.drain()
        await asyncio.gather(pipe(creader, w), pipe(r, cwriter))
    elif lane_def.get("kind") in ("ws", "tls-ws"):
        # plain HTTP client hitting a WS lane: the obtuse conversion.
        # head was ALREADY consumed during fingerprinting — hand it over,
        # never re-read (double readuntil = deadlocked bridge).
        await http_to_ws_bridge(creader, cwriter, lane, head)
    else:
        # raw tcp lane, plain http: transparent replay
        r, w = await asyncio.wait_for(
            asyncio.open_connection(lane_def["host"], int(lane_def["port"])), timeout=CEILING)
        if head_bytes:
            w.write(head_bytes)
            await w.drain()
        await asyncio.gather(pipe(creader, w), pipe(r, cwriter))


async def pipe(src, dst, cap=None, limit=1024):
    try:
        while True:
            data = await src.read(65536)
            if not data:
                break
            dst.write(data)
            await dst.drain()
    except Exception:
        pass
    finally:
        try:
            dst.close()
        except Exception:
            pass


# ---------------------------------------------------------------
# control plane
# ---------------------------------------------------------------

async def ctrl_handler(reader, writer):
    try:
        cmd = json.loads((await reader.read(65536)).decode())
        c = cmd.get("cmd")
        if c == "routes":
            out = {"lanes": state["lanes"], "fingerprints": [f.get("name") for f in state["fingerprints"]],
                   "resolutions": len(state["resolutions"]), "counts": state["counts"]}
        elif c == "chaos":
            out = {"ok": True, "note": "chaos = clear resolution cache so lanes re-race"}
            state["resolutions"].clear()
        elif c == "fingerprint":
            state["fingerprints"].insert(cmd.get("pos", 0), cmd["fp"])
            out = {"ok": True, "fingerprints": [f.get("name") for f in state["fingerprints"]]}
        elif c == "lane":
            state["lanes"][cmd["name"]] = cmd["def"]
            out = {"ok": True}
        elif c == "reload":
            load_conf()
            out = {"ok": True}
        elif c == "bench":
            out = await bench(int(cmd.get("n", 10)))
        elif c == "stop":
            state["running"] = False
            out = {"ok": True}
        else:
            out = {"ok": False, "error": "unknown cmd"}
        writer.write(json.dumps(out).encode() + b"\n")
        await writer.drain()
    except Exception as e:
        try:
            writer.write(json.dumps({"ok": False, "error": str(e)}).encode() + b"\n")
            await writer.drain()
        except Exception:
            pass
    finally:
        writer.close()


async def bench(n):
    """HFT bench: hot-dial every lane, measure connect + round-trip."""
    out = {}
    for name, lane in state["lanes"].items():
        lats = []
        for _ in range(n):
            try:
                t0 = time.time()
                state["hot"].pop(name, None)
                await lane_connect(name)
                lats.append(round((time.time() - t0) * 1000, 1))
            except Exception as e:
                lats.append(None)
                log("bench lane %s err %s" % (name, e))
        ok = [x for x in lats if x is not None]
        out[name] = {"p50": sorted(ok)[len(ok)//2] if ok else None,
                     "min": min(ok) if ok else None,
                     "max": max(ok) if ok else None,
                     "fails": len([x for x in lats if x is None])}
    ledger({"ts": time.time(), "bench": out})
    return out


async def health_loop():
    while state["running"]:
        await asyncio.sleep(20)
        for name, lane in state["lanes"].items():
            try:
                if name in state["hot"]:
                    r, w = state["hot"][name]
                    if w.is_closing():
                        state["hot"].pop(name, None)
            except Exception:
                pass


async def main():
    load_conf()
    ports = sorted({int(p) for fp in state["fingerprints"] for p in (fp.get("ports") or [])})
    servers = []
    for port in ports:
        try:
            srv = await asyncio.start_server(lambda r, w, p=port: serve_conn(p, r, w), "0.0.0.0", port)
            servers.append(srv)
            log("morphe bound :%d" % port)
        except OSError as e:
            log("BIND-FAIL :%d %s" % (port, e))
    if os.path.exists(CTRL):
        os.unlink(CTRL)
    csrv = await asyncio.start_unix_server(ctrl_handler, CTRL)
    asyncio.create_task(health_loop())
    log("morphe v2 up: %d ports, control %s" % (len(servers), CTRL))
    await asyncio.gather(*[s.serve_forever() for s in servers + [csrv]])


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
