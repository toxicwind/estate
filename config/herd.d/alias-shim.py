#!/usr/bin/env python3
"""alias-shim: fixed-target alias forwarder for herd.

Started by herd (llama-swap) as a models.<alias> cmd entry:
    python3 alias-shim.py --port ${PORT} --target <peer-model-id> [--standby <peer-model-id>]... [--advance-on 5xx,conn,429,402,404] [--name <alias>]

Rewrites incoming `model: "<alias>"` to the fixed target and forwards to
herd, streaming the response back. The target (and optional standby chain)
are fixed at config time -- the ROUTER CONFIG owns model selection; this
shim never selects, ranks, probes, or prefers any model family. If every
candidate is down the caller gets the last upstream error verbatim (fail
loudly, never silently substitute).

CRITICAL CONSTRAINT (learned 2026-09-21, oracle-judge-local incident): a
shim hosted INSIDE llama-swap as a cmd model MUST NOT target another
llama-swap cmd model. The swapper cannot swap to the target while the shim
holds the active slot for the in-flight outer request -- re-entrant
deadlock: /health stays 200 (no swap on GET /v1/models) while completions
hang until the connect/TTFT timeout fires. Targets must be proxy peers
(remote upstreams) or standalone daemons -- never sibling cmd models.

Optional ordered standby chain (HFT telecom pattern): --standby may be
repeated to declare an ordered failover chain. When a candidate errors with
a chain-advancing signal the shim tries the next candidate exactly once
each, then surfaces whatever the last candidate returned. Never a retry
spin. Default advancing signals: connection failure and HTTP 5xx. Config
may extend via --advance-on (e.g. "5xx,conn,429,402,404" for free-tier
maximal chains where throttle/billing/rotation are expected transients).
HTTP 401 NEVER advances: an auth failure is misconfiguration and surfaces
verbatim so it stays visible. Without --advance-on, 4xx surfaces verbatim.

Transport behavior:
curl-like header layout (Pollinations bot-filter workaround), browser
User-Agent, Authorization passthrough, verbatim SSE streaming, fail-fast
8s herd connect/TTFT ceiling, self-loop rejection (508).
Timeout split (v3.1): the 8s ceiling covers connect + response headers
only. Once headers arrive the socket timeout relaxes to READ_TIMEOUT
(default 300s, env SHIM_READ_TIMEOUT) so a slow-but-alive upstream is
never killed mid-generation. A stalled upstream still surfaces a loud
502 JSON -- never a dropped connection (HTTP 000).

Health is honest: /health does one bounded catalog GET to the router's
/v1/models on every call (event-driven -- no timers, no probes, no
completions) and ALWAYS returns HTTP 200 (process liveness); the body
carries "routable": true/false plus a detail string. A non-200 here
would make supervisors (llama-swap swap scheduler, pitchfork health)
treat an unroutable-but-alive alias as dead and wedge dispatch -- the
process must stay dispatchable so the chain can advance past dead
candidates. Request failures surface as the upstream status, never a
masked 200.

Router-config ownership: to change what an alias serves, edit the --target
/ --standby flags in the herd config (config/herd.yaml or the --config-dir
fragment). No code changes, no timers, no probes.

Usage (herd invokes it; never run by hand with a different target).
"""

import argparse
import http.client
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, required=True)
ap.add_argument("--target", required=True,
                help="primary model id -- set in ROUTER CONFIG (herd.yaml / config-dir fragment)")
ap.add_argument("--standby", action="append", default=[],
                help="optional ordered failover model id -- repeat for a chain; "
                     "set in ROUTER CONFIG")
ap.add_argument("--advance-on", default="5xx,conn",
                help="comma list of chain-advancing signals: 5xx, conn, 429, "
                     "402, 404 (401 never advances). Set in ROUTER CONFIG.")
ap.add_argument("--name", default=None,
                help="alias name advertised on /v1/models (optional)")
ap.add_argument("--herd", default="http://127.0.0.1:25100")
args = ap.parse_args()
HERD = urlparse(args.herd)

# Timeout split: fail-fast on connect/first-byte (herd is localhost; a
# stalled upstream must surface loudly, not hang the caller), generous
# once the upstream proves alive (slow/cold models stream for minutes).
CONNECT_TIMEOUT = float(os.environ.get("SHIM_CONNECT_TIMEOUT", "8"))
READ_TIMEOUT = float(os.environ.get("SHIM_READ_TIMEOUT", "300"))

