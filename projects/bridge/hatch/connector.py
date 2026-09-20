#!/usr/bin/env python3
"""yote-connector — a specific custom connector for yote.

Persistent cell-side daemon (runs as root), listening on a local TCP port
(default 127.0.0.1:18301). It reuses the proven WSS exec lane in-process
(bridge_exec module: ws_daemon unix socket, HTTPS fallback) and exposes:

  GET  /health          {"ok", "exec_probe", "ws_lane_claim",
                         "https_lane_claim", "https_down_reason", "ts"}
                         (ok=True requires a real authenticated exec probe;
                         *_claim flags are claims, not truth — see lines below)
  POST /exec            {"cmd", "workdir"?, "timeout"?} -> exec result dict
  POST /exec-multi      {"cmds": [{"cmd", "workdir"?, "timeout"?}], "max_workers"?}
                         -> {"results": [exec result dict per cmd, tagged]}
                         Runs N commands concurrently on yote (bridge-max).
  POST /exec-bg         {"cmd", "workdir"?} -> {"handle", "state"}
                         Dispatches a long-running command fully detached on
                         yote (setsid, own session, PPID 1). Returns immediately.
  GET  /bg              list known background handles + cached status
  GET  /bg/<handle>     live status: state, exit code, log tails
  /herd/*              proxied to yote 127.0.0.1:25100 (prefix stripped)
  /flock/*             proxied to yote 127.0.0.1:8000 (prefix stripped)

Service proxying is HTTP-over-exec via /home/toxic/.cache/yote_svc_proxy.py
on yote: one exec call per proxied request, no new yote ports, no server
changes. Only 127.0.0.1 is bound (cell-local callers).

Canonical source: projects/bridge/hatch/connector.py in toxicwind/sovereign-projects.
"""
import base64
import importlib.util
import json
import os
import re
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("YOTE_CONNECTOR_PORT", "18301"))
HERE = os.path.dirname(os.path.abspath(__file__))
BRIDGE_EXEC = os.path.expanduser("~/workspace/awrawr-bridge/exec.py")
YOTE_HELPER = "/home/toxic/.cache/yote_svc_proxy.py"
SVC_PORTS = {"herd": 25100, "flock": 8000}
MAX_BODY = 10 * 1024 * 1024

# --- bridge-max: background dispatch ---------------------------------------
BG_BASE_YOTE = "/home/toxic/.cache/bridge-bg"
BG_RUN_PY = "/home/toxic/sovereign/projects/bridge/bin/bg-run.py"
REGISTRY = os.path.expanduser("~/.cache/bridge-bg-registry.json")
HANDLE_RX = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
BG_TAIL_BYTES = 4000

_spec = importlib.util.spec_from_file_location("bridge_exec", BRIDGE_EXEC)
bridge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bridge)


def b64e(b):
    return base64.b64encode(b).decode()


def b64d(s):
    return base64.b64decode(s.encode())


def log(*a):
    sys.stderr.write("[yote-connector %s] %s\n"
                     % (time.strftime("%H:%M:%S"),
                        " ".join(str(x) for x in a)))
    sys.stderr.flush()


def yote_exec(cmd, workdir="/home/toxic", timeout=120):
    """Run cmd on yote; WS lane first, HTTPS fallback on pre-dispatch fail."""
    res = bridge._ws_exec(cmd, workdir, None, timeout, capture=True)
    if res is None:
        try:
            res = bridge._https_exec_capture(cmd, workdir, 150)
        except Exception as e:
            res = {"code": 1, "stdout": "", "stderr": "",
                   "transport": "none",
                   "error": "all lanes down: %s" % e}
    return res


# --- bridge-max: background registry (cell-side) ----------------------------

def _reg_load():
    try:
        with open(REGISTRY) as f:
            d = json.load(f)
            return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _reg_save(reg):
    try:
        os.makedirs(os.path.dirname(REGISTRY), exist_ok=True)
        tmp = REGISTRY + ".tmp"
        with open(tmp, "w") as f:
            json.dump(reg, f)
        os.replace(tmp, REGISTRY)
    except Exception as e:
        log("registry save failed: %s" % e)


def _bg_launch(cmd, workdir="/home/toxic"):
    """Dispatch cmd fully detached on yote. Returns handle.

    Detachment: the launch exec runs with workdir=rundir so `&` binds only
    to the setsid'd launcher (AGENTS.md daemon-start scoping rule). The
    launcher survives the exec session: new session (setsid), stdin
    /dev/null, output redirected. bg-run.py writes status.json atomically.
    """
    handle = uuid.uuid4().hex[:12]
    rundir = "%s/%s" % (BG_BASE_YOTE, handle)
    cmdb64 = b64e(cmd.encode())
    r = yote_exec("mkdir -p %s" % rundir, "/home/toxic", 30)
    if r.get("code") != 0:
        raise RuntimeError("mkdir failed: %s %s"
                           % (r.get("error"), r.get("stderr")))
    launch = ("setsid nohup python3 %s %s %s >launcher.log 2>&1 < /dev/null &"
              % (BG_RUN_PY, handle, cmdb64))
    r2 = yote_exec(launch, rundir, 30)
    if r2.get("code") != 0 or r2.get("error"):
        raise RuntimeError("launch failed: %s %s"
                           % (r2.get("error"), r2.get("stderr")))
    reg = _reg_load()
    reg[handle] = {"cmd": cmd[:500], "workdir": workdir,
                   "launched_at": time.time()}
    _reg_save(reg)
    log("bg dispatched handle=%s cmd=%.60s" % (handle, cmd))
    return handle


