#!/usr/bin/env python3
"""herd-keypool — API key-pool rotation proxy for herd cloud peers.

Listens on 127.0.0.1:25109 (override with KEYPOOL_HOST / KEYPOOL_PORT env). Path-routed: /<pool>/... forwards to the
pool's upstream with a HEALTH-CHECKED key picked first-valid-wins per call.

  GET/POST /openrouter/v1/chat/completions -> https://openrouter.ai/api/v1/chat/completions
  GET/POST /gemini/v1/chat/completions    -> https://generativelanguage.googleapis.com/v1beta/openai/v1/chat/completions

Pool config: config/keypools.yaml. Key VALUES live only in
/home/toxic/.secrets (parsed at startup + on SIGHUP, never logged, never
returned by any endpoint). Only key NAMES, health states, latencies and
value fingerprints appear in /status and the audit log.

Health model (Chris 2026-09-20):
  - A 401/402/429 on one key is a ROUTING SIGNAL, not a death certificate
    and never a config rewrite: the key is parked for a cooldown, the
    request fails over to the next key, and the parked key revalidates
    on demand (cheap probe, e.g. OpenRouter /v1/auth/key) the moment it
    becomes eligible again. A recovered key rejoins automatically.
  - Cheap probes first: a key whose health is unknown is probed with the
    pool's health endpoint (fast, no spend) before it carries traffic.
  - Fail-fast: probes and failover attempts use short timeouts; the first
    valid key wins per call.
  - Racing (KEYPOOL_RACE_KEYS=N, default 1): with N>1 the top-N eligible
    keys are attempted CONCURRENTLY and the first valid (2xx) wins — the
    hedged-request answer to a degraded-but-not-dead first key serializing
    the tail. Losers are abandoned and their connections closed best-effort
    (urllib blocking calls can't be force-cancelled; in-flight losers
    self-close on completion once the race is decided). A 401/402/429
    on any contestant still parks just that key (routing signal, as above);
    a non-routing error is forwarded immediately, exactly as in sequential
    mode; a lone timeout just loses the race (no state change). N=1 keeps
    the historical sequential pick-then-failover loop unchanged.

Env:
  KEYPOOL_RACE_KEYS   keys raced per call (default 1 = sequential)
  KEYPOOL_PORT        listen port (default 25109; set to e.g. 25110 for a
                      sidecar test instance without touching the live daemon)

Endpoints:
  /health  -> 200 {"ok": true}
  /status  -> per-pool key states (names, states, latency_ms, fingerprint,
              last_error_class, recover_in_s) plus race_keys. NO key values, ever.

Audit: every select/failover/recovery appends one JSON line to
  /home/toxic/sovereign/data/keypool-audit.jsonl
(key names + fingerprints only). Rotated at KEYPOOL_AUDIT_MAX_BYTES (10MB).

Run under pitchfork as sovereign/keypool. Stdlib only.
"""
import hashlib
import json
import os
import re
import signal
import sys
import threading
import time
import urllib.request
import urllib.error
import queue
from concurrent import futures
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LISTEN = (
    __import__("os").environ.get("KEYPOOL_HOST", "127.0.0.1"),
    int(__import__("os").environ.get("KEYPOOL_PORT", "25109")),
)
POOLS_PATH = os.environ.get(
    "KEYPOOLS_CONFIG",
    "/home/toxic/sovereign/config/keypools.yaml",
)
SECRETS_PATH = os.environ.get("KEYPOOL_SECRETS", "/home/toxic/.secrets")
AUDIT_PATH = os.environ.get(
    "KEYPOOL_AUDIT",
    "/home/toxic/sovereign/data/keypool-audit.jsonl",
)
AUDIT_MAX_BYTES = int(os.environ.get("KEYPOOL_AUDIT_MAX_BYTES", 10_000_000))
# RACING (edge-additions 2026-09-20): how many top eligible keys to race
# concurrently per call. "1" (default) = today's sequential pick-then-failover,
# bit-for-bit. "2"+ = first-valid-wins across the top-N keys (hedged-request
# lineage: Dean & Barroso; TailSieve tail-isolation). Roll out by setting
# KEYPOOL_RACE_KEYS=2 in the pitchfork unit env; the default changes nothing.
RACE_KEYS = max(1, int(os.environ.get("KEYPOOL_RACE_KEYS", "1")))

HOP_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade",
}
# Strip any caller-supplied auth: the pool injects the chosen key itself.
REQ_STRIP_HEADERS = HOP_HEADERS | {
    "content-length", "host", "authorization", "x-api-key", "x-goog-api-key",
}


def log(msg):
    print(f"[keypool] {msg}", file=sys.stderr, flush=True)


def fingerprint(value):
    """Non-reversible label for a key value. Safe to show in /status."""
    return hashlib.sha256(value.encode()).hexdigest()[:12]


def _is_free_model(model_id):
    """True only for OpenRouter free-model IDs. This gates a free-ONLY key
    (what the key may serve), never what any key must serve."""
    return bool(model_id) and (
        model_id == "openrouter/free" or model_id.endswith(":free"))


def _extract_model(raw):
    """Best-effort model ID from a proxied JSON body. None when absent."""
    try:
        if raw:
            doc = json.loads(raw)
            m = doc.get("model") if isinstance(doc, dict) else None
            if isinstance(m, str) and m:
                return m
    except Exception:
        pass
    return None



