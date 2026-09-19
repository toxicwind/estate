#!/usr/bin/env python3
"""ml-serve — resident ML inference daemon for desktop wallpaper intelligence.

Hot-loaded ONNX segmentation + e621 native tag resolution over HTTP, so
desktop components (Quickshell, wallpaper pipeline) get millisecond
inference instead of cold-starting a process per call.

There is deliberately NO local image tagger: e621 already has maximal tags.
Tag resolution is md5 -> e621 API lookup, cached in a sidecar JSON.

Models (shared cache, never committed to git):
  - SkyTNT anime-seg ISNet (anime subject segmentation) -> /segment

Endpoints (JSON throughout):
  GET  /health    providers, loaded models, e621 cache stats, timings
  POST /segment  {"path": "/abs/img.png"} -> subject bbox/centroid/coverage
  POST /lookup   {"path": "/abs/img.png"} -> md5 + e621 tag_string (cached)
  POST /pick     {"dir": "/abs/dir", ...} -> ranked best pick scored on
                  cached e621 native tags

A background thread re-scans the wallpaper pool every CACHE_INTERVAL_S and
resolves new/changed files against e621 into `.wallpaper-ml-cache.json`
inside the pool dir, so /pick is cache-hot.

Env:
  ML_SERVE_PORT    (default 25180)
  ML_SERVE_POOL    (default ~/Pictures/Wallpapers)
  WPML_CACHE_DIR   (default ~/.cache/quickshell/wallpaper-ml)
  CACHE_INTERVAL_S (default 60)
  FURRY_BOOST      (default 3.0)
  WM_PENALTY       (default 1.5)
  E621_TAGS_FURRY  (default "anthro kemono")
  E621_TAGS_MALE   (default "male")
  E621_TAGS_WM     (default "watermark text")
  E621_USER_AGENT  (default "ml-serve/1.0 (resident wallpaper inference)")
  SEG_INPUT        (default 1024; ISNet native size)
"""

import hashlib
import http.server
import json
import math
import os
import socketserver
import sys
import threading
import time
import urllib.request

IMG_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".avif", ".bmp")


def _env(name, default):
    return os.environ.get(name, default)


def _tagset(name, default):
    return set(_env(name, default).split())


CACHE_DIR = _env("WPML_CACHE_DIR",
                 os.path.join(os.path.expanduser("~"), ".cache",
                              "quickshell", "wallpaper-ml"))
SEG_ONNX = os.path.join(CACHE_DIR, "isnetis.onnx")
POOL_DIR = _env("ML_SERVE_POOL",
                os.path.join(os.path.expanduser("~"), "Pictures", "Wallpapers"))
CACHE_INTERVAL_S = float(_env("CACHE_INTERVAL_S", "60"))
SEG_INPUT = int(_env("SEG_INPUT", "1024"))  # ISNet native size
# Masks sparser than this are sensor noise, not a subject (ISNet is
# anime-trained; on photos it can return a few scattered pixels).
MIN_COVERAGE = float(_env("SEG_MIN_COVERAGE", "0.002"))

FURRY_TAGS = _tagset("E621_TAGS_FURRY", "anthro kemono")
MALE_TAGS = _tagset("E621_TAGS_MALE", "male")
WM_TAGS = _tagset("E621_TAGS_WM", "watermark text")
E621_UA = _env("E621_USER_AGENT",
               "ml-serve/1.0 (resident wallpaper inference)")

# e621 rate limit: max 2 req/s. 0.6s spacing keeps us safely under it.
E621_THROTTLE_S = 0.6
_e621_lock = threading.Lock()
_e621_last = 0.0
E621_STATS = {"lookups": 0, "hits": 0, "misses": 0, "errors": 0}


# ---------------------------------------------------------------- models

