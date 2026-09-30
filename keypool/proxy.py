"""HTTP handler. The only file that opens sockets."""
import json
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler

from . import affinity as _aff, clock, translate

POOLS: dict = {}
ALERTS = None

HOP = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
       "te", "trailers", "transfer-encoding", "upgrade"}
STRIP = HOP | {"content-length", "host", "authorization", "x-api-key",
               "x-goog-api-key"}


def _emit(ev, **detail):
    if ALERTS is not None:
        ALERTS.emit({"ts": clock.wall(), "event": ev, "detail": detail})

LEDGER_PATH = "/home/toxic/.cache/keypool-usage/usage.jsonl"

def _ledger_record(pool_name, key_name, model, ms, out_doc):
    """Append one JSONL usage record. key_name only, never the key value."""
    try:
        import os, uuid
        usage = None
        req_id = None
        if isinstance(out_doc, dict):
            u = out_doc.get("usage")
            if isinstance(u, dict):
                usage = {k: u.get(k) for k in (
                    "total_tokens", "total_input_tokens", "total_output_tokens",
                    "total_cached_tokens", "total_thought_tokens",
                    "prompt_tokens", "completion_tokens") if u.get(k) is not None}
            req_id = out_doc.get("id") or str(uuid.uuid4())
        else:
            req_id = str(uuid.uuid4())
        os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
        rec = {"ts": clock.wall(), "event": "request_complete",
               "pool": pool_name, "key": key_name, "model": model,
               "ms": round(ms, 1), "usage": usage, "request_id": req_id}
        with open(LEDGER_PATH, "a") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception:
        pass


def _read_body(h):
    if "chunked" in h.headers.get("Transfer-Encoding", "").lower():
        b = bytearray()
        while True:
            line = h.rfile.readline().strip()
            if not line:
                break
            n = int(line.split(b";")[0], 16)
            if n == 0:
                while True:
                    t = h.rfile.readline()
                    if not t.strip():
                        break
                break
            b += h.rfile.read(n)
            h.rfile.readline()
        return bytes(b)
    n = int(h.headers.get("Content-Length") or 0)
    return h.rfile.read(n) if n else b""


def _model(raw: bytes):
    if not raw:
        return None
    try:
        d = json.loads(raw)
        m = d.get("model") if isinstance(d, dict) else None
        return m if isinstance(m, str) else None
    except Exception:
        return None