# ------------------------------------------ OpenAI-compat request adaptation
# Borrowed from tau provider compat layer
# (projects/tau/engine/docs/provider-compat-reference.md). Tau documents
# per-provider wire rules for OpenAI-compatible hosts; the keypool applies the
# request-shaping subset here so callers can send neutral OpenAI bodies and get
# correct wire format per upstream.
#
# Borrowed mapping (tau flag -> keypool behavior):
# - maxTokensField: "max_tokens" for Mistral/native Moonshot/Z.AI/Fireworks/
#   direct DeepSeek, else "max_completion_tokens". Our upstreams need NO rename:
#   openrouter.ai accepts both fields; the Google OpenAI-compat endpoint
#   accepts max_tokens. Documented here, deliberately not transformed -- a
#   rename would risk breaking callers for zero observed benefit.
# - supportsSamplingParams=false for the o1/o3/gpt-5+ class: those hosts 400
#   when temperature/top_p/penalties are present -> stripped below.
# - supportsStore=false for Mistral: omit "store". (The mistral peer in
#   herd.yaml proxies DIRECTLY to api.mistral.ai, not through the keypool, so
#   this is documented for completeness, not implemented here.)
# - Reasoning-first families need token headroom: the budget is consumed by
#   reasoning tokens BEFORE visible content. A tiny max_tokens reads as
#   200-empty (proven live 2026-09-20: ling-fin at max_tokens=100 -> 91
#   reasoning tokens, 0 content; at 2000 -> exact output). Floor applied below.

_REASONING_FIRST_SUBSTR = (
    "ling-3.0-flash",        # inclusionai ling family (reasoning-first)
    "nemotron-3-nano-omni",  # nvidia nano-omni reasoning variant
    "north-mini-code",       # cohere north-mini-code (reasoning model)
    "dots-3-note",           # dots-studio note preview
    "lfm-2.5",              # liquid lfm-2.5
)
_REASONING_TOKEN_FLOOR = 512

_NO_SAMPLING_RE = re.compile(r"(^|/)(o1|o3|gpt-5)(" + chr(92) + "b|[-.])")
_SAMPLING_FIELDS = ("temperature", "top_p", "frequency_penalty", "presence_penalty")


def _apply_openai_compat(pool_name, model_id, raw):
    """Adapt a neutral OpenAI request body to the upstream wire rules.

    Returns the (possibly rewritten) raw bytes. Never raises: on any doubt
    the body passes through untouched, so this is strictly safer than raw
    proxying."""
    if not raw or not model_id:
        return raw
    try:
        doc = json.loads(raw)
    except Exception:
        return raw
    if not isinstance(doc, dict) or "messages" not in doc:
        return raw  # not a chat-completions body; leave alone
    changed = False
    mlow = model_id.lower()
    # 1. reasoning-first token floor
    if any(sub in mlow for sub in _REASONING_FIRST_SUBSTR):
        mt = doc.get("max_tokens")
        if isinstance(mt, int) and mt < _REASONING_TOKEN_FLOOR:
            doc["max_tokens"] = _REASONING_TOKEN_FLOOR
            changed = True
        else:
            mt = doc.get("max_completion_tokens")
            if isinstance(mt, int) and mt < _REASONING_TOKEN_FLOOR:
                doc["max_completion_tokens"] = _REASONING_TOKEN_FLOOR
                changed = True
    # 2. strip sampling params for the o1/o3/gpt-5+ class
    if _NO_SAMPLING_RE.search(mlow):
        for f in _SAMPLING_FIELDS:
            if f in doc:
                del doc[f]
                changed = True
    if not changed:
        return raw
    try:
        return json.dumps(doc, separators=(",", ":")).encode()
    except Exception:
        return raw

# ------------------------------------------------------------------ config

def _strip_comment(raw):
    out, quote, i = [], None, 0
    while i < len(raw):
        c = raw[i]
        if quote:
            out.append(c)
            if c == "\\" and i + 1 < len(raw):
                out.append(raw[i + 1]); i += 1
            elif c == quote:
                quote = None
        elif c in "\"'":
            quote, out = c, out + [c]
        elif c == "#":
            break
        else:
            out.append(c)
        i += 1
    return "".join(out).rstrip()


def _parse_simple_yaml(text):
    lines = [l for l in (_strip_comment(r) for r in text.splitlines()) if l.strip()]

    def indent_of(s):
        return len(s) - len(s.lstrip(" "))

    def scalar(v):
        v = v.strip()
        if v in ("true", "True"): return True
        if v in ("false", "False"): return False
        if v in ("null", "~", ""): return None
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'": return v[1:-1]
        if len(v) >= 2 and v[0] == "[" and v[-1] == "]":
            inner = v[1:-1].strip()
            if not inner: return []
            items, cur, quote = [], "", None
            for c in inner + ",":
                if quote:
                    cur += c
                    if c == quote: quote = None
                elif c in "\"'":
                    quote, cur = c, cur + c
                elif c == ",":
                    items.append(scalar(cur)); cur = ""
                else:
                    cur += c
            return items
        if len(v) >= 2 and v[0] == "{" and v[-1] == "}":
            inner = v[1:-1].strip()
            if not inner: return {}
            d, cur, quote, pairs = {}, "", None, []
            for c in inner + ",":
                if quote:
                    cur += c
                    if c == quote: quote = None
                elif c in "\"'":
                    quote, cur = c, cur + c
                elif c == ",":
                    pairs.append(cur); cur = ""
                else:
                    cur += c
            for p in pairs:
                if ":" in p:
                    k, vv = p.split(":", 1)
                    d[scalar(k)] = scalar(vv)
            return d
        try: return int(v)
        except ValueError: pass
        try: return float(v)
        except ValueError: pass
        return v

    pos = [0]

    def parse_block(min_indent):
        items = None
        while pos[0] < len(lines):
            line = lines[pos[0]]
            ind = indent_of(line)
            if ind < min_indent: break
            stripped = line.strip()
            if stripped.startswith("- "):
                if items is None: items = []
                if not isinstance(items, list): raise ValueError("mixed list/map")
                pos[0] += 1
                rest = stripped[2:].strip()
                if not rest:
                    items.append(parse_block(ind + 1))
                elif ":" in rest and not rest.startswith(("[", "{")):
                    k, v = rest.split(":", 1)
                    d = {}
                    if v.strip(): d[k.strip()] = scalar(v)
                    else: d[k.strip()] = parse_block(ind + 1)
                    while pos[0] < len(lines):
                        nline = lines[pos[0]]
                        nind = indent_of(nline)
                        if nind <= ind or nline.strip().startswith("- "): break
                        if ":" not in nline:
                            pos[0] += 1; continue
                        nk, nv = nline.strip().split(":", 1)
                        pos[0] += 1
                        if nv.strip(): d[nk.strip()] = scalar(nv)
                        else: d[nk.strip()] = parse_block(nind + 1)
                    items.append(d)
                else:
                    items.append(scalar(rest))
            elif ":" in stripped:
                if items is None: items = {}
                if not isinstance(items, dict): raise ValueError("mixed map/list")
                k, v = stripped.split(":", 1)
                pos[0] += 1
                if v.strip(): items[k.strip()] = scalar(v)
                else:
                    if pos[0] < len(lines) and indent_of(lines[pos[0]]) > ind:
                        items[k.strip()] = parse_block(indent_of(lines[pos[0]]))
                    else:
                        items[k.strip()] = None
            else:
                pos[0] += 1
        return items if items is not None else {}

    return parse_block(0)