class ModelManager:
    """Lazy, hot-after-first-use ONNX session with CUDA->CPU fallback."""

    def __init__(self):
        import onnxruntime as ort
        self._ort = ort
        avail = set(ort.get_available_providers())
        self.pref = [p for p in ("CUDAExecutionProvider", "CPUExecutionProvider")
                     if p in avail] or ["CPUExecutionProvider"]
        self.available_providers = sorted(avail)
        self._sess = None
        self._prov = None
        self._stats = {"loaded": False}
        self._lock = threading.Lock()

    def get(self):
        with self._lock:
            if self._sess is None:
                t0 = time.perf_counter()
                opts = self._ort.SessionOptions()
                opts.log_severity_level = 3
                self._sess = self._ort.InferenceSession(
                    SEG_ONNX, sess_options=opts, providers=self.pref)
                self._prov = self._sess.get_providers()[0]
                self._stats = {
                    "loaded": True,
                    "provider": self._prov,
                    "load_ms": round((time.perf_counter() - t0) * 1000, 1),
                    "inferences": 0,
                    "total_ms": 0.0,
                }
            return self._sess, self._prov

    def record(self, ms):
        self._stats["inferences"] += 1
        self._stats["total_ms"] += ms

    def stats(self):
        d = dict(self._stats)
        n = d.get("inferences", 0)
        d["avg_ms"] = round(d["total_ms"] / n, 1) if n else 0.0
        d.pop("total_ms", None)
        return d


MODELS = None  # set in main()