def _bg_status(handle):
    """Live status of a background handle. One exec call; poll-free truth
    is the yote-side status.json written atomically by bg-run.py."""
    if not HANDLE_RX.match(handle or ""):
        return {"handle": handle, "state": "bad-handle"}
    reg = _reg_load()
    info = reg.get(handle, {})
    rd = "%s/%s" % (BG_BASE_YOTE, handle)
    res = yote_exec(
        "cat %s/status.json 2>/dev/null; "
        "echo '---STDOUT_TAIL---'; tail -c %d %s/stdout.log 2>/dev/null; "
        "echo '---STDERR_TAIL---'; tail -c %d %s/stderr.log 2>/dev/null"
        % (rd, BG_TAIL_BYTES, rd, BG_TAIL_BYTES, rd),
        "/home/toxic", 30)
    out = {"handle": handle, "cmd": info.get("cmd"),
           "launched_at": info.get("launched_at")}
    if res.get("code") != 0 or res.get("error"):
        out.update({"state": "unknown",
                    "error": res.get("error") or res.get("stderr")})
        return out
    stdout = res.get("stdout", "")
    parts = stdout.split("---STDOUT_TAIL---", 1)
    status_raw = parts[0].strip()
    rest = parts[1] if len(parts) > 1 else ""
    logs = rest.split("---STDERR_TAIL---", 1)
    try:
        st = json.loads(status_raw) if status_raw else None
    except Exception:
        st = None
    if st:
        out.update(st)
        out["stdout_tail"] = logs[0] if len(logs) > 0 else ""
        out["stderr_tail"] = logs[1] if len(logs) > 1 else ""
    else:
        out.update({"state": "dispatched",
                    "note": "launcher accepted; bg-run.py not yet reporting"})
    return out


def svc_proxy(svc, method, path, headers, body):
    """Proxy one HTTP request to a yote-local service over the exec lane."""
    payload = {"method": method, "port": SVC_PORTS[svc], "path": path,
               "headers": dict(headers), "body_b64": b64e(body),
               "timeout": 60}
    arg = b64e(json.dumps(payload).encode())
    res = yote_exec("python3 %s '%s'" % (YOTE_HELPER, arg),
                    "/home/toxic", timeout=90)
    if res.get("code") != 0 or res.get("error"):
        return {"status": 502, "headers": {},
                "body": ("yote exec failed: %s %s"
                         % (res.get("error"), res.get("stderr"))).encode()}
    try:
        doc = json.loads(b64d(res["stdout"].strip()).decode())
    except Exception as e:
        return {"status": 502, "headers": {},
                "body": ("bad proxy frame: %s" % e).encode()}
    return {"status": int(doc.get("status", 502)),
            "headers": doc.get("headers", {}) or {},
            "body": b64d(doc.get("body_b64", ""))}


HOP_HEADERS = {"connection", "transfer-encoding", "keep-alive",
               "proxy-authenticate", "proxy-authorization", "te",
               "trailer", "upgrade"}