def load_secrets(path):
    """Parse `export NAME=value` / `NAME=value` lines. Returns {NAME: value}."""
    vals = {}
    try:
        with open(path) as f:
            for raw in f:
                line = raw.strip()
                if line.startswith("export "):
                    line = line[len("export "):]
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, val = line.split("=", 1)
                name, val = name.strip(), val.strip()
                if (len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'"):
                    val = val[1:-1]
                if name:
                    vals[name] = val
    except OSError as e:
        log(f"secrets read failed: {e}")
    return vals


class KeyState:
    __slots__ = ("name", "value", "fp", "state", "latency_ms",
                 "last_error", "down_until", "last_probe_ok", "free_only")

    def __init__(self, name, value, free_only=False):
        self.name = name
        self.value = value
        self.free_only = bool(free_only)
        self.fp = fingerprint(value)
        self.state = "unknown"   # unknown | healthy | down
        self.latency_ms = None
        self.last_error = None
        self.down_until = 0.0
        self.last_probe_ok = False


class Pool:
    def __init__(self, name, cfg, secrets):
        self.name = name
        self.upstream = cfg["upstream"].rstrip("/")
        self.health_method = (cfg.get("health") or {}).get("method", "GET")
        self.health_path = (cfg.get("health") or {}).get("path", "/v1/auth/key")
        self.health_ok = set((cfg.get("health") or {}).get("ok", [200]))
        self.fail_status = set(cfg.get("fail_status", [401, 402, 429]))
        self.probe_timeout = float(cfg.get("probe_timeout", 5))
        self.request_timeout = float(cfg.get("request_timeout", 120))
        cd = cfg.get("cooldown") or {}
        self.cooldown = {
            401: float(cd.get(401, cd.get("401", 300))),
            402: float(cd.get(402, cd.get("402", 300))),
            429: float(cd.get(429, cd.get("429", 60))),
        }
        self.cooldown_default = float(cd.get("default", 120))
        self.keys = []
        for kspec in cfg.get("keys") or []:
            # entry: plain name, or {name: ..., free_only: true}.
            # A free_only key may serve ONLY free-model requests.
            if isinstance(kspec, dict):
                kname, free_only = kspec.get("name"), bool(kspec.get("free_only"))
            else:
                kname, free_only = kspec, False
            val = secrets.get(kname) if isinstance(kname, str) else None
            if val:
                self.keys.append(KeyState(kname, val, free_only))
            else:
                log(f"pool {name}: key {kname} not in secrets — skipped (names only)")
        self.lock = threading.Lock()
        # Racing telemetry for the KEYPOOL_RACE_KEYS>1 path. Updated only via
        # _race_record() under self.lock; surfaced read-only in /status.
        self.race_stats = {"races": 0, "wins": 0, "failed": 0}

    # ------------------------------------------------------------ probing

    def _health_probe(self, ks):
        """Cheap probe: returns (ok, latency_ms, status_or_err)."""
        url = self.upstream + self.health_path
        req = urllib.request.Request(url, method=self.health_method)
        req.add_header("Authorization", "Bearer " + ks.value)
        t0 = time.monotonic()
        try:
            resp = urllib.request.urlopen(req, timeout=self.probe_timeout)
            ms = (time.monotonic() - t0) * 1000
            return resp.status in self.health_ok, ms, resp.status
        except urllib.error.HTTPError as e:
            ms = (time.monotonic() - t0) * 1000
            return e.code in self.health_ok, ms, e.code
        except Exception as e:
            ms = (time.monotonic() - t0) * 1000
            return False, ms, type(e).__name__

    def _audit(self, event, ks, detail=None):
        try:
            d = os.path.dirname(AUDIT_PATH)
            if d:
                os.makedirs(d, exist_ok=True)
            try:
                if os.path.getsize(AUDIT_PATH) >= AUDIT_MAX_BYTES:
                    os.replace(AUDIT_PATH, AUDIT_PATH + ".1")
            except FileNotFoundError:
                pass
            rec = {"ts": time.time(), "pool": self.name, "key": ks.name,
                   "fp": ks.fp, "event": event}
            if detail is not None:
                rec["detail"] = detail
            with open(AUDIT_PATH, "a") as f:
                f.write(json.dumps(rec) + "\n")
        except OSError as e:
            log(f"audit write failed: {e}")

    def _probe_and_update(self, ks):
        ok, ms, status = self._health_probe(ks)
        with self.lock:
            ks.latency_ms = round(ms, 1)
            if ok:
                was = ks.state
                ks.state, ks.last_error, ks.last_probe_ok = "healthy", None, True
                ks.down_until = 0.0
                if was != "healthy":
                    log(f"pool {self.name}: {ks.name} RECOVERED ({ms:.0f}ms)")
                    self._audit("recover", ks, {"latency_ms": round(ms, 1)})
            else:
                ks.last_probe_ok = False
                ks.last_error = f"probe:{status}"
        return ok

    # ------------------------------------------------------------ selection

    def _eligible(self, now, model_id=None):
        """Keys usable right now (not in cooldown). A free_only key is
        eligible only for free-model requests -- never for paid traffic."""
        out = []
        for ks in self.keys:
            if ks.state == "down" and now < ks.down_until:
                continue
            if ks.free_only and not _is_free_model(model_id):
                continue
            out.append(ks)
        return out

    def _order(self, cands):
        def rank(ks):
            # healthy first, then unknown, then stale-down; fastest probe first
            st = {"healthy": 0, "unknown": 1, "down": 2}.get(ks.state, 3)
            return (st, ks.latency_ms if ks.latency_ms is not None else 1e9)
        return sorted(cands, key=rank)

    def _select_one(self, ks, model_id, now, via=None):
        """Probe-or-select a single candidate. Returns True when ks may
        carry traffic. Shared by pick() and race_candidates() so both paths
        apply identical probing, parking, free_only gating and audits."""
        if ks.state == "unknown" or not ks.last_probe_ok:
            if self._probe_and_update(ks):
                detail = {"latency_ms": ks.latency_ms, "model": model_id}
                if via:
                    detail["via"] = via
                self._audit("select", ks, detail)
                return True
            # probe failed -> park it briefly, keep going
            with self.lock:
                ks.state = "down"
                ks.down_until = now + self.cooldown_default
            self._audit("probe_fail", ks, {"error": ks.last_error})
            return False
        detail = {"latency_ms": ks.latency_ms, "model": model_id}
        if via:
            detail["via"] = via
        self._audit("select", ks, detail)
        return True

    def pick(self, model_id=None):
        """First-valid-wins. Returns a KeyState or None (all down).
        model_id gates free_only keys: they serve only free models."""
        now = time.time()
        for ks in self._order(self._eligible(now, model_id)):
            if self._select_one(ks, model_id, now):
                return ks
        # Nothing eligible: on-demand revalidation sweep (recovery path).
        # Respect cooldown: never re-probe a key that was just marked down
        # (its health probe may pass while a specific model still 429s --
        # re-selecting it causes the "keys exhausted" repeat-pick bug).
        for ks in self._order(self.keys):
            if ks.state == "down" and time.time() < ks.down_until:
                continue
            if ks.free_only and not _is_free_model(model_id):
                continue
            if self._select_one(ks, model_id, time.time(),
                                via="recovery_sweep"):
                return ks
        return None

    def race_candidates(self, model_id, n):
        """Top-n race candidates for KEYPOOL_RACE_KEYS>1. Applies exactly
        pick()'s selection semantics (cheap probes, parking, free_only
        gating, recovery sweep) but returns up to n usable keys instead of
        one, so the race never spends a contestant slot on a key pick()
        would have rejected."""
        now = time.time()
        out = []
        for ks in self._order(self._eligible(now, model_id)):
            if len(out) >= n:
                break
            if self._select_one(ks, model_id, now):
                out.append(ks)
        if len(out) < n:
            for ks in self._order(self.keys):
                if len(out) >= n:
                    break
                if ks in out:
                    continue
                if ks.state == "down" and time.time() < ks.down_until:
                    continue
                if ks.free_only and not _is_free_model(model_id):
                    continue
                if self._select_one(ks, model_id, time.time(),
                                    via="recovery_sweep"):
                    out.append(ks)
        return out

    def mark_down(self, ks, status):
        cd = self.cooldown.get(status, self.cooldown_default)
        with self.lock:
            ks.state = "down"
            ks.last_error = f"http:{status}"
            ks.down_until = time.time() + cd
        log(f"pool {self.name}: {ks.name} http:{status} -> down {cd:.0f}s (routing signal)")
        self._audit("failover", ks, {"http_status": status,
                                     "cooldown_s": cd})

    def _race_record(self, won):
        """Account one finished race (KEYPOOL_RACE_KEYS>1 path)."""
        with self.lock:
            self.race_stats["races"] += 1
            self.race_stats["wins" if won else "failed"] += 1


POOLS = {}
POOLS_LOCK = threading.Lock()


def load_pools():
    secrets = load_secrets(SECRETS_PATH)
    try:
        with open(POOLS_PATH) as f:
            doc = _parse_simple_yaml(f.read())
    except OSError as e:
        log(f"pools config read failed: {e}")
        return
    pools = {}
    for pname, cfg in (doc.get("pools") or {}).items():
        try:
            pools[pname] = Pool(pname, cfg, secrets)
            log(f"pool {pname}: {len(pools[pname].keys)} keys loaded (names only)")
        except Exception as e:
            log(f"pool {pname} config error: {e} — skipped")
    global POOLS
    with POOLS_LOCK:
        POOLS = pools


def reload_all(signum=None, frame=None):
    log("reloading pools config + secrets")
    load_pools()


def race_first_valid(pool, forward, candidates):
    """Concurrent first-valid-wins across candidates (KEYPOOL_RACE_KEYS>1).

    forward(ks) -> response object on 2xx, or raises urllib.error.HTTPError
    / Exception. Each contestant runs on its own daemon thread; results are
    collected event-driven on a queue (no sleeps, no polling, no
    ThreadPoolExecutor-as-context-manager which would serialize the tail).

    Returns (kind, ks, payload, ms):
      ("winner", ks, resp, ms)   first 2xx — serve resp, losers are closed
      ("error", None, code, ms)  first non-routing HTTPError — forward it now,
                                 exactly as the sequential path would
      ("failed", None, None, 0)  every contestant lost — 502 with tried list

    A 401/402/429 parks just that key (pool.mark_down: routing signal, same
    as sequential) and that contestant drops out. A timeout / network error
    just loses the race (no key state change). Loser responses are closed
    best-effort: urllib blocking calls cannot be force-cancelled, so the
    live-response registry + stop flag guarantee every loser connection is
    closed either by the settler or by the still-flying thread itself.
    """
    q = queue.Queue()
    stop = threading.Event()
    pending = len(candidates)
    live = {}               # key name -> response arrived but race undecided
    live_lock = threading.Lock()

    def close_resp(resp):
        try:
            resp.close()
        except Exception:
            pass

    def attempt(ks):
        t0 = time.monotonic()
        try:
            resp = forward(ks)
        except urllib.error.HTTPError as e:
            q.put(("httperr", ks, e, (time.monotonic() - t0) * 1000))
            return
        except Exception as e:  # timeout / DNS / reset: just loses the race
            q.put(("err", ks, e, (time.monotonic() - t0) * 1000))
            pool._audit("race_loss", ks, {"error": str(e)[:160]})
            return
        ms = (time.monotonic() - t0) * 1000
        with live_lock:
            if stop.is_set():
                closed = True
            else:
                live[ks.name] = resp
                closed = False
        if closed:
            close_resp(resp)          # race already decided: self-close
            q.put(("late", ks, None, ms))
        else:
            q.put(("ok", ks, resp, ms))

    def settle(winner_resp=None):
        """Decide the race: no new winners; close every loser connection."""
        stop.set()
        with live_lock:
            for resp in live.values():
                if resp is not winner_resp:
                    close_resp(resp)
            live.clear()
        while True:
            try:
                kind, ks, payload, _ms = q.get_nowait()
            except queue.Empty:
                return
            if kind == "ok" and payload is not None \
                    and payload is not winner_resp:
                close_resp(payload)

    for ks in candidates:
        threading.Thread(target=attempt, args=(ks,), daemon=True,
                         name=f"keypool-race-{pool.name}-{ks.name}").start()

    # Every attempt carries pool.request_timeout; the deadline is slack for
    # thread teardown only — winners arrive event-driven through the queue.
    deadline = time.monotonic() + pool.request_timeout + 5
    while pending > 0:
        try:
            kind, ks, payload, ms = q.get(
                timeout=max(0.05, deadline - time.monotonic()))
        except queue.Empty:
            break  # hung attempt; daemon threads self-close on completion
        pending -= 1
        if kind == "ok":
            pool._audit("race_win", ks, {
                "latency_ms": round(ms, 1),
                "contestants": [c.name for c in candidates],
            })
            settle(payload)
            return ("winner", ks, payload, ms)
        if kind == "httperr":
            e = payload
            if e.code in pool.fail_status:
                # Routing signal: park just this key, keep waiting.
                pool.mark_down(ks, e.code)
                continue
            # Non-routing error: forward immediately, like sequential mode.
            settle()
            return ("error", None, e.code, ms)
        # "err" / "late": contestant lost, keep waiting for the rest.
    settle()
    return ("failed", None, None, 0.0)


# ------------------------------------------------------------------- proxy

def _read_body(handler):
    if "chunked" in handler.headers.get("Transfer-Encoding", "").lower():
        body = bytearray()
        while True:
            line = handler.rfile.readline().strip()
            if not line:
                break
            n = int(line.split(b";")[0], 16)
            if n == 0:
                while True:
                    t = handler.rfile.readline()
                    if not t.strip():
                        break
                break
            body += handler.rfile.read(n)
            handler.rfile.readline()
        return bytes(body)
    length = int(handler.headers.get("Content-Length") or 0)
    return handler.rfile.read(length) if length else b""


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "KeyPool/1.0"

    def _send_json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _route(self):
        # /<pool>/rest... -> (pool, /rest)
        parts = self.path.split("?", 1)[0].split("/", 2)
        if len(parts) < 2 or not parts[1]:
            return None, None
        with POOLS_LOCK:
            pool = POOLS.get(parts[1])
        rest = "/" + parts[2] if len(parts) > 2 else "/"
        return pool, rest

    def do_GET(self):
        p = self.path.split("?", 1)[0]
        if p == "/health" or p == "/health/":
            self._send_json(200, {"ok": True})
            return
        if p == "/status" or p == "/status/":
            self._serve_status()
            return
        self._proxy()

    def _serve_status(self):
        now = time.time()
        out = {"ts": now, "race_keys": RACE_KEYS, "pools": {}}
        with POOLS_LOCK:
            pools = dict(POOLS)
        for pname, pool in pools.items():
            keys = []
            for ks in pool.keys:
                with pool.lock:
                    keys.append({
                        "name": ks.name,
                        "free_only": ks.free_only,
                        "fingerprint": ks.fp,
                        "state": ks.state,
                        "latency_ms": ks.latency_ms,
                        "last_error": ks.last_error,
                        "recover_in_s": round(max(0.0, ks.down_until - now), 1)
                        if ks.state == "down" else 0.0,
                    })
            with pool.lock:
                race = dict(pool.race_stats)
            out["pools"][pname] = {"upstream": pool.upstream, "keys": keys,
                                   "race": race}
        self._send_json(200, out)

    def _forward(self, pool, rest, raw, ks):
        url = pool.upstream + rest
        qs = self.path.split("?", 1)
        if len(qs) > 1:
            url += "?" + qs[1]
        if self.command in ("POST", "PUT", "PATCH"):
            req = urllib.request.Request(url, data=raw, method=self.command)
        else:
            req = urllib.request.Request(url, method=self.command)
        for k, v in self.headers.items():
            if k.lower() not in REQ_STRIP_HEADERS:
                req.add_header(k, v)
        # The pool injects the chosen key. This is the ONLY place a raw
        # key value is used — it never appears in logs, audit, or /status.
        req.add_header("Authorization", "Bearer " + ks.value)
        return urllib.request.urlopen(req, timeout=pool.request_timeout)

    def _serve_response(self, resp):
        """Stream an upstream response back to the caller. Shared by the
        sequential path and the race winner."""
        rctype = resp.headers.get("Content-Type", "")
        no_length = resp.headers.get("Content-Length") is None
        self.send_response(resp.status)
        for k, v in resp.headers.items():
            if k.lower() not in HOP_HEADERS:
                self.send_header(k, v)
        if no_length:
            self.send_header("Connection", "close")
        self.end_headers()
        streaming = ("text/event-stream" in rctype) or (
            no_length and "chunked" in resp.headers.get("Transfer-Encoding", "").lower()
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
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            try:
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
        if no_length:
            self.close_connection = True

    def _proxy(self):
        pool, rest = self._route()
        if pool is None:
            self._send_json(404, {"error": "unknown keypool route"})
            return
        raw = _read_body(self)
        model_id = _extract_model(raw)
        # Tau-compat borrow: adapt neutral OpenAI bodies to upstream wire
        # rules (reasoning-first token floor, sampling-strip for o1/o3/gpt-5+).
        raw = _apply_openai_compat(pool.name, model_id, raw)

        if RACE_KEYS > 1:
            self._proxy_race(pool, rest, raw, model_id)
        else:
            self._proxy_sequential(pool, rest, raw, model_id)

    def _proxy_sequential(self, pool, rest, raw, model_id):
        """Historical path: pick one key, fail over serially. Bit-for-bit
        the pre-racing behavior; RACE_KEYS=1 lands here."""
        tried = []
        while True:
            ks = pool.pick(model_id)
            if ks is None:
                self._send_json(502, {
                    "error": f"keypool '{pool.name}': no healthy key",
                    "tried": tried,
                    "hint": "see /status for per-key states; keys revalidate on demand",
                })
                return
            if ks.name in tried:
                # pick() returned a repeat — all remaining are down; stop.
                self._send_json(502, {
                    "error": f"keypool '{pool.name}': keys exhausted",
                    "tried": tried,
                })
                return
            tried.append(ks.name)
            try:
                resp = self._forward(pool, rest, raw, ks)
            except urllib.error.HTTPError as e:
                if e.code in pool.fail_status:
                    pool.mark_down(ks, e.code)
                    continue  # fail over to next key
                self._send_json(e.code, {"error": f"keypool upstream: HTTP {e.code}"})
                return
            except Exception as e:
                self._send_json(502, {"error": f"keypool upstream: {e}"})
                return

            self._serve_response(resp)
            return

    def _proxy_race(self, pool, rest, raw, model_id):
        """KEYPOOL_RACE_KEYS>1: first-valid-wins across the top-N eligible
        keys. A degraded-but-not-dead first key no longer serializes the
        tail; losers are abandoned and their connections closed."""
        candidates = pool.race_candidates(model_id, RACE_KEYS)
        if not candidates:
            self._send_json(502, {
                "error": f"keypool '{pool.name}': no healthy key",
                "tried": [],
                "hint": "see /status for per-key states; keys revalidate on demand",
            })
            return
        tried = [ks.name for ks in candidates]
        kind, ks, payload, ms = race_first_valid(
            pool, lambda k: self._forward(pool, rest, raw, k), candidates)
        pool._race_record(kind == "winner")
        if kind == "winner":
            self._serve_response(payload)
        elif kind == "error":
            self._send_json(payload,
                            {"error": f"keypool upstream: HTTP {payload}"})
        else:
            self._send_json(502, {
                "error": f"keypool '{pool.name}': no healthy key",
                "tried": tried,
                "hint": "see /status for per-key states; keys revalidate on demand",
            })

    # HTTP verb aliases — bound AFTER _proxy is defined (class-body order).
    do_POST = _proxy
    do_PUT = _proxy
    do_DELETE = _proxy
    do_PATCH = _proxy

    def log_message(self, *a):
        pass


def selftest():
    """Key selection / failover / recovery logic against a MOCK upstream.
    Never touches real keys or the network."""
    import http.server as hs
    import tempfile
    global AUDIT_PATH
    AUDIT_PATH = os.path.join(tempfile.mkdtemp(prefix="keypool-selftest-"),
                              "audit.jsonl")

    class MockUpstream(hs.BaseHTTPRequestHandler):
        # class-level script: list of (path, auth_fp) -> (status, body)
        behavior = {}
        def _h(self):
            key = (self.path, self.headers.get("Authorization"))
            st, body = MockUpstream.behavior.get(key, (404, b"nope"))
            b = body if isinstance(body, bytes) else body.encode()
            self.send_response(st)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
        do_GET = _h
        do_POST = _h
        def log_message(self, *a):
            pass

    srv = hs.HTTPServer(("127.0.0.1", 0), MockUpstream)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    fails = 0

    def mkpool(keys, health_map, fail_status=(401, 402, 429)):
        p = Pool.__new__(Pool)
        p.name, p.upstream = "test", f"http://127.0.0.1:{port}"
        p.health_method, p.health_path = "GET", "/auth"
        p.health_ok, p.fail_status = {200}, set(fail_status)
        p.probe_timeout, p.request_timeout = 2, 10
        p.cooldown = {401: 300, 402: 300, 429: 60}
        p.cooldown_default = 120
        p.keys = [KeyState(n, v) for n, v in keys]
        p.lock = threading.Lock()
        p.race_stats = {"races": 0, "wins": 0, "failed": 0}
        p._health_map = health_map
        orig = p._health_probe
        def fake(ks):
            st = p._health_map.get(ks.name, (False, 1.0, 401))
            ok, ms, code = st
            return ok, ms, code
        p._health_probe = fake
        return p

    # case 1: first-valid-wins — dead first key probed, skipped, second used
    MockUpstream.behavior = {
        ("/v1/chat/completions", "Bearer K2"): (200, b'{"ok":1}'),
        ("/v1/chat/completions", "Bearer K1"): (401, b'{"error":"bad"}'),
    }
    pool = mkpool([("K1NAME", "K1"), ("K2NAME", "K2")],
                  {"K1NAME": (False, 5.0, 401), "K2NAME": (True, 8.0, 200)})
    ks = pool.pick()
    if ks is None or ks.name != "K2NAME":
        print(f"FAIL case1: pick -> {ks and ks.name}"); fails += 1
    if pool.keys[0].state != "down":
        print("FAIL case1: dead key not parked"); fails += 1

    # case 2: 401 mid-request fails over to next key
    MockUpstream.behavior = {
        ("/v1/chat/completions", "Bearer KA"): (401, b'{"error":"bad"}'),
        ("/v1/chat/completions", "Bearer KB"): (200, b'{"ok":1}'),
    }
    pool = mkpool([("A", "KA"), ("B", "KB")],
                  {"A": (True, 5.0, 200), "B": (True, 6.0, 200)})
    # simulate: first pick A, mark_down on 401, pick again -> B
    first = pool.pick()
    pool.mark_down(first, 401)
    second = pool.pick()
    if first.name != "A" or second.name != "B":
        print(f"FAIL case2: {first.name} -> {second and second.name}"); fails += 1
    if first.state != "down":
        print("FAIL case2: A not parked after 401"); fails += 1

    # case 3: recovery — down key rejoins when cooldown expires
    pool.keys[0].down_until = time.time() - 1  # cooldown elapsed
    pool._health_map = {"A": (True, 5.0, 200), "B": (True, 6.0, 200)}
    # force re-probe path by marking unknown
    pool.keys[0].state, pool.keys[0].last_probe_ok = "unknown", False
    # B must not win on rank: park it in cooldown so A is the only candidate
    pool.keys[1].state, pool.keys[1].down_until = "down", time.time() + 300
    got = pool.pick()
    if got is None or got.name != "A" or got.state != "healthy":
        print(f"FAIL case3: recovery -> {got and (got.name, got.state)}"); fails += 1

    # case 4: fingerprints are stable and non-reversible-looking
    if fingerprint("K1") == "K1" or len(fingerprint("K1")) != 12:
        print("FAIL case4: fingerprint"); fails += 1

    # case 5: all keys down -> pick() runs recovery sweep, returns None when all fail
    pool = mkpool([("X", "KX")], {"X": (False, 5.0, 401)})
    pool.keys[0].state, pool.keys[0].down_until = "down", time.time() + 300
    got = pool.pick()
    if got is not None:
        print(f"FAIL case5: expected None, got {got.name}"); fails += 1

    # case 6: free_only key IS selected for a :free model
    pool = mkpool([("FREENAME", "KF"), ("PAIDNAME", "KP")],
                  {"FREENAME": (True, 5.0, 200), "PAIDNAME": (True, 6.0, 200)})
    pool.keys[0].free_only = True
    got = pool.pick("x/y:free")
    if got is None or got.name != "FREENAME":
        print(f"FAIL case6: free model -> {got and got.name}"); fails += 1

    # case 7: free_only key is NEVER selected for a paid model;
    # only-free_only pool + paid model -> None (no silent fallback)
    got = pool.pick("x/y")
    if got is None or got.name != "PAIDNAME":
        print(f"FAIL case7a: paid model -> {got and got.name}"); fails += 1
    pool2 = mkpool([("FREENAME", "KF")], {"FREENAME": (True, 5.0, 200)})
    pool2.keys[0].free_only = True
    got = pool2.pick("x/y")
    if got is not None:
        print(f"FAIL case7b: paid model on free-only pool -> {got.name}"); fails += 1
    got = pool2.pick("openrouter/free")
    if got is None or got.name != "FREENAME":
        print(f"FAIL case7c: openrouter/free -> {got and got.name}"); fails += 1

    # case 8: dict key entries via real Pool.__init__ + _is_free_model/_extract_model
    cfg = {"upstream": f"http://127.0.0.1:{port}",
           "health": {"method": "GET", "path": "/auth", "ok": [200]},
           "keys": [{"name": "D1", "free_only": True}, "D2"]}
    pool3 = Pool("cfgtest", cfg, {"D1": "VD1", "D2": "VD2"})
    if len(pool3.keys) != 2 or not pool3.keys[0].free_only or pool3.keys[1].free_only:
        print("FAIL case8a: dict key entries"); fails += 1
    if not (_is_free_model("a/b:free") and _is_free_model("openrouter/free")
            and not _is_free_model("a/b") and not _is_free_model(None)
            and not _is_free_model("")):
        print("FAIL case8b: _is_free_model"); fails += 1
    if _extract_model(b'{"model":"a/b:free"}') != "a/b:free" or \
       _extract_model(b"") is not None or _extract_model(b"not json") is not None:
        print("FAIL case8c: _extract_model"); fails += 1
    # legacy pick() with no args still works
    got = pool.pick()
    if got is None:
        print("FAIL case8d: legacy pick()"); fails += 1

    # ---- racing: race_first_valid + race_candidates (KEYPOOL_RACE_KEYS>1)
    import urllib.error as _ue

    class FakeResp:
        def __init__(self):
            self.closed = False
        def close(self):
            self.closed = True

    def http_err(code):
        return _ue.HTTPError("http://127.0.0.1/x", code, f"HTTP {code}",
                             {}, None)

    def wait_closed(resp, timeout=2.0):
        end = time.monotonic() + timeout
        while not resp.closed and time.monotonic() < end:
            time.sleep(0.01)
        return resp.closed

    # case 9: slow A (0.4s) vs fast B (0.01s) — B wins well before A finishes,
    # and the loser's connection is closed.
    seen = {}
    def fwd_ab(ks):
        if ks.name == "A":
            time.sleep(0.4)
        else:
            time.sleep(0.01)
        r = FakeResp()
        seen[ks.name] = r
        return r
    pool = mkpool([("A", "KA"), ("B", "KB")],
                  {"A": (True, 5.0, 200), "B": (True, 6.0, 200)})
    cands = pool.race_candidates(None, 2)
    t0 = time.monotonic()
    kind, ks, payload, ms = race_first_valid(pool, fwd_ab, cands)
    dt = time.monotonic() - t0
    if kind != "winner" or ks.name != "B":
        print(f"FAIL case9: race -> {kind} {ks and ks.name}"); fails += 1
    if dt >= 0.35:
        print(f"FAIL case9: winner took {dt:.2f}s (fast key ~0.01s)"); fails += 1
    end = time.monotonic() + 2.0
    while "A" not in seen and time.monotonic() < end:
        time.sleep(0.01)
    if "A" not in seen or not wait_closed(seen["A"]):
        print("FAIL case9: loser connection not closed"); fails += 1

    # case 10: fast 401 on A, healthy B — B wins, A parked (routing signal)
    def fwd_401(ks):
        if ks.name == "A":
            raise http_err(401)
        return FakeResp()
    pool = mkpool([("A", "KA"), ("B", "KB")],
                  {"A": (True, 5.0, 200), "B": (True, 6.0, 200)})
    cands = pool.race_candidates(None, 2)
    kind, ks, payload, ms = race_first_valid(pool, fwd_401, cands)
    if kind != "winner" or ks.name != "B":
        print(f"FAIL case10: -> {kind} {ks and ks.name}"); fails += 1
    if pool.keys[0].state != "down":
        print("FAIL case10: 401 contestant not parked"); fails += 1

    # case 11: all contestants 401 — race fails, every key parked
    def fwd_all401(ks):
        raise http_err(401)
    pool = mkpool([("A", "KA"), ("B", "KB")],
                  {"A": (True, 5.0, 200), "B": (True, 6.0, 200)})
    cands = pool.race_candidates(None, 2)
    kind, ks, payload, ms = race_first_valid(pool, fwd_all401, cands)
    if kind != "failed":
        print(f"FAIL case11: -> {kind}"); fails += 1
    if any(k.state != "down" for k in pool.keys):
        print("FAIL case11: not all contestants parked"); fails += 1

    # case 12: fast 500 on A, slow B — non-routing error forwarded
    # immediately (same as sequential mode), not after B's 0.4s
    def fwd_500(ks):
        if ks.name == "A":
            raise http_err(500)
        time.sleep(0.4)
        return FakeResp()
    pool = mkpool([("A", "KA"), ("B", "KB")],
                  {"A": (True, 5.0, 200), "B": (True, 6.0, 200)})
    cands = pool.race_candidates(None, 2)
    t0 = time.monotonic()
    kind, ks, payload, ms = race_first_valid(pool, fwd_500, cands)
    dt = time.monotonic() - t0
    if kind != "error" or payload != 500:
        print(f"FAIL case12: -> {kind} {payload}"); fails += 1
    if dt >= 0.35:
        print(f"FAIL case12: non-routing error not immediate ({dt:.2f}s)"); fails += 1

    # case 13: timeout on A, healthy B — B wins, A NOT parked (no state
    # change for a lone timeout, per the racing contract)
    def fwd_timeout(ks):
        if ks.name == "A":
            raise TimeoutError("upstream timed out")
        return FakeResp()
    pool = mkpool([("A", "KA"), ("B", "KB")],
                  {"A": (True, 5.0, 200), "B": (True, 6.0, 200)})
    cands = pool.race_candidates(None, 2)
    kind, ks, payload, ms = race_first_valid(pool, fwd_timeout, cands)
    if kind != "winner" or ks.name != "B":
        print(f"FAIL case13: -> {kind} {ks and ks.name}"); fails += 1
    if pool.keys[0].state == "down":
        print("FAIL case13: timeout wrongly parked the key"); fails += 1

    # case 14: race_candidates honors free_only gating and the N cap.
    # (healthy keys rank before unknown ones, exactly like pick().)
    pool = mkpool([("F", "KF"), ("P1", "KP1"), ("P2", "KP2")],
                  {"F": (True, 1.0, 200), "P1": (True, 2.0, 200),
                   "P2": (True, 3.0, 200)})
    pool.keys[0].free_only = True
    cands = pool.race_candidates("x/y", 3)
    if [k.name for k in cands] != ["P1", "P2"]:
        print(f"FAIL case14a: paid -> {[k.name for k in cands]}"); fails += 1
    pool = mkpool([("F", "KF"), ("P1", "KP1"), ("P2", "KP2")],
                  {"F": (True, 1.0, 200), "P1": (True, 2.0, 200),
                   "P2": (True, 3.0, 200)})
    pool.keys[0].free_only = True
    cands = pool.race_candidates("x/y:free", 2)
    if [k.name for k in cands] != ["F", "P1"]:
        print(f"FAIL case14b: free n=2 -> {[k.name for k in cands]}"); fails += 1
    cands = pool.race_candidates("x/y:free", 3)
    if [k.name for k in cands] != ["F", "P1", "P2"]:
        print(f"FAIL case14c: free n=3 -> {[k.name for k in cands]}"); fails += 1
    if pool.keys[0].state != "healthy":
        print("FAIL case14d: free_only key not probed healthy"); fails += 1

    # case 15: race telemetry init/record; RACE_KEYS default stays 1
    pool = mkpool([("A", "KA")], {"A": (True, 5.0, 200)})
    if pool.race_stats != {"races": 0, "wins": 0, "failed": 0}:
        print("FAIL case15a: race_stats init"); fails += 1
    pool._race_record(True)
    pool._race_record(False)
    if pool.race_stats != {"races": 2, "wins": 1, "failed": 1}:
        print(f"FAIL case15b: {pool.race_stats}"); fails += 1
    if RACE_KEYS != 1:
        print("FAIL case15c: default RACE_KEYS should be 1"); fails += 1

    srv.shutdown()
    print("keypool selftest: " + ("ALL PASS" if not fails else f"{fails} FAILURES"))
    return fails


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        sys.exit(1 if selftest() else 0)
    load_pools()
    signal.signal(signal.SIGHUP, reload_all)
    try:
        srv = ThreadingHTTPServer(LISTEN, Handler)
    except OSError as e:
        import errno as _errno
        if e.errno == _errno.EADDRINUSE:
            msg = ("[keypool] FATAL: %s:%d already in use - another keypool "
                   "holds it. Set KEYPOOL_PORT to run a second instance."
                   % (LISTEN[0], LISTEN[1]))
            print(msg, flush=True)
            sys.exit(98)
        raise
    log(f"listening on {LISTEN[0]}:{LISTEN[1]} (pools: {', '.join(sorted(POOLS)) or 'none'})")
    srv.serve_forever()


if __name__ == "__main__":
    main()
