#!/usr/bin/env python3
"""forensics-srv: persistent internal forensics HTTP server on awrawr-pc.

Exposes the refusal-hunt forensics pipeline as a service:
  (1) parquet ingest/query via pyarrow
  (2) tiktoken cl100k_base encode/count
  (3) refusal/sorry anomaly ledger reads
  (4) trigger-token census

Internal only: binds 127.0.0.1, bearer-token auth (token in .token, 0600).
Managed by pitchfork as sovereign/forensics-srv (retry, boot_start).
Stdlib HTTP server; pyarrow + tiktoken from the venv.
"""
import base64
import hashlib
import json
import os
import re
import secrets
import sys
import threading
import time
import unicodedata
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORE_DIR = os.path.join(BASE_DIR, "store")
TOKEN_FILE = os.path.join(BASE_DIR, ".token")
VERSION = "1.0.0"
PORT = int(os.environ.get("FORENSICS_SRV_PORT", "25160"))
MAX_BODY = 64 * 1024 * 1024  # 64 MiB (parquet ingest)

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

# tiktoken is the tokenizer of record (cl100k_base). Lazy: the BPE blob is
# cached in the venv dir so the server never touches the network at runtime.
_ENC = None


def get_encoding():
    global _ENC
    if _ENC is None:
        import tiktoken

        os.environ.setdefault(
            "TIKTOKEN_CACHE_DIR", os.path.join(BASE_DIR, "tiktoken-cache")
        )
        _ENC = tiktoken.get_encoding("cl100k_base")
    return _ENC


# ---------------------------------------------------------------------------
# Trigger-token census (borrowed from refusal-hunt/bin/banned_token_check.py)
# ---------------------------------------------------------------------------
_ZW = dict.fromkeys(map(ord, "\u200b\u200c\u200d\ufeff\u2060\u00ad\u200e\u200f"))
_SORRY_RE = re.compile(r"\bsorry\b", re.IGNORECASE)
# Known canned-refusal body digests (refusal-sigs.json): 384-char system
# variant and 96-char assistant variant. Classified by digest, never quoted.
_DIGEST_TOKENS = {
    "refusal_digest_384": "b4aefd29108f232f9c0d5a4b030215c1",
    "refusal_digest_96": "582bcbd080daeb3f826c45ed4a83b265",
}


def canonicalize(text):
    try:
        norm = get_encoding().decode(get_encoding().encode(text))
    except Exception:
        norm = unicodedata.normalize("NFKC", text)
    return norm.translate(_ZW)


def census_text(text):
    norm = canonicalize(text)
    counts = {"sorry": len(_SORRY_RE.findall(norm))}
    # whitespace-smuggling pass: "s o r r y" collapses back to the token
    collapsed = re.sub(r"\s+", "", norm)
    counts["sorry_smuggled"] = max(
        0, len(_SORRY_RE.findall(collapsed)) - counts["sorry"]
    )
    low = norm.lower()
    for name, digest in _DIGEST_TOKENS.items():
        counts[name] = low.count(digest)
    return counts


# ---------------------------------------------------------------------------
# Store helpers
# ---------------------------------------------------------------------------
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.\-]{0,63}$")


def dataset_path(name):
    if not _NAME_RE.match(name or ""):
        raise ValueError("bad dataset name")
    return os.path.join(STORE_DIR, name + ".parquet")


def dataset_info(path):
    st = os.stat(path)
    pf = pq.ParquetFile(path)
    return {
        "name": os.path.basename(path)[:-8],
        "rows": pf.metadata.num_rows,
        "columns": pf.schema.names,
        "bytes": st.st_size,
        "mtime": st.st_mtime,
    }


def list_datasets():
    out = []
    if os.path.isdir(STORE_DIR):
        for fn in sorted(os.listdir(STORE_DIR)):
            if fn.endswith(".parquet"):
                try:
                    out.append(dataset_info(os.path.join(STORE_DIR, fn)))
                except Exception:
                    pass
    return out


_PRED_OPS = {
    "eq": pc.equal,
    "ne": pc.not_equal,
    "gt": pc.greater,
    "ge": pc.greater_equal,
    "lt": pc.less,
    "le": pc.less_equal,
}


def apply_predicates(table, predicates):
    if not predicates:
        return table
    mask = None
    for pred in predicates:
        col = pred["col"]
        op = pred["op"]
        value = pred.get("value")
        arr = table.column(col)
        if op in _PRED_OPS:
            m = _PRED_OPS[op](arr, value)
        elif op == "contains":
            m = pc.match_substring(arr.cast(pa.string()), str(value))
        elif op == "startswith":
            m = pc.starts_with(arr.cast(pa.string()), str(value))
        elif op == "is_null":
            m = pc.is_null(arr)
        elif op == "not_null":
            m = pc.is_valid(arr)
        else:
            raise ValueError("unknown predicate op: %r" % (op,))
        m = pc.fill_null(m, False)
        mask = m if mask is None else pc.and_(mask, m)
    return table.filter(mask)


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------
START_TIME = time.time()
BEARER = None


def load_bearer():
    global BEARER
    try:
        with open(TOKEN_FILE) as f:
            BEARER = f.read().strip()
    except FileNotFoundError:
        BEARER = None