class Handler(BaseHTTPRequestHandler):
    server_version = "yote-connector/2.0"

    def _json(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_body(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
        except (TypeError, ValueError):
            n = 0
        if n > MAX_BODY:
            return None
        return self.rfile.read(n) if n > 0 else b""

    def _read_json(self):
        body = self._read_body()
        if body is None:
            return None, (413, {"error": "body too large"})
        try:
            return json.loads(body.decode() or "{}"), None
        except ValueError:
            return None, (400, {"error": "invalid JSON"})

    def do_GET(self):
        if self.path == "/health":
            # Lane flags below are claims, not truth: a connectable socket
            # does not prove authenticated execution (caught 2026-09-20:
            # both lanes "true" while every real command 401'd). The
            # authoritative bit is exec_probe: a real no-op command executed
            # end-to-end through auth. ok=True requires it.
            ws_ok = False
            try:
                s = bridge._ws_try_once()
                if s is not None:
                    ws_ok = True
                    s.close()
            except Exception:
                pass
            https_down, https_why = bridge._https_known_down()
            probe = {"ok": False, "ms": 0, "transport": None,
                     "error": "not run"}
            t0 = time.time()
            try:
                res = yote_exec("true", "/home/toxic", timeout=15)
                probe["ms"] = int((time.time() - t0) * 1000)
                probe["transport"] = res.get("transport")
                probe["code"] = res.get("code")
                err = res.get("error") or ""
                if err:
                    probe["error"] = err
                elif res.get("code") != 0:
                    probe["error"] = ("exit %s stderr=%s"
                                      % (res.get("code"),
                                         (res.get("stderr") or "")[:200]))
                else:
                    probe["ok"] = True
                    probe["error"] = None
            except Exception as e:
                probe["ms"] = int((time.time() - t0) * 1000)
                probe["error"] = "%s: %s" % (type(e).__name__, e)
            ok = probe["ok"]
            self._json(200 if ok else 503,
                       {"ok": ok, "exec_probe": probe,
                        "ws_lane_claim": ws_ok,
                        "https_lane_claim": not https_down,
                        "https_down_reason": https_why,
                        "ts": time.time()})
            return
        if self.path == "/bg":
            reg = _reg_load()
            items = []
            for h, info in sorted(reg.items(),
                                  key=lambda kv: kv[1].get("launched_at", 0),
                                  reverse=True):
                items.append({"handle": h, "cmd": info.get("cmd"),
                              "launched_at": info.get("launched_at")})
            self._json(200, {"handles": items})
            return
        if self.path.startswith("/bg/"):
            handle = self.path[len("/bg/"):].split("/")[0].split("?")[0]
            self._json(200, _bg_status(handle))
            return
        self._proxy()

    def do_POST(self):
        if self.path == "/exec":
            spec, err = self._read_json()
            if err:
                self._json(*err)
                return
            cmd = spec.get("cmd")
            if not cmd:
                self._json(400, {"error": "missing cmd"})
                return
            t0 = time.time()
            res = yote_exec(cmd, spec.get("workdir", "/home/toxic"),
                            int(spec.get("timeout", 120)))
            res["connector_ms"] = int((time.time() - t0) * 1000)
            self._json(200, res)
            return
        if self.path == "/exec-multi":
            # bridge-max: N commands, concurrent dispatch, tagged results.
            spec, err = self._read_json()
            if err:
                self._json(*err)
                return
            cmds = spec.get("cmds")
            if not isinstance(cmds, list) or not cmds:
                self._json(400, {"error": "cmds must be a non-empty list"})
                return
            if len(cmds) > 64:
                self._json(400, {"error": "max 64 commands per batch"})
                return
            try:
                max_workers = int(spec.get("max_workers",
                                           min(8, len(cmds))))
            except (TypeError, ValueError):
                max_workers = min(8, len(cmds))
            max_workers = max(1, min(16, max_workers))

            def one(c):
                t0 = time.time()
                try:
                    r = yote_exec(c.get("cmd", ""),
                                  c.get("workdir", "/home/toxic"),
                                  int(c.get("timeout", 120)))
                except Exception as e:
                    r = {"code": 1, "stdout": "", "stderr": "",
                         "error": "%s: %s" % (type(e).__name__, e)}
                r["tag"] = c.get("tag", c.get("cmd", "")[:80])
                r["connector_ms"] = int((time.time() - t0) * 1000)
                return r

            t0 = time.time()
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                results = list(ex.map(one, cmds))
            self._json(200, {"results": results,
                             "count": len(results),
                             "total_ms": int((time.time() - t0) * 1000)})
            return
        if self.path == "/exec-bg":
            # bridge-max: detached background dispatch. Returns a handle
            # immediately; poll status via GET /bg/<handle>.
            spec, err = self._read_json()
            if err:
                self._json(*err)
                return
            cmd = spec.get("cmd")
            if not cmd:
                self._json(400, {"error": "missing cmd"})
                return
            try:
                handle = _bg_launch(cmd, spec.get("workdir", "/home/toxic"))
            except Exception as e:
                self._json(500, {"error": "dispatch failed: %s" % e})
                return
            self._json(200, {"handle": handle, "state": "dispatched",
                             "status_url": "/bg/%s" % handle})
            return
        self._proxy()

    # PUT/PATCH/DELETE etc. also proxy to services.
    do_PUT = do_POST
    do_DELETE = do_POST
    do_PATCH = do_POST

    def _proxy(self):
        for svc in SVC_PORTS:
            prefix = "/" + svc + "/"
            if self.path == "/" + svc:
                rel, svc_hit = "/", svc
                break
            if self.path.startswith(prefix):
                rel, svc_hit = self.path[len(prefix) - 1:], svc
                break
        else:
            self._json(404, {"error": "unknown route",
                             "routes": ["/health", "/exec", "/exec-multi",
                                        "/exec-bg", "/bg", "/bg/<handle>",
                                        "/herd/*", "/flock/*"]})
            return
        body = self._read_body()
        if body is None:
            self._json(413, {"error": "body too large"})
            return
        t0 = time.time()
        try:
            res = svc_proxy(svc_hit, self.command, rel,
                            self.headers, body)
        except Exception as e:
            self._json(502, {"error": "proxy failure: %s: %s"
                             % (type(e).__name__, e)})
            return
        data = res["body"]
        self.send_response(res["status"])
        ctype = res["headers"].get("Content-Type",
                                   res["headers"].get("content-type"))
        self.send_header("Content-Type",
                         ctype or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Yote-Connector-Ms",
                         str(int((time.time() - t0) * 1000)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        log("%s %s" % (self.address_string(), fmt % args))


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    srv.daemon_threads = True
    log("listening on 127.0.0.1:%d (pid %d)" % (PORT, os.getpid()))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