def segment_image(path):
    """ISNet anime segmentation -> subject bbox/centroid/coverage (orig px)."""
    from PIL import Image
    import numpy as np

    t0 = time.perf_counter()
    sess, prov = MODELS.get()
    img = Image.open(path).convert("RGB")
    w, h = img.size
    rs = img.resize((SEG_INPUT, SEG_INPUT), Image.BICUBIC)
    arr = np.asarray(rs, dtype=np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    arr = (arr - mean) / std
    arr = np.transpose(arr, (2, 0, 1))[None, ...]
    out = sess.run(None, {sess.get_inputs()[0].name: arr})[0][0, 0]
    # NOTE: this export emits an already-sigmoided probability map in [0,1]
    # (verified: raw max ~0.008 on background-only input). Do NOT apply
    # sigmoid here — it would push every value above 0.5.
    mask = out > 0.5
    ms = (time.perf_counter() - t0) * 1000
    MODELS.record(ms)

    if not mask.any() or float(mask.mean()) < MIN_COVERAGE:
        return {"bbox": None, "centroid": None, "coverage": 0.0,
                "ms": round(ms, 1), "provider": prov}
    ys, xs = np.nonzero(mask)
    sx, sy = w / SEG_INPUT, h / SEG_INPUT
    x0, x1 = int(xs.min() * sx), int(xs.max() * sx)
    y0, y1 = int(ys.min() * sy), int(ys.max() * sy)
    return {"bbox": [x0, y0, x1, y1],
            "centroid": [int(xs.mean() * sx), int(ys.mean() * sy)],
            "coverage": round(float(mask.mean()), 4),
            "ms": round(ms, 1), "provider": prov}


# ------------------------------------------------------- e621 tag lookup

def file_md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def e621_lookup_md5(md5):
    """Resolve an md5 against e621's native tags. Returns (tags, source).

    tags is a sorted list of native e621 tag strings, or None when the
    file is not on e621. Throttled to respect e621's 2 req/s limit.
    """
    global _e621_last
    with _e621_lock:
        wait = E621_THROTTLE_S - (time.time() - _e621_last)
        if wait > 0:
            # in-process wait; no sleep binary involved
            threading.Event().wait(wait)
        _e621_last = time.time()
        E621_STATS["lookups"] += 1
    url = "https://e621.net/posts.json?tags=md5:" + md5 + "&limit=1"
    req = urllib.request.Request(url, headers={"User-Agent": E621_UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        E621_STATS["errors"] += 1
        return None, "error"
    posts = data.get("posts") or []
    if not posts:
        E621_STATS["misses"] += 1
        return None, "miss"
    E621_STATS["hits"] += 1
    tagmap = posts[0].get("tags") or {}
    tags = sorted({t for cat in tagmap.values() if isinstance(cat, list)
                   for t in cat})
    return tags, "e621"


# ------------------------------------------------------------- tag cache

CACHE_LOCK = threading.Lock()


def _sidecar_path(pool):
    return os.path.join(pool, ".wallpaper-ml-cache.json")


def load_cache(pool):
    p = _sidecar_path(pool)
    try:
        with open(p) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_cache(pool, cache):
    tmp = _sidecar_path(pool) + ".tmp"
    with open(tmp, "w") as f:
        json.dump(cache, f)
    os.replace(tmp, _sidecar_path(pool))


def image_size(path):
    from PIL import Image
    with Image.open(path) as img:
        return img.size  # (w, h)


def ensure_tags(path, pool):
    """Return cache entry for path, resolving via e621 on demand.

    Entry schema: {"mtime","size","w","h","md5","tag_string":[...],
                   "source":"e621"|"miss"|"error","ms"}.
    tag_string is None when the file is not on e621.
    """
    name = os.path.basename(path)
    try:
        st = os.stat(path)
    except OSError:
        return None
    with CACHE_LOCK:
        cache = load_cache(pool)
        ent = cache.get(name)
        if ent and ent.get("mtime") == st.st_mtime \
                and ent.get("size") == st.st_size:
            return ent
    t0 = time.perf_counter()
    try:
        w, h = image_size(path)
        md5 = file_md5(path)
    except Exception:
        return None
    tags, source = e621_lookup_md5(md5)
    ent = {"mtime": st.st_mtime, "size": st.st_size, "w": w, "h": h,
           "md5": md5, "tag_string": tags, "source": source,
           "ms": round((time.perf_counter() - t0) * 1000, 1)}
    with CACHE_LOCK:
        cache = load_cache(pool)
        cache[name] = ent
        save_cache(pool, cache)
    return ent


def scan_pool(pool):
    """Resolve every new/changed image in pool dir against e621."""
    resolved, skipped = 0, 0
    try:
        files = sorted(os.listdir(pool))
    except OSError:
        return 0, 0
    for name in files:
        if not name.lower().endswith(IMG_EXTS):
            continue
        ent = ensure_tags(os.path.join(pool, name), pool)
        if ent:
            resolved += 1
        else:
            skipped += 1
    return resolved, skipped


def cache_daemon():
    while True:
        try:
            scan_pool(POOL_DIR)
        except Exception:
            pass
        threading.Event().wait(CACHE_INTERVAL_S)


# ----------------------------------------------------------------- pick

def score_entry(ent, furry_boost, wm_penalty, target_aspect):
    """Score from native e621 tags (binary present/absent).

    score = aspect_term + upscale - boost*furry*male - penalty*watermark.
    Lower wins. Entries with no e621 tags score on geometry alone.
    """
    tags = set(ent.get("tag_string") or [])
    w, h = ent.get("w", 0), ent.get("h", 0)
    furry = 1.0 if tags & FURRY_TAGS else 0.0
    male = 1.0 if tags & MALE_TAGS else 0.0
    wm = 1.0 if tags & WM_TAGS else 0.0
    aspect_term = 0.0
    if target_aspect and w and h:
        aspect_term = abs(math.log((w / h) / target_aspect))
    upscale = 2.0 if (w * h < 1_000_000) else 0.0
    score = aspect_term + upscale - furry_boost * furry * male \
        - wm_penalty * wm
    return score, furry, male, wm


# ------------------------------------------------------------------ http

class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "ml-serve/2.0"

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
        except ValueError:
            n = 0
        if n <= 0 or n > 10_000_000:
            return {}
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            return {}

    def do_GET(self):
        if self.path == "/health":
            cache = load_cache(POOL_DIR)
            self._json({
                "ok": True,
                "providers_available": MODELS.available_providers,
                "provider_preference": MODELS.pref,
                "models": {"seg": MODELS.stats()},
                "tag_source": "e621 native tags (md5 lookup, cached)",
                "e621": dict(E621_STATS, cached=len(cache)),
                "pool": POOL_DIR,
                "pool_cached": len(cache),
                "cache_interval_s": CACHE_INTERVAL_S,
            })
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        data = self._body()
        try:
            if self.path == "/segment":
                path = data.get("path", "")
                if not path or not os.path.isfile(path):
                    return self._json({"error": "path missing/not a file"}, 400)
                res = segment_image(path)
                res["path"] = path
                self._json(res)
            elif self.path == "/lookup":
                path = data.get("path", "")
                if not path or not os.path.isfile(path):
                    return self._json({"error": "path missing/not a file"}, 400)
                pool = os.path.dirname(os.path.abspath(path)) or POOL_DIR
                ent = ensure_tags(path, pool)
                if not ent:
                    return self._json({"error": "could not read file"}, 400)
                self._json({"path": path, "md5": ent["md5"],
                            "tag_string": ent["tag_string"],
                            "source": ent["source"], "ms": ent["ms"]})
            elif self.path == "/pick":
                pool = data.get("dir") or POOL_DIR
                furry_boost = float(data.get("furry_boost",
                                            _env("FURRY_BOOST", "3.0")))
                wm_penalty = float(data.get("wm_penalty",
                                            _env("WM_PENALTY", "1.5")))
                ta = data.get("target_aspect")
                target_aspect = float(ta) if ta else 0.0
                t0 = time.perf_counter()
                best, scored = None, []
                try:
                    files = sorted(os.listdir(pool))
                except OSError:
                    return self._json({"error": "dir not readable"}, 400)
                for name in files:
                    if not name.lower().endswith(IMG_EXTS):
                        continue
                    ent = ensure_tags(os.path.join(pool, name), pool)
                    if not ent:
                        continue
                    s, furry, male, wm = score_entry(
                        ent, furry_boost, wm_penalty, target_aspect)
                    scored.append((s, name, ent, furry, male, wm))
                scored.sort(key=lambda x: x[0])
                if scored:
                    s, name, ent, furry, male, wm = scored[0]
                    tags = ent.get("tag_string") or []
                    best = {"path": os.path.join(pool, name),
                            "score": round(s, 3),
                            "furry": furry, "male": male,
                            "watermark": wm,
                            "tag_source": ent.get("source"),
                            "matched_tags": sorted(
                                (set(tags) & (FURRY_TAGS | MALE_TAGS | WM_TAGS))),
                            "tag_count": len(tags)}
                self._json({"best": best,
                            "candidates": len(scored),
                            "ms": round((time.perf_counter() - t0) * 1000, 1)})
            else:
                self._json({"error": "not found"}, 404)
        except FileNotFoundError as e:
            self._json({"error": "model missing: %s" % e.filename}, 503)
        except Exception as e:
            self._json({"error": "%s: %s" % (type(e).__name__, e)}, 500)

    def log_message(self, fmt, *args):
        sys.stderr.write("ml-serve %s %s\n" %
                         (self.address_string(), fmt % args))


class ThreadedServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    global MODELS
    port = int(_env("ML_SERVE_PORT", "25180"))
    if not os.path.isfile(SEG_ONNX):
        sys.stderr.write("ml-serve: missing model file: %s\n" % SEG_ONNX)
        sys.exit(2)
    MODELS = ModelManager()
    threading.Thread(target=cache_daemon, name="cache-daemon",
                     daemon=True).start()
    srv = ThreadedServer(("127.0.0.1", port), Handler)
    sys.stderr.write("ml-serve: listening on 127.0.0.1:%d pool=%s "
                     "tags=e621\n" % (port, POOL_DIR))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
