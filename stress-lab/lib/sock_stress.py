#!/usr/bin/env python3
"""socket edge-case stress harness — measurement, not DoS.
Arms: payload cap overflow, half-close, fragmented/boundary payloads, concurrent conn flood.
Target: an echo server; run in-process so it's self-contained and non-destructive.
Returns a JSON verdict per arm (err signatures captured on stderr are isolated)."""
import socket, threading, time, json, sys, os

HOST, PORT = "127.0.0.1", 0  # ephemeral port
CAP = 1 << 16  # 64KiB payload cap the server enforces

def start_echo(cap=CAP):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT)); srv.listen(128)
    port = srv.getsockname()[1]
    sig = {"overflow": 0, "halfclose": 0, "fragment": 0, "flood": 0}
    def handle(c):
        try:
            data = b""
            while True:
                chunk = c.recv(1 << 15)
                if not chunk: break
                data += chunk
            if len(data) > cap: sig["overflow"] += 1
            if len(data) == 0: sig["halfclose"] += 1
            if 0 < len(data) <= cap: c.sendall(data)
        except Exception: pass
        finally:
            try: c.close()
            except Exception: pass
    def loop():
        while True:
            c, _ = srv.accept()
            threading.Thread(target=handle, args=(c,), daemon=True).start()
    threading.Thread(target=loop, daemon=True).start()
    return port, sig

def verdicts(port, sig):
    out = {}
    # arm A: payload cap overflow — send CAP+1 bytes, server must reject/flag
    try:
        s = socket.socket(); s.settimeout(2); s.connect(("127.0.0.1", port))
        s.sendall(b"x" * (CAP + 1)); s.shutdown(socket.SHUT_WR)
        data = s.recv(CAP + 2); s.close()
        out["a-overflow"] = {"sent": CAP + 1, "recv": len(data), "sig": "overflow", "ok": len(data) == 0}
    except Exception as e:
        out["a-overflow"] = {"err": str(e), "ok": False}
    # arm B: half-close (SHUT_WR) then read — echo should return EOF, not hang
    try:
        s = socket.socket(); s.settimeout(2); s.connect(("127.0.0.1", port))
        s.sendall(b"hello-half"); s.shutdown(socket.SHUT_WR)
        r = s.recv(64); s.close()
        out["b-halfclose"] = {"sent": b"hello-half".decode(), "recv": r.decode(errors="replace"), "ok": r == b"hello-half"}
    except Exception as e:
        out["b-halfclose"] = {"err": str(e), "ok": False}
    # arm C: fragmented/boundary payload — send many small chunks, echo must reassemble
    try:
        s = socket.socket(); s.settimeout(2); s.connect(("127.0.0.1", port))
        total = b""
        for i in range(8):
            chunk = bytes([65 + i]) * (i + 1)
            s.sendall(chunk); total += chunk
        s.shutdown(socket.SHUT_WR); r = b""
        while True:
            part = s.recv(64)
            if not part: break
            r += part
        s.close()
        out["c-fragment"] = {"sent": len(total), "recv": len(r), "ok": r == total}
    except Exception as e:
        out["c-fragment"] = {"err": str(e), "ok": False}
    # arm D: concurrent flood — 16 parallel conns each small, all echo back
    def one(i):
        try:
            s = socket.socket(); s.settimeout(2); s.connect(("127.0.0.1", port))
            s.sendall(f"m{i}".encode()); s.shutdown(socket.SHUT_WR)
            return s.recv(16)
        except Exception as e:
            return ("ERR:" + str(e)).encode()
    conns = 16
    vals = []
    threads = [threading.Thread(target=lambda i=i: vals.append(one(i))) for i in range(conns)]
    [t.start() for t in threads]; [t.join() for t in threads]
    out["d-flood"] = {"conns": conns, "ok": len([v for v in vals if v]) == conns}
    return out

if __name__ == "__main__":
    port, sig = start_echo()
    time.sleep(0.2)
    res = verdicts(port, sig)
    # isolate stderr signatures: any socket.errno/TimeoutError/ConnectionReset maps to a patch
    errsignals = []
    for k, v in res.items():
        if not v.get("ok"):
            errsignals.append({"arm": k, "err": v.get("err", "timeout/reset")})
    print(json.dumps({"verdicts": res, "err_signatures": errsignals}, indent=2))
    # exit 0 only if all arms ok
    sys.exit(0 if all(v.get("ok") for v in res.values()) else 1)