# Browser UA for all herd traffic (Pollinations bot-filter workaround,
# verified 2026-09-14). Transport detail, not model selection.
BROWSER_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
              "Chrome/126.0 Safari/537.36")

LOOP_MSG = "alias loop: requested model is the alias target itself"


class _UpstreamError(Exception):
    """Upstream failed before we sent response headers: safe to 502."""


class Handler(BaseHTTPRequestHandler):
    server_version = "alias-shim/3.1"

    def log_message(self, fmt, *a):
        sys.stderr.write("[alias-shim:%s] " % args.target + fmt % a + "\n")

    def _chain(self):
        """Ordered candidate chain: target first, then unique standbys."""
        seen = []
        for cand in [args.target] + (args.standby or []):
            if cand and cand not in seen:
                seen.append(cand)
        return seen

    def _advance_signals(self):
        """Parse --advance-on into ({status codes}, allow_conn, allow_5xx)."""
        codes, conn, fxx = set(), False, False
        for tok in (args.advance_on or "").split(","):
            tok = tok.strip().lower()
            if tok == "conn":
                conn = True
            elif tok in ("5xx", "500"):
                fxx = True
            elif tok.isdigit():
                codes.add(int(tok))
        return codes, conn, fxx

    def _send_json(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        if self.path == "/health" or self.path.startswith("/health?"):
            # Process liveness is ALWAYS 200: the shim is up and serving.
            # Route health rides in the body ("routable" bool). A non-200
            # here makes supervisors (llama-swap swap, pitchfork health)
            # treat an unroutable-but-alive alias as dead and wedge the
            # scheduler -- the process must stay dispatchable so the chain
            # can advance past dead candidates.
            ok, detail = self._route_check()
            self._send_json(200, {
                "status": "ok" if ok else "unroutable",
                "target": args.target,
                "standby": args.standby or [],
                "chain": self._chain(),
                "advance_on": args.advance_on,
                "alias": args.name,
                "selection": "router-config",
                "routable": ok,
                "detail": detail,
                "note": "http 200 = process alive; see 'routable' for route health",
            })
        elif self.path == "/v1/models" or self.path.startswith("/v1/models?"):
            data = []
            if args.name:
                data.append({
                    "id": args.name, "object": "model", "owned_by": "alias-shim",
                    "metadata": {"alias_of": args.target,
                                 "chain": self._chain(),
                                 "advance_on": args.advance_on,
                                 "selection": "router-config"},
                })
            self._send_json(200, {"object": "list", "data": data})
        else:
            self._send_json(404, {"error": "not found"})

    def _route_check(self):
        """One bounded catalog GET to the router, only when /health is hit.

        No timers, no probing, no selection: verifies exactly the configured
        target is advertised by the router. Returns (ok, detail).
        """
        conn = None
        try:
            conn = http.client.HTTPConnection(HERD.hostname, HERD.port or 80,
                                              timeout=5)
            conn.request("GET", "/v1/models")
            resp = conn.getresponse()
            if resp.status != 200:
                return False, "router /v1/models -> %d" % resp.status
            data = json.loads(resp.read().decode("utf-8", "replace"))
            ids = {m.get("id") for m in data.get("data", [])
                   if isinstance(m, dict)}
            if args.target in ids:
                return True, "target advertised by router"
            return False, "target %r not advertised by router" % args.target
        except Exception as exc:
            return False, "router unreachable: %s" % exc
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    def _forward(self, model_id, payload, auth):
        """Forward one attempt to herd with model_id.

        Connect + response headers are fail-fast (CONNECT_TIMEOUT); once
        headers arrive the socket timeout relaxes to READ_TIMEOUT so a
        slow-but-alive upstream is never killed mid-generation.
        Returns (conn, resp, None) or (None, None, err).
        """
        body = json.dumps(payload).encode("utf-8")
        conn = None
        try:
            conn = http.client.HTTPConnection(HERD.hostname, HERD.port or 80,
                                              timeout=CONNECT_TIMEOUT)
            conn.putrequest("POST", "/v1/chat/completions")
            conn.putheader("Accept", "*/*")
            conn.putheader("Content-Type", "application/json")
            conn.putheader("User-Agent", BROWSER_UA)
            if auth:
                conn.putheader("Authorization", auth)
            conn.putheader("Content-Length", str(len(body)))
            conn.endheaders()
            conn.send(body)
            resp = conn.getresponse()
            # Headers arrived: upstream is alive. Relax the timeout for the
            # body -- a cold local model or long generation takes minutes.
            try:
                conn.sock.settimeout(READ_TIMEOUT)
            except Exception:
                pass
            return conn, resp, None
        except Exception as exc:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
            return None, None, "upstream %s via herd %s: %s" % (model_id, args.herd, exc)

    def _stream_back(self, resp, conn):
        """Relay the upstream response. Raises _UpstreamError if the body
        dies before we sent headers (caller turns it into a loud 502)."""
        self.send_response(resp.status)
        ctype = resp.getheader("Content-Type", "application/json")
        self.send_header("Content-Type", ctype)
        if "text/event-stream" in ctype:
            self.send_header("Cache-Control", "no-cache")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()
            try:
                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
        else:
            try:
                data = resp.read()
            except Exception as exc:
                raise _UpstreamError("upstream %s body read failed: %s"
                                    % (args.target, exc))
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass
        try:
            conn.close()
        except Exception:
            pass

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            self._send_json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            self._send_json(400, {"error": "invalid JSON body"})
            return
        requested = payload.get("model")
        if requested in (None, ""):
            self._send_json(400, {"error": "missing model"})
            return
        chain = self._chain()
        if requested in chain:
            # Self-reference guard: the alias must never route into itself.
            self._send_json(508, {"error": LOOP_MSG})
            return
        advance_codes, advance_conn, advance_5xx = self._advance_signals()
        auth = self.headers.get("Authorization")

        # Ordered chain walk (config-driven): each candidate tried at most
        # once, in config order. A candidate advances the chain on connection
        # failure (if 'conn') or HTTP 5xx (if '5xx') or any listed status.
        # HTTP 401 NEVER advances -- auth misconfiguration surfaces verbatim.
        # The caller receives the LAST candidate's response verbatim: success
        # streams back, terminal failure surfaces as the upstream status.
        conn, resp, err, served = None, None, None, None
        for i, cand in enumerate(chain):
            last = (i == len(chain) - 1)
            payload["model"] = cand
            conn, resp, err = self._forward(cand, payload, auth)
            if resp is None:
                if advance_conn and not last:
                    sys.stderr.write("[alias-shim:%s] %s unreachable (%s); advancing chain\n"
                                     % (args.target, cand, err))
                    continue
                break
            st = resp.status
            if st < 400 or st == 401:
                served = cand if i == 0 else "%s ->[%d] %s" % (args.target, i, cand)
                break  # success, or auth failure: surface verbatim, no advance
            adv = (st >= 500 and advance_5xx) or (st in advance_codes)
            if adv and not last:
                try:
                    resp.read()
                except Exception:
                    pass
                try:
                    conn.close()
                except Exception:
                    pass
                sys.stderr.write("[alias-shim:%s] %s -> herd HTTP %d; advancing chain\n"
                                 % (args.target, cand, st))
                conn, resp = None, None
                continue
            served = cand if i == 0 else "%s ->[%d] %s" % (args.target, i, cand)
            break

        if resp is None:
            self._send_json(502, {"error": err or "herd unreachable",
                                  "chain": chain, "served": served})
            return
        try:
            self._stream_back(resp, conn)
        except _UpstreamError as exc:
            # Headers not yet sent: loud 502, never a dropped connection.
            self._send_json(502, {"error": str(exc), "chain": chain,
                                  "served": served})
        except (BrokenPipeError, ConnectionResetError):
            pass  # client went away; nothing to surface
        except Exception as exc:
            # Headers already sent (mid-stream): log loudly, close.
            sys.stderr.write("[alias-shim:%s] stream aborted: %s\n"
                             % (args.target, exc))
        sys.stderr.write("[alias-shim:%s] %s -> %s (%s)\n"
                         % (args.target, requested, served, resp.status))


if __name__ == "__main__":
    sys.stderr.write("[alias-shim] target=%s standby=%s advance_on=%s alias=%s -> herd %s (selection: router-config)\n"
                     % (args.target, args.standby or [], args.advance_on, args.name, args.herd))
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