def _apply_auth(req, pool, ks):
    """Pick auth header by effective path, not by host.

    Gemini native endpoints (v1beta/models, v1beta/interactions) want
    x-goog-api-key. The OpenAI-compat endpoint at /v1beta/openai wants
    Authorization: Bearer. Same host, different contract.
    """
    up = pool.upstream.rstrip("/")
    if up.endswith("/openai"):
        req.add_header("Authorization", "Bearer " + ks.value)
    elif "generativelanguage.googleapis.com" in up:
        req.add_header("x-goog-api-key", ks.value)
    else:
        req.add_header("Authorization", "Bearer " + ks.value)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "KeyPool/3.0"

    def log_message(self, *a):
        pass

    def _json(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        p = self.path.split("?", 1)[0]
        if p in ("/health", "/health/"):
            self._json(200, {"ok": True, "pools": {
                n: {"keys": len(pl.keys),
                    "healthy": sum(1 for k in pl.keys if k.state == "healthy")}
                for n, pl in POOLS.items()}})
            return
        if p in ("/status", "/status/"):
            self._status()
            return
        self._proxy()

    def _status(self):
        out = {"ts": clock.wall(), "pools": {}}
        for n, pl in POOLS.items():
            out["pools"][n] = {
                "upstream": pl.upstream,
                "protocol": pl.protocol,
                "breaker": pl.breaker.snapshot(),
                "affinity_size": pl.affinity.size(),
                "keys": [k.public() for k in pl.keys],
            }
        self._json(200, out)

    def _route(self):
        parts = self.path.split("?", 1)[0].split("/", 2)
        if len(parts) < 2 or not parts[1]:
            return None, None
        return POOLS.get(parts[1]), "/" + parts[2] if len(parts) > 2 else "/"

    def _forward(self, pool, rest, raw, ks):
        url = pool.upstream + rest
        qs = self.path.split("?", 1)
        if len(qs) > 1:
            url += "?" + qs[1]
        req = urllib.request.Request(
            url, data=raw if self.command in ("POST", "PUT", "PATCH") else None,
            method=self.command)
        for k, v in self.headers.items():
            if k.lower() not in STRIP:
                req.add_header(k, v)
        _apply_auth(req, pool, ks)
        return urllib.request.urlopen(req, timeout=pool.request_timeout)

    def _serve(self, resp, transform=None, model=None):
        if transform:
            body = resp.read()
            try:
                doc = json.loads(body.decode("utf-8", "replace"))
                out = transform(doc, model or "eap")
                self._json(resp.status, out)
                return out
            except Exception:
                self._json(resp.status, {"error": "bad upstream body"})
            return None
        no_len = resp.headers.get("Content-Length") is None
        rctype = resp.headers.get("Content-Type", "")
        self.send_response(resp.status)
        for k, v in resp.headers.items():
            if k.lower() not in HOP:
                self.send_header(k, v)
        if no_len:
            self.send_header("Connection", "close")
        self.end_headers()
        streaming = ("text/event-stream" in rctype) or (
            no_len and "chunked" in resp.headers.get("Transfer-Encoding", "").lower()
        )
        try:
            if streaming:
                while True:
                    b = resp.read(1)
                    if not b:
                        break
                    self.wfile.write(b)
                    self.wfile.flush()
            else:
                while True:
                    c = resp.read(65536)
                    if not c:
                        break
                    self.wfile.write(c)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _proxy(self):
        pool, rest = self._route()
        if pool is None:
            self._json(404, {"error": "unknown keypool route"})
            return
        raw = _read_body(self)
        model = _model(raw)
        body_dict = None
        if raw:
            try:
                body_dict = json.loads(raw)
            except Exception:
                body_dict = None
        session = _aff.session_key(self.headers, body_dict)

        # Interactions protocol translation
        want_translate = False
        if pool.protocol == "gemini-interactions":
            try:
                doc = json.loads(raw or b"{}")
                rest = pool.interactions_path
                raw = json.dumps(translate.openai_to_interactions(doc)).encode()
                want_translate = True
            except Exception:
                pass

        tried = []
        while True:
            ks = pool.pick(model, session)
            if ks is None or ks.name in tried:
                self._json(502, {"error": f"keypool '{pool.name}': no healthy key",
                                 "tried": tried})
                return
            tried.append(ks.name)
            t0 = clock.mono()
            try:
                resp = self._forward(pool, rest, raw, ks)
            except urllib.error.HTTPError as e:
                body = e.read(200)
                kind = pool.classify(e.code, body)
                if kind == "switch":
                    pool.on_failure(ks, kind, e.code, e.headers, session)
                    _emit("failover", pool=pool.name, key=ks.name, code=e.code)
                    continue
                pool.on_failure(ks, kind, e.code, e.headers, session)
                self._json(e.code, {"error": f"upstream {e.code}",
                                    "body": body.decode("utf-8", "replace")[:500]})
                return
            except Exception as e:
                pool.on_failure(ks, "soft", 0, None, session)
                self._json(502, {"error": f"upstream {e}"})
                return
            ms = (clock.mono() - t0) * 1000
            pool.on_success(ks, resp.headers, ms)
            if want_translate:
                out = self._serve(resp, transform=translate.interactions_to_openai, model=model)
                _ledger_record(pool.name, ks.name, model, ms, out)
            else:
                self._serve(resp)
                _ledger_record(pool.name, ks.name, model, ms, None)
            return

    do_POST = do_PUT = do_PATCH = do_DELETE = _proxy