class Handler(BaseHTTPRequestHandler):
    server_version = "forensics-srv/" + VERSION

    def log_message(self, fmt, *args):
        sys.stderr.write(
            "%s %s %s\n"
            % (time.strftime("%Y-%m-%dT%H:%M:%S"), self.command, self.path)
        )

    def _send(self, status, obj):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY:
            raise ValueError("bad content length: %d" % length)
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8")) if raw else {}

    def _auth_ok(self):
        if not BEARER:
            return False
        auth = self.headers.get("Authorization") or ""
        if not auth.startswith("Bearer "):
            return False
        return secrets.compare_digest(auth[7:].strip(), BEARER)

    def do_GET(self):
        t0 = time.perf_counter()
        if self.path == "/health":
            enc_ok = True
            try:
                get_encoding()
            except Exception:
                enc_ok = False
            self._send(
                200,
                {
                    "ok": True,
                    "version": VERSION,
                    "uptime_s": round(time.time() - START_TIME, 3),
                    "pyarrow": pa.__version__,
                    "tiktoken_cl100k_base": enc_ok,
                    "datasets": len(list_datasets()),
                    "took_ms": round((time.perf_counter() - t0) * 1000, 3),
                },
            )
        elif self.path == "/parquet/list":
            if not self._auth_ok():
                return self._send(401, {"error": "unauthorized"})
            self._send(
                200,
                {
                    "datasets": list_datasets(),
                    "took_ms": round((time.perf_counter() - t0) * 1000, 3),
                },
            )
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        t0 = time.perf_counter()
        if self.path != "/health" and not self._auth_ok():
            return self._send(401, {"error": "unauthorized"})
        try:
            req = self._read_json()
        except Exception as e:
            return self._send(400, {"error": "bad request: %s" % e})

        def done(obj, status=200):
            obj["took_ms"] = round((time.perf_counter() - t0) * 1000, 3)
            self._send(status, obj)

        try:
            if self.path == "/tokens/count":
                text = req.get("text", "")
                n = len(get_encoding().encode(text))
                return done({"chars": len(text), "tokens": n})

            if self.path == "/tokens/encode":
                text = req.get("text", "")
                max_ids = int(req.get("max_ids", 2000))
                ids = get_encoding().encode(text)
                return done(
                    {
                        "count": len(ids),
                        "token_ids": ids[:max_ids],
                        "truncated": len(ids) > max_ids,
                    }
                )

            if self.path == "/parquet/ingest":
                name = req.get("name", "")
                data = base64.b64decode(req.get("data_b64", ""))
                path = dataset_path(name)
                tmp = path + ".tmp"
                with open(tmp, "wb") as f:
                    f.write(data)
                # validate by reading back through pyarrow
                table = pq.read_table(tmp)
                os.replace(tmp, path)
                return done(
                    {
                        "name": name,
                        "rows": table.num_rows,
                        "columns": table.schema.names,
                        "bytes": len(data),
                    }
                )

            if self.path == "/parquet/query":
                name = req.get("name", "")
                table = pq.read_table(dataset_path(name))
                total = table.num_rows
                table = apply_predicates(table, req.get("predicates"))
                cols = req.get("columns")
                if cols:
                    table = table.select(cols)
                offset = int(req.get("offset", 0) or 0)
                limit = req.get("limit", 100)
                limit = 1000 if limit is None else min(int(limit), 10000)
                if offset:
                    table = table.slice(offset)
                table = table.slice(0, limit)
                return done(
                    {
                        "name": name,
                        "rows": table.to_pylist(),
                        "returned": table.num_rows,
                        "total_rows": total,
                    }
                )

            if self.path == "/ledger/read":
                # refusal/sorry anomaly ledger: ingested as dataset
                # "anomalies", with LEDGER_PATH env fallback.
                path = None
                try:
                    path = dataset_path("anomalies")
                    if not os.path.exists(path):
                        path = None
                except ValueError:
                    path = None
                env_path = os.environ.get("LEDGER_PATH")
                if path is None and env_path and os.path.exists(env_path):
                    path = env_path
                if path is None or not os.path.exists(path):
                    return done(
                        {
                            "error": "anomaly ledger not ingested "
                            "(POST /parquet/ingest name=anomalies)"
                        },
                        404,
                    )
                table = pq.read_table(path)
                total = table.num_rows
                cols = req.get("columns")
                if cols:
                    table = table.select(cols)
                limit = min(int(req.get("limit", 100) or 100), 10000)
                return done(
                    {
                        "source": path,
                        "rows": table.slice(0, limit).to_pylist(),
                        "returned": min(limit, total),
                        "total_rows": total,
                        "columns": pq.read_schema(path).names,
                    }
                )

            if self.path == "/census/trigger-tokens":
                if "text" in req:
                    text = req["text"]
                elif "dataset" in req and "column" in req:
                    table = pq.read_table(
                        dataset_path(req["dataset"])
                    ).select([req["column"]])
                    limit = min(int(req.get("limit", 100000)), 1000000)
                    col = table.column(req["column"]).slice(0, limit)
                    text = "\n".join(
                        str(v) for v in col.to_pylist() if v is not None
                    )
                else:
                    return done(
                        {"error": "need 'text' or 'dataset'+'column'"}, 400
                    )
                counts = census_text(text)
                return done(
                    {
                        "counts": counts,
                        "chars": len(text),
                        "tokens": len(get_encoding().encode(text)),
                    }
                )

            return done({"error": "not found"}, 404)
        except FileNotFoundError as e:
            return done({"error": "not found: %s" % e}, 404)
        except ValueError as e:
            return done({"error": str(e)}, 400)
        except Exception as e:
            return done(
                {"error": "%s: %s" % (type(e).__name__, e)}, 500
            )


def main():
    os.makedirs(STORE_DIR, exist_ok=True)
    load_bearer()
    if not BEARER:
        sys.stderr.write("FATAL: %s missing; create it first\n" % TOKEN_FILE)
        sys.exit(2)
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    srv.daemon_threads = True
    sys.stderr.write(
        "forensics-srv %s listening on 127.0.0.1:%d\n" % (VERSION, PORT)
    )
    srv.serve_forever()


if __name__ == "__main__":
    main()
