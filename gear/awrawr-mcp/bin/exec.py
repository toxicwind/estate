#!/usr/bin/env python3
"""Run a shell command on yote through its MCP exec bridge.

Usage:
    exec.py "echo ok && whoami" [workdir]
    exec.py --sysinfo            one JSON snapshot: fresh vitals, hatch + yote
    exec.py --poll [SECS]        full-snapshot stream (default 5s); Ctrl-C stops
    exec.py --watch [SECS]       agentic event stream: baseline snapshot, then
                                 only changes, threshold alerts and errors;
                                 --alert-load N, --alert-mem PCT for thresholds

Sides: hatch is this runtime; yote is the bridge box (CachyOS/Arch, BORE
scheduler, server kernel). Every poll reads FRESH values from /proc and
sysfs on each side -- nothing is cached, because load, memory, thread counts
and uptime can change at any moment. The yote leg reuses the same transport
priority (ws_daemon, then HTTPS) and never re-dispatches.

Auth: Secure Vault connector custom.awrawr-mcp. The raw token is never
readable here; only its hsurr:* surrogate is sent, and only to the bridge
host. The surrogate travels in the X-MCP-Token header (the connector's
placement), which is the bridge's auth boundary. Sentinel swaps the
surrogate for the real credential on approved egress.

Performance: transport selection is an HFT race (first-valid-wins).
Both lanes pre-dispatch concurrently (unix-socket connect vs session
check, ~ms); the WS lane keeps dispatch priority while healthy and only
the winning lane ever dispatches remotely, so a command can never
double-execute. Every hop is measured in microseconds; winners go to
~/.cache/shingle/hft_race_winners.jsonl (tag "bridge-exec"). When WS has
won the last 10 races within 5 minutes the race is skipped entirely
(lead-with-winner: zero overhead) and re-raced once the log goes stale.
  1. local ws_daemon (one persistent wss:// connection to /exec-ws, ~0.1-0.3s
     per call, live streaming stdout/stderr) — started lazily on first use;
  2. HTTPS MCP with cached session id (~0.6s) as fallback.
A stale session falls back to a full handshake automatically.
Env: AWRAWR_RACE=0 legacy sequential; AWRAWR_RACE_ALWAYS=1 force racing;
AWRAWR_RACE_DEBUG=1 stderr timings.

Hardening: the HTTPS lane enforces a LOCAL read deadline (default 150s:
the awrawr-pc exec tool's 90s server ceiling + 60s margin, overridable with
--read-timeout) so a stalled/broken SSE stream can never hang the client —
--timeout only bounds the remote command, never the local read. A lane
that IncompleteReads, stalls, blows its deadline, or fails correlation is
marked degraded (~/.cache/awrawr-https-down, 60s TTL): the next call fails
fast instead of burning another full read cycle, then recovers on its own.
"""
import http.client
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error
import uuid
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import (
    add_surrogate_to_request,
    ensure_allowed_url,
)

CRED = "custom.awrawr-mcp"
HOSTS = ["github-mcp-host.tailc9ac71.ts.net"]
BASE = "https://github-mcp-host.tailc9ac71.ts.net/mcp"
TIMEOUT = 120
# Socket timeout for the HTTPS lane's urlopen (finding #4, 2026-09-20):
# must comfortably exceed the daemon's max wait (~150s). A quiet command
# in the 120-150s window previously died client-side with socket.timeout
# while the daemon was fine — and was then wrongly marked a read stall.
# Keep this above _DEFAULT_READ_TIMEOUT (150s) so the local read deadline,
# not the socket timeout, decides when a stalled stream is a real stall.
_HTTPS_SOCKET_TIMEOUT = 180
SESSION_FILE = os.path.expanduser("~/.cache/awrawr-mcp-session.json")
WS_SOCK = os.path.expanduser("~/.cache/awrawr-ws-bridge.sock")
WS_DAEMON = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "ws_daemon.py")

# Degraded steady-state: when the WS lane proves itself unusable, mark it
# down for _WS_DOWN_TTL so the next call skips WS entirely and goes straight
# to HTTPS instead of burning a connect cycle per call. Pre-dispatch
# failures (daemon never saw the command) fall back to HTTPS safely;
# post-dispatch failures (command may have executed remotely) are reported
# WITHOUT fallback — re-dispatch would risk double execution.
_WS_DOWN_FLAG = os.path.expanduser("~/.cache/awrawr-ws-down")
_WS_DOWN_TTL = 15


def _ws_known_down() -> bool:
    try:
        return time.time() - os.path.getmtime(_WS_DOWN_FLAG) < _WS_DOWN_TTL
    except OSError:
        return False


def _ws_mark_down() -> None:
    try:
        with open(_WS_DOWN_FLAG, "w") as f:
            f.write(str(time.time()))
    except OSError:
        pass


# Last pre-dispatch message from the WS daemon (e.g. "bridge not connected:
# ws handshake failed: HTTP/1.1 401 Unauthorized"). _ws_exec returns None on
# pre-dispatch failure (the HTTPS-fallback signal), which would otherwise
# discard the daemon's diagnosis; _sysinfo_yote reads this for auth
# detection. Reset on every _ws_exec entry; meaningful only when that call
# returned None.
_ws_predispatch_error = ""


def _ws_names_auth(msg):
    """Does this WS lane message name an auth failure (401/unauthorized)?"""
    m = (msg or "").lower()
    return "401" in m or "unauthorized" in m


# Local read deadline for the HTTPS lane (finding #2, 2026-09-18): a bridge
# exec call with --timeout 25 hung ~24 MINUTES locally and died with
# IncompleteRead(2250 bytes read). --timeout bounds the REMOTE command; the
# awrawr-pc exec tool itself caps at 90s (subprocess timeout in
# awrawr_mcp.py). Nothing bounded the LOCAL read: the client sat in
# resp.read() on a broken SSE stream with no deadline. The deadline below
# bounds the total local read independently of the remote --timeout.
_HTTPS_SERVER_CEILING = 90   # mirrors awrawr_mcp.py's subprocess timeout
_READ_MARGIN = 60            # network/SSE overhead beyond the server ceiling
_DEFAULT_READ_TIMEOUT = _HTTPS_SERVER_CEILING + _READ_MARGIN  # 150s

# Degraded steady-state for the HTTPS lane, mirroring _WS_DOWN_FLAG: a lane
# that IncompleteReads, stalls mid-read, blows its read deadline, or fails
# response correlation is marked sick for _HTTPS_DOWN_TTL so the next call
# fails fast instead of burning another full read cycle. The marker
# expires on its own (recovery), and carries the reason for debuggability.
_HTTPS_DOWN_FLAG = os.path.expanduser("~/.cache/awrawr-https-down")
_HTTPS_DOWN_TTL = 60


def _https_known_down() -> tuple:
    """(down, reason): is the HTTPS lane currently marked degraded?"""
    try:
        with open(_HTTPS_DOWN_FLAG) as f:
            rec = json.load(f)
        if time.time() - float(rec.get("ts", 0)) < _HTTPS_DOWN_TTL:
            return True, str(rec.get("reason", "unknown"))
    except (OSError, ValueError, TypeError):
        pass
    return False, ""


def _https_mark_down(reason: str) -> None:
    try:
        with open(_HTTPS_DOWN_FLAG, "w") as f:
            json.dump({"ts": time.time(), "reason": reason}, f)
    except OSError:
        pass


class _ReadDeadlineExceeded(RuntimeError):
    """Local read deadline fired before the response arrived."""


class _CorrelationFailed(RuntimeError):
    """Stream ended with no JSON-RPC response matching our request id."""


def _read_sse_correlated(resp, want_id, deadline):
    """Incrementally read an SSE stream; return (doc, foreign_skipped).

    Only a JSON-RPC response envelope whose id matches want_id is
    accepted; anything else is skipped and counted. Raises
    _CorrelationFailed if the stream ends (EOF) without a match, and
    _ReadDeadlineExceeded if the deadline fires first. Transport-level
    read errors (IncompleteRead, socket.timeout) propagate to the caller
    for degraded-lane marking.
    """
    foreign = 0
    data_seen = False
    while True:
        if time.monotonic() > deadline:
            raise _ReadDeadlineExceeded(
                "local read deadline fired waiting for response id %r "
                "(%d foreign data line(s) skipped)" % (want_id, foreign))
        line = resp.readline()
        if not line:
            break  # EOF: server closed the stream
        try:
            text = line.decode("utf-8", "replace")
        except Exception:
            foreign += 1
            continue
        if not text.startswith("data:"):
            continue
        data_seen = True
        try:
            doc = json.loads(text[5:].strip())
        except ValueError:
            foreign += 1
            continue
        if want_id is _MISSING:
            return doc, foreign
        if isinstance(doc, dict) and doc.get("jsonrpc") == "2.0" \
                and doc.get("id") == want_id:
            return doc, foreign
        foreign += 1
    if want_id is _MISSING and not data_seen:
        return {}, foreign  # notification POST, empty SSE body
    raise _CorrelationFailed(
        "bridge response correlation failed: no JSON-RPC response "
        "matching request id %r (%d foreign data line(s) skipped; "
        "not retrying, command may be non-idempotent)"
        % (want_id, foreign))


def _read_body_bounded(resp, deadline, chunk_size: int = 65536) -> bytes:
    """Read a (non-SSE) response body with a local deadline.

    IncompleteRead / socket.timeout propagate to the caller for
    degraded-lane marking.
    """
    chunks = []
    while True:
        if time.monotonic() > deadline:
            raise _ReadDeadlineExceeded(
                "local read deadline fired while reading response body")
        chunk = resp.read(chunk_size)
        if not chunk:
            break
        chunks.append(chunk)
    return b"".join(chunks)


def _ws_try_once() -> socket.socket | None:
    """Single attempt at the daemon's unix socket; None on any failure."""
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect(WS_SOCK)
        return s
    except OSError:
        return None


def _ws_start_daemon():
    """Spawn the ws daemon (singleflight via bind); returns Popen or None."""
    logf = None
    try:
        logf = open(os.path.expanduser("~/.cache/awrawr-ws-bridge.log"), "a")
        env = dict(os.environ)
        # Tunnel override (2026-09-20): propagate to the daemon so it
        # routes via the public tunnel when the tailnet host is blocked.
        # Falls back to the compiled-in default if unset.
        proc = subprocess.Popen(
            [sys.executable, WS_DAEMON],
            stdin=subprocess.DEVNULL, stdout=logf, stderr=logf,
            start_new_session=True, env=env)
    except Exception:
        return None
    finally:
        if logf is not None:
            try:
                logf.close()  # child keeps its own fd copy; don't leak ours
            except Exception:
                pass
    return proc


def _ws_connect_legacy():
    """Legacy connect: socket now, else lazy-start the daemon and wait 12s.

    Returns a connected socket, or None (with _ws_predispatch_error set).
    """
    global _ws_predispatch_error
    s = _ws_try_once()
    if s is not None:
        return s
    # Lazy-start the daemon (singleflight: stale socket file is unlinked
    # by the daemon itself on start; a second starter just fails to bind
    # and the connect below still succeeds).
    proc = _ws_start_daemon()
    if proc is None:
        return None
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        s = _ws_try_once()
        if s is not None:
            break
        if proc.poll() is not None:
            # Daemon exited during start (e.g. ImportError on wsframe):
            # fail fast instead of burning the whole 12s wait.
            break
        time.sleep(0.25)
    if s is None:
        _ws_predispatch_error = "ws daemon unavailable (no socket)"
    return s


def _ws_predispatch_fast():
    """Race phase-1: connect now or not at all (no waiting).

    If the daemon socket is absent the daemon is spawned fire-and-forget
    (it heals for the next call) and this lane reports not-ready
    immediately, so the HTTPS lane can serve this call without delay.
    Returns a connected socket, or None (with _ws_predispatch_error set
    and the lane down-marked per degraded steady-state).
    """
    global _ws_predispatch_error
    _ws_predispatch_error = ""
    s = _ws_try_once()
    if s is None:
        _ws_start_daemon()  # heal in background; don't block this call
        _ws_predispatch_error = "ws daemon unavailable (spawned in background)"
        _ws_mark_down()
        return None
    return s


def _ws_exec(cmd: str, workdir: str, argv=None,
             timeout: int | None = None, capture: bool = False):
    """Run via the local ws_daemon.

    capture=False: streams chunks to stdout, returns exit code (or None to
    fall back to HTTPS). capture=True: accumulates chunks, returns a result
    dict (or None to fall back).

    Fallback contract: None = pre-dispatch failure (daemon never saw the
    command; HTTPS re-dispatch is safe). Any non-None return = the WS lane
    owns the result; post-dispatch failures return a failure WITHOUT
    falling back, so a command that may have executed remotely is never
    run twice.
    """
    global _ws_predispatch_error
    _ws_predispatch_error = ""
    if _ws_known_down():
        _ws_predispatch_error = "ws lane marked down (degraded steady-state)"
        return None  # degraded steady-state: straight to HTTPS
    s = _ws_connect_legacy()
    if s is None:
        return None
    return _ws_run(s, cmd, workdir, argv, timeout, capture)


def _ws_run(s: socket.socket, cmd: str, workdir: str, argv,
            timeout: int | None, capture: bool = False):
    """Execute one command over a connected daemon socket.

    Same fallback contract as _ws_exec: None = pre-dispatch failure (HTTPS
    re-dispatch is safe); any non-None return = the WS lane owns the
    result, so post-dispatch failures report WITHOUT falling back and a
    command that may have executed remotely is never run twice.
    """
    global _ws_predispatch_error
    t0 = time.monotonic()
    out_parts: list[str] = []
    err_parts: list[str] = []
    try:
        payload = {"workdir": workdir}
        if argv is not None:
            payload["argv"] = argv
        else:
            payload["cmd"] = cmd
        if timeout is not None:
            payload["timeout"] = timeout
        dispatched = False
        try:
            s.sendall((json.dumps(payload) + "\n").encode())
        except OSError:
            # Pre-dispatch: the payload never reached the daemon, so HTTPS
            # re-dispatch is safe. Mark the lane down briefly so a flapping
            # daemon doesn't get hammered.
            _ws_predispatch_error = "ws send to daemon failed (pre-dispatch)"
            _ws_mark_down()
            return None
        dispatched = True  # daemon now owns the command; no re-dispatch
        buf = b""
        # The socket must stay silent-tolerant for the whole requested
        # command timeout: a quiet `sleep 600` sends no chunks, and a fixed
        # 120s ceiling here would kill it before the server's own timeout.
        s.settimeout(max(TIMEOUT, (timeout or 0) + 60))
        t0 = time.monotonic()
        out_parts: list[str] = []
        err_parts: list[str] = []
        while True:
            blk = s.recv(65536)
            if not blk:
                # Silent socket close: the lane died without a frame. The
                # daemon may have dispatched before dying, so do NOT fall
                # back (no double-exec). Mark down for degraded steady-state.
                _ws_mark_down()
                msg = "ws socket closed mid-command (no retry)"
                if capture:
                    return {"code": 1, "stdout": "".join(out_parts),
                            "stderr": "".join(err_parts),
                            "duration_ms": int((time.monotonic() - t0) * 1000),
                            "transport": "ws", "error": msg,
                            "truncated": False}
                print("exec.py: " + msg, file=sys.stderr)
                return 1
            buf += blk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                if not line.strip():
                    continue
                try:
                    doc = json.loads(line.decode())
                except ValueError:
                    continue
                t = doc.get("type")
                if t == "chunk":
                    if capture:
                        tgt = err_parts if doc.get("stream") == "stderr" \
                            else out_parts
                        tgt.append(doc.get("data", ""))
                    else:
                        sys.stdout.write(doc.get("data", ""))
                        sys.stdout.flush()
                elif t == "done":
                    code = int(doc.get("code", 0))
                    if capture:
                        return {
                            "code": code,
                            "stdout": "".join(out_parts),
                            "stderr": "".join(err_parts),
                            "duration_ms": int((time.monotonic() - t0) * 1000),
                            "transport": "ws",
                            "error": doc.get("error"),
                            "truncated": bool(doc.get("truncated", False)),
                        }
                    if doc.get("error"):
                        print(doc["error"], file=sys.stderr)
                    return code
                elif t == "error":
                    msg = str(doc.get("message") or doc.get("error") or "")
                    if "may have executed" in msg or "response timeout" in msg:
                        # Post-dispatch: the daemon sent the command upstream
                        # but got no response. It MAY have executed remotely:
                        # report failure, do NOT fall back (no double-exec).
                        # Mark the lane down so the next call goes HTTPS.
                        _ws_mark_down()
                        full_msg = "ws post-dispatch failure (no retry): " + msg
                        if capture:
                            return {
                                "code": 1, "stdout": "".join(out_parts),
                                "stderr": "".join(err_parts),
                                "duration_ms": int((time.monotonic() - t0) * 1000),
                                "transport": "ws", "error": full_msg,
                                "truncated": False,
                            }
                        print("exec.py: " + full_msg, file=sys.stderr)
                        return 1
                    # Pre-dispatch ("not connected", "send failed",
                    # "reconnecting"): the daemon never sent it upstream,
                    # so HTTPS re-dispatch is safe. Keep the daemon's
                    # message: it may name the real cause (e.g. a 401).
                    _ws_predispatch_error = msg
                    _ws_mark_down()
                    return None
    except socket.timeout:
        # Post-dispatch silence: the daemon accepted the command but never
        # answered. It may have executed. Mark down, report, no fallback.
        _ws_mark_down()
        msg = "ws response timeout (no retry)"
        if capture:
            return {"code": 1, "stdout": "", "stderr": "",
                    "duration_ms": 0, "transport": "ws",
                    "error": msg, "truncated": False}
        print("exec.py: " + msg, file=sys.stderr)
        return 1
    except (OSError, ValueError):
        # The lane proved unusable. If the payload went out (dispatched),
        # the command may have executed: report, no fallback. Otherwise
        # (payload never built/sent) HTTPS re-dispatch is safe.
        _ws_mark_down()
        try:
            s.close()
        except Exception:
            pass
        if dispatched:
            msg = "ws transport failed post-dispatch (no retry)"
            if capture:
                return {"code": 1, "stdout": "".join(out_parts),
                        "stderr": "".join(err_parts),
                        "duration_ms": int((time.monotonic() - t0) * 1000),
                        "transport": "ws", "error": msg,
                        "truncated": False}
            print("exec.py: " + msg, file=sys.stderr)
            return 1
        _ws_predispatch_error = "ws lane failed pre-dispatch"
        return None


# ---------------------------------------------------------------------------
# HFT bridge race: WS vs HTTPS pre-dispatch, first-valid-wins (dispatch-gated).
#
# The hot path used to be sequential: try WS, and only on pre-dispatch
# failure fall back to HTTPS. The race runs both lanes' pre-dispatch
# CONCURRENTLY; the WS lane keeps dispatch priority while healthy
# (structurally lower per-call overhead), and only the winning lane ever
# dispatches remotely — a command can never double-execute. If the winner
# fails between selection and dispatch (still pre-dispatch), the other
# lane takes over; post-dispatch failures keep the legacy no-retry
# contract (no double-exec, ever).
#
# Every hop is measured with time.perf_counter_ns (microsecond reporting)
# and winners are appended to _RACE_LOG with tag "bridge-exec" — the same
# file the race.py skill uses, so bridge races join the fleet-wide
# winners data. Lead-with-winner: once WS has won the last
# _RACE_SKIP_STREAK races within _RACE_SKIP_MAX_AGE seconds, the race is
# skipped entirely (zero overhead: the exact legacy fast path) and
# re-raced automatically once the log goes stale.
#
# Env: AWRAWR_RACE=0         legacy sequential WS-then-HTTPS (A/B, escape hatch)
#      AWRAWR_RACE_ALWAYS=1  force racing even on a WS streak (testing)
#      AWRAWR_RACE_DEBUG=1   print per-call race timings to stderr
# ---------------------------------------------------------------------------
_RACE_LOG = os.path.expanduser("~/.cache/shingle/hft_race_winners.jsonl")
_RACE_TAG = "bridge-exec"
_RACE_PRE_TIMEOUT = 5.0    # fail-fast ceiling for the concurrent pre-dispatch
_RACE_SKIP_STREAK = 10     # skip the race after this many straight WS wins
_RACE_SKIP_MAX_AGE = 300   # ...provided the newest win is this fresh (seconds)
_RACE_FALLBACK = object()  # sentinel: nothing dispatched; run legacy path


def _https_predispatch():
    """Race phase-1: cheap HTTPS lane check.

    Returns (session_id,) — session_id may be None (cold: the full
    handshake happens in phase-2 only if HTTPS actually wins). Returns
    None when the lane is unusable (degraded steady-state).
    """
    down, _why = _https_known_down()
    if down:
        return None
    try:
        return (_load_session(),)
    except Exception:
        return None


def _https_dispatch_execute(pre, cmd, workdir, argv, timeout, read_timeout,
                            json_mode):
    """Phase-2: dispatch via HTTPS. Mirrors main()'s lane translation."""
    import shlex
    if argv is not None or timeout is not None:
        # The HTTPS fallback only speaks shell `cmd` with the server's fixed
        # ceiling. --argv is translated losslessly with shlex.join; a custom
        # --timeout drops to the server ceiling with a warning.
        if timeout is not None and not json_mode:
            print("exec.py: --timeout %d dropped; HTTPS path uses the "
                  "server ceiling" % timeout, file=sys.stderr)
        cmd = shlex.join(argv) if argv is not None else cmd
    if json_mode:
        return _https_exec_capture(cmd, workdir, read_timeout)
    return _https_exec(cmd, workdir, read_timeout)


def _future_get_before(fut, deadline):
    """Future result before a monotonic deadline; None on timeout/error."""
    try:
        return fut.result(timeout=max(0.0, deadline - time.monotonic()))
    except Exception:
        fut.cancel()
        return None


def _race_should_skip() -> bool:
    """Lead with the winner: skip racing while WS dominates the log."""
    if os.environ.get("AWRAWR_RACE_ALWAYS") == "1":
        return False
    try:
        with open(_RACE_LOG, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - 16384))
            tail = f.read().decode("utf-8", "replace").splitlines()
    except OSError:
        return False
    wins = []
    for line in reversed(tail):
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("tag") != _RACE_TAG or not e.get("winner"):
            continue
        try:
            ts = float(e.get("ts", 0))
        except (TypeError, ValueError):
            continue
        wins.append((e["winner"], ts))
        if len(wins) >= _RACE_SKIP_STREAK:
            break
    if len(wins) < 5:
        return False  # not enough data: race
    if time.time() - wins[0][1] > _RACE_SKIP_MAX_AGE:
        return False  # log stale: re-race to refresh the data
    return all(w == "ws" for w, _ in wins)


def _race_log(winner, pre, exec_times, t0_ns, t_decide_ns, t_done_ns,
              cmd, json_mode):
    """Append one winners-log entry. Best-effort: never breaks the call."""
    try:
        os.makedirs(os.path.dirname(_RACE_LOG), exist_ok=True)
        lat = {}
        for lane in ("ws", "https"):
            p = pre.get(lane) or {}
            ok = bool(p.get("ok"))
            pre_s = round(float(p.get("pre_s") or 0.0), 6)
            entry = {"ok": ok, "valid": ok, "pre_s": pre_s,
                     "latency_s": pre_s}
            if p.get("err"):
                entry["error"] = str(p["err"])[:120]
            if lane in exec_times:
                e_s = round(float(exec_times[lane]), 6)
                entry["exec_s"] = e_s
                entry["latency_s"] = round(pre_s + e_s, 6)
            lat[lane] = entry
        rec = {"ts": time.time(), "tag": _RACE_TAG, "winner": winner,
               "latency": lat,
               "decide_s": round((t_decide_ns - t0_ns) / 1e9, 6),
               "total_s": round((t_done_ns - t0_ns) / 1e9, 6),
               "cmd_chars": len(cmd or ""),
               "json_mode": bool(json_mode)}
        line = json.dumps(rec)
        with open(_RACE_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        if os.environ.get("AWRAWR_RACE_DEBUG") == "1":
            print("race " + line, file=sys.stderr)
    except OSError:
        pass


def _race_exec(cmd, workdir, argv, timeout, read_timeout, json_mode):
    """Race WS vs HTTPS pre-dispatch concurrently; the winner dispatches.

    Dispatch-gated: only the winning lane dispatches remotely, so the
    command can never double-execute. Returns the lane result (exit code
    or result dict), _RACE_FALLBACK when no lane could dispatch (nothing
    executed remotely: the caller runs the legacy path), or raises like
    the legacy path would (e.g. HTTPS degraded).
    """
    t0_ns = time.perf_counter_ns()
    pre = {}

    def ws_job():
        s = time.perf_counter_ns()
        try:
            res = _ws_predispatch_fast()
            ok, err = res is not None, None
        except Exception as e:
            res, ok, err = None, False, "%s: %s" % (type(e).__name__, e)
        pre["ws"] = {"ok": ok,
                     "pre_s": round((time.perf_counter_ns() - s) / 1e9, 6),
                     "err": err}
        return res

    def https_job():
        s = time.perf_counter_ns()
        try:
            res = _https_predispatch()
            ok, err = res is not None, None
        except Exception as e:
            res, ok, err = None, False, "%s: %s" % (type(e).__name__, e)
        pre["https"] = {"ok": ok,
                        "pre_s": round((time.perf_counter_ns() - s) / 1e9, 6),
                        "err": err}
        return res

    with ThreadPoolExecutor(max_workers=2) as ex:
        fws = ex.submit(ws_job)
        fht = ex.submit(https_job)
        deadline = time.monotonic() + _RACE_PRE_TIMEOUT
        ws_sock = _future_get_before(fws, deadline)
        https_pre = _future_get_before(fht, deadline)
    t_decide_ns = time.perf_counter_ns()

    winner = None
    exec_times = {}
    result = _RACE_FALLBACK
    if ws_sock is not None:
        # WS keeps dispatch priority while healthy: persistent connection,
        # structurally lower per-call overhead than HTTPS.
        winner = "ws"
        e0 = time.perf_counter_ns()
        try:
            result = _ws_run(ws_sock, cmd, workdir, argv, timeout, json_mode)
        finally:
            exec_times["ws"] = (time.perf_counter_ns() - e0) / 1e9
        if result is None and https_pre is not None:
            # WS failed between selection and dispatch (still pre-dispatch:
            # the daemon never saw the command), so HTTPS dispatch is safe.
            winner = "https"
            e0 = time.perf_counter_ns()
            try:
                result = _https_dispatch_execute(
                    https_pre, cmd, workdir, argv, timeout,
                    read_timeout, json_mode)
            finally:
                exec_times["https"] = (time.perf_counter_ns() - e0) / 1e9
        elif result is None:
            result = _RACE_FALLBACK
    elif https_pre is not None:
        winner = "https"
        e0 = time.perf_counter_ns()
        try:
            result = _https_dispatch_execute(
                https_pre, cmd, workdir, argv, timeout,
                read_timeout, json_mode)
        finally:
            exec_times["https"] = (time.perf_counter_ns() - e0) / 1e9
    t_done_ns = time.perf_counter_ns()
    _race_log(winner, pre, exec_times, t0_ns, t_decide_ns, t_done_ns,
              cmd, json_mode)
    return result


_MISSING = object()


def _new_id() -> str:
    """Unique JSON-RPC request id per call.

    Concurrent exec.py processes share the cached Mcp-Session-Id, so the
    old hardcoded ids (1/2) collided across callers and made response
    correlation impossible. pid + uuid makes a foreign/crossed response
    detectable instead of silently deliverable.
    """
    return "exec-%d-%s" % (os.getpid(), uuid.uuid4().hex[:12])


def _degraded_and_raise(reason: str, detail: str) -> None:
    """Mark the HTTPS lane degraded and raise a fail-fast RuntimeError."""
    _https_mark_down(reason)
    raise RuntimeError("%s (https lane marked degraded: %s; not retrying, "
                       "command may be non-idempotent)" % (detail, reason))


def _post(payload: dict, session_id: str | None,
          read_timeout: float = _DEFAULT_READ_TIMEOUT) -> tuple:
    """POST one JSON-RPC message; return (response_doc, session_id).

    Response correlation (finding #1, 2026-09-18): the shared cached
    Mcp-Session-Id is used by many concurrent exec.py processes, and the
    old code accepted the FIRST SSE `data:` line with no id check — a
    foreign/crossed response (e.g. another caller's long-poll body) was
    silently delivered as our command's output. Now: requests carry a
    unique id (_new_id), and only a JSON-RPC response envelope whose id
    matches is accepted. Foreign data lines are skipped and counted; if
    no matching response arrives the call FAILS LOUDLY (no retry — the
    command is not idempotent, so re-dispatch risks double execution).

    Local read deadline (finding #2, 2026-09-18): the total local read is
    bounded by read_timeout (default 150s = 90s server ceiling + 60s
    margin), independent of the remote --timeout. A stalled/broken stream
    raises instead of hanging; IncompleteRead / socket.timeout /
    deadline-exceeded / correlation-failed all mark the HTTPS lane
    degraded so the next call fails fast (see _HTTPS_DOWN_FLAG).
    """
    ensure_allowed_url(BASE, HOSTS)
    want_id = payload.get("id", _MISSING)
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        BASE,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
    )
    add_surrogate_to_request(req, CRED, allowed_hosts=HOSTS)
    if session_id:
        req.add_header("Mcp-Session-Id", session_id)
    try:
        resp = urllib.request.urlopen(req, timeout=_HTTPS_SOCKET_TIMEOUT)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        raise RuntimeError(f"HTTP {e.code} from bridge: {detail}")
    except (urllib.error.URLError, ConnectionError, socket.timeout) as e:
        # Finding #3 (2026-09-20): connect-path failures (DNS failure,
        # connection refused, connect stall) never marked the HTTPS lane
        # degraded, so every call burned the full socket timeout again
        # before failing. Mark the lane sick and fail fast, like read
        # stalls do. (No retry anywhere here, so no double-exec risk.)
        _degraded_and_raise(
            "connect failure: %s" % type(e).__name__,
            "https connect failed (%s: %s)"
            % (type(e).__name__, e))
    deadline = time.monotonic() + read_timeout
    with resp:
        ctype = resp.headers.get("Content-Type", "")
        sid = resp.headers.get("Mcp-Session-Id") or session_id
        if "text/event-stream" in ctype:
            try:
                doc, _foreign = _read_sse_correlated(resp, want_id,
                                                     deadline)
            except _ReadDeadlineExceeded as e:
                _degraded_and_raise("read deadline exceeded",
                                    "https read deadline exceeded: %s" % e)
            except _CorrelationFailed as e:
                _degraded_and_raise("correlation failed", str(e))
            except (http.client.IncompleteRead, socket.timeout) as e:
                _degraded_and_raise(
                    "read stall: %s" % type(e).__name__,
                    "https transport read stall (%s: %s)"
                    % (type(e).__name__, e))
            return doc, sid
        try:
            raw = _read_body_bounded(resp, deadline)
        except _ReadDeadlineExceeded as e:
            _degraded_and_raise("read deadline exceeded",
                                "https read deadline exceeded: %s" % e)
        except (http.client.IncompleteRead, socket.timeout) as e:
            _degraded_and_raise(
                "read stall: %s" % type(e).__name__,
                "https transport read stall (%s: %s)"
                % (type(e).__name__, e))
        try:
            doc = json.loads(raw.decode("utf-8")) if raw.strip() else {}
        except ValueError:
            return {}, sid  # e.g. 202 empty body on notifications
        if want_id is not _MISSING and not (
                isinstance(doc, dict) and doc.get("jsonrpc") == "2.0"
                and doc.get("id") == want_id):
            _degraded_and_raise(
                "envelope id mismatch",
                "bridge response correlation failed: envelope is not a "
                "JSON-RPC response for request id %r" % (want_id,))
        return doc, sid


def _load_session() -> str | None:
    try:
        with open(SESSION_FILE) as f:
            return json.load(f).get("session_id")
    except Exception:
        return None


def _save_session(session_id: str) -> None:
    try:
        os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
        tmp = SESSION_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"session_id": session_id}, f)
        os.replace(tmp, SESSION_FILE)
    except Exception:
        pass


def _initialize(read_timeout: float = _DEFAULT_READ_TIMEOUT) -> str | None:
    init = {
        "jsonrpc": "2.0",
        "id": _new_id(),
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "awrawr-mcp-skill", "version": "1.1"},
        },
    }
    _, session_id = _post(init, None, read_timeout)
    _post({"jsonrpc": "2.0", "method": "notifications/initialized"},
          session_id, read_timeout)
    if session_id:
        _save_session(session_id)
    return session_id


def _read_sysinfo_file(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return ""


def _sysinfo_hatch():
    """Fresh local (hatch) vitals from /proc + sysfs. No caching: load,
    memory, thread counts and uptime can change at any moment."""
    info = {"side": "hatch", "ok": True}
    info["kernel"] = os.uname().release
    try:
        info["nproc"] = os.cpu_count()
    except OSError:
        info["nproc"] = None
    mem = {}
    for line in _read_sysinfo_file("/proc/meminfo").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].rstrip(":") in ("MemTotal",
                                                       "MemAvailable"):
            try:
                mem[parts[0].rstrip(":")] = int(parts[1])  # kB
            except ValueError:
                pass
    info["mem_total_kb"] = mem.get("MemTotal")
    info["mem_avail_kb"] = mem.get("MemAvailable")
    load = _read_sysinfo_file("/proc/loadavg").split()
    info["loadavg"] = load[:3] if len(load) >= 3 else []
    # 4th field is "running/total" kernel threads, e.g. "2/365".
    info["threads_running_total"] = load[3] if len(load) >= 4 else None
    up = _read_sysinfo_file("/proc/uptime").split()
    try:
        info["uptime_s"] = float(up[0]) if up else None
    except ValueError:
        info["uptime_s"] = None
    scheds = set()
    try:
        block_devs = os.listdir("/sys/block")
    except OSError:
        block_devs = []
    for dev in block_devs:
        s = _read_sysinfo_file(
            os.path.join("/sys/block", dev, "queue", "scheduler"))
        if s:
            scheds.add(" ".join(s.split()))
    info["io_schedulers"] = sorted(scheds)
    return info


# Labeled-line probe executed ON yote; parsed back by
# _sysinfo_parse_probe. Same fields as _sysinfo_hatch.
_SYSINFO_PROBE = (
    "echo \"kernel=$(uname -r)\"; "
    "echo \"nproc=$(nproc)\"; "
    "awk '/^MemTotal:/{t=$2} /^MemAvailable:/{a=$2} "
    "END{print \"mem_total_kb=\"t; print \"mem_avail_kb=\"a}' /proc/meminfo; "
    "echo \"loadavg=$(cat /proc/loadavg)\"; "
    "echo \"uptime_s=$(cut -d' ' -f1 /proc/uptime)\"; "
    "echo \"io_sched=$(cat /sys/block/*/queue/scheduler 2>/dev/null"
    " | sort -u | tr '\\n' ';')\""
)


def _sysinfo_parse_probe(stdout):
    parsed = {}
    for line in stdout.splitlines():
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip()
        if k in ("nproc", "mem_total_kb", "mem_avail_kb"):
            try:
                v = int(v)
            except ValueError:
                pass
        elif k == "uptime_s":
            try:
                v = float(v)
            except ValueError:
                pass
        elif k == "loadavg":
            v = v.split()[:3]
        elif k == "io_sched":
            v = [s for s in v.split(";") if s]
        parsed[k] = v
    return parsed


def _sysinfo_yote(read_timeout):
    """Fresh yote vitals through the exec bridge. Never raises.

    Lane contract honored: the WS lane returns None pre-dispatch (safe to
    fall back to HTTPS); any non-None WS result is owned by that lane and
    is never re-dispatched, so the probe can never double-execute.

    Auth detection: the daemon owns the TLS handshake, so a token mismatch
    surfaces as its pre-dispatch message ("bridge not connected: ws
    handshake failed: HTTP/1.1 401 Unauthorized"), which _ws_exec stashes in
    _ws_predispatch_error instead of discarding it with the None return."""
    probe = _SYSINFO_PROBE
    workdir = "/home/toxic"
    result = None
    if os.environ.get("AWRAWR_TRANSPORT", "ws") != "https":
        try:
            result = _ws_exec(probe, workdir, None, None, capture=True)
        except Exception as e:
            result = {"code": 1, "stdout": "", "stderr": "",
                      "error": "ws lane exception: %s" % e}
    if result is None and not _ws_names_auth(_ws_predispatch_error) \
            and "never connected" in _ws_predispatch_error:
        # Fresh-daemon race: the handshake may not have resolved when the
        # first probe landed. One bounded pre-dispatch re-probe after it
        # settles (nothing was dispatched: no double-exec risk), bypassing
        # our own 15s down-mark for this single retry.
        time.sleep(2.0)
        try:
            os.unlink(_WS_DOWN_FLAG)
        except OSError:
            pass
        try:
            result = _ws_exec(probe, workdir, None, None, capture=True)
        except Exception as e:
            result = {"code": 1, "stdout": "", "stderr": "",
                      "error": "ws lane exception: %s" % e}
    if result is None:
        # WS gave up pre-dispatch; we now fail on the HTTPS lane, but a 401
        # would have happened on the WS lane -- check the daemon's message.
        ws_msg = _ws_predispatch_error.lower()
        auth_failed = "401" in ws_msg or "unauthorized" in ws_msg
        down, why = _https_known_down()
        if down:
            err = "https lane degraded (%s)" % why
            if auth_failed:
                err += "; yote also rejected credentials (401)"
            return {"side": "yote", "ok": False,
                    "auth_failed": auth_failed, "error": err}
        try:
            result = _https_exec_capture(probe, workdir, read_timeout)
        except Exception as e:
            if auth_failed:
                err = ("yote rejected credentials (401): possibly transient "
                       "(observed self-heal within ~3 min); if persistent, "
                       "token mismatch -- resubmit the exact value of "
                       "~/.awrawr_mcp_token via the connector")
            else:
                err = "https lane exception: %s" % str(e)[:160]
            return {"side": "yote", "ok": False,
                    "auth_failed": auth_failed, "error": err}
    info = {"side": "yote", "transport": result.get("transport"),
            "auth_failed": False,
            "ok": result.get("code", 1) == 0 and not result.get("error")}
    if not info["ok"]:
        err_text = ("%s %s %s" % (result.get("error") or "",
                                  result.get("stderr") or "",
                                  _ws_predispatch_error)).lower()
        auth_failed = "401" in err_text or "unauthorized" in err_text
        info["auth_failed"] = auth_failed
        if auth_failed:
            info["error"] = ("yote rejected credentials (401): possibly "
                             "transient (observed self-heal within ~3 min); "
                             "if persistent, token mismatch -- resubmit the "
                             "exact value of ~/.awrawr_mcp_token via the "
                             "connector")
        else:
            info["error"] = (result.get("error")
                             or (result.get("stderr") or "")[:160]
                             or "yote command failed")
        return info
    info.update(_sysinfo_parse_probe(result.get("stdout", "")))
    return info


def _utc_ts():
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _sysinfo_snapshot(read_timeout):
    return {
        "ts": _utc_ts(),
        "hatch": _sysinfo_hatch(),
        "yote": _sysinfo_yote(read_timeout),
    }


def _sysinfo_loop(interval, read_timeout):
    """Dynamic polling loop: one fresh both-sides snapshot per interval.

    No-overlap: if a cycle overruns the interval, the next starts after a
    short breather instead of stacking up."""
    try:
        while True:
            t0 = time.monotonic()
            print(json.dumps(_sysinfo_snapshot(read_timeout)), flush=True)
            time.sleep(max(0.5, interval - (time.monotonic() - t0)))
    except KeyboardInterrupt:
        pass
    return 0


# ---------------------------------------------------------------------------
# --watch: the agentic event stream.
#
# --poll streams full snapshots blindly; --watch emits NDJSON *events* so an
# agent can tail the stream and react instead of re-parsing everything:
#   snapshot   first full both-sides snapshot (the baseline)
#   change     field(s) moved beyond noise tolerance; carries before/after
#   alert      an --alert-* threshold was breached or cleared (hysteresis)
#   error      a side failed: first occurrence, or the error text changed
#   recovered  a side came back after failing (with downtime_s)
#   heartbeat  every 60s: liveness, per-side ok, cycle/overrun counters
#
# Edge cases, integrated:
# - No-overlap polling: an overrunning cycle never stacks; it is counted.
# - Auth-failure backoff: 401s are often transient (self-healing blips ~3 min
#   observed per AGENTS.md), so a yote leg that fails auth re-probes at most
#   every 60s instead of every cycle; escalate to "resubmit token" only if
#   the 401 survives the transient window.
# - No error spam: repeated identical failures emit nothing new; only
#   transitions (and heartbeats) speak.
# - No threshold flapping: alerts use hysteresis (load clears at 90% of
#   the breach level; memory clears 5 points above it).
# - Noisy counters don't spam: loadavg needs a 0.25 move, mem_available a
#   5% move, the running-thread count is ignored (only the total matters),
#   and monotonic uptime_s is excluded from change detection entirely.
# - Ctrl-C exits 0. Every line is one valid JSON object (pipe-safe).
# ---------------------------------------------------------------------------
_WATCH_HEARTBEAT_S = 60.0
_WATCH_AUTH_RETRY_S = 60.0
_WATCH_NOISE_LOAD = 0.25    # max abs move across loadavg to count
_WATCH_NOISE_MEM = 0.05     # mem_avail_kb move, relative to mem_total_kb
_WATCH_SKIP_FIELDS = {"uptime_s"}  # monotonic: would fire every cycle


def _watch_flat(info):
    """Flatten one side snapshot to comparable fields for change detection."""
    flat = {}
    for k, v in info.items():
        if k == "side" or k in _WATCH_SKIP_FIELDS:
            continue
        if k == "loadavg":
            try:
                flat[k] = tuple(float(x) for x in v)
            except (TypeError, ValueError):
                flat[k] = None
        elif k == "threads_running_total" and isinstance(v, str) \
                and "/" in v:
            # "running/total": the running count jitters every cycle; the
            # total is the signal (a climbing total means a thread leak).
            flat[k] = v.split("/", 1)[1]
        elif isinstance(v, list):
            flat[k] = tuple(v)
        else:
            flat[k] = v
    return flat


def _watch_significant(field, before, after, info):
    """True if a before->after move on field is a real change, not noise."""
    if before == after:
        return False
    if before is None or after is None:
        return True  # appeared / disappeared
    if field == "loadavg":
        try:
            return max(abs(a - b)
                       for a, b in zip(before, after)) > _WATCH_NOISE_LOAD
        except TypeError:
            return True
    if field == "mem_avail_kb":
        total = info.get("mem_total_kb") or 0
        try:
            if total:
                return abs(after - before) > _WATCH_NOISE_MEM * total
        except TypeError:
            pass
        return True
    return True


def _watch_diffs(prev_flat, cur_flat, cur_info):
    diffs = []
    for field in sorted(set(prev_flat) | set(cur_flat)):
        b, a = prev_flat.get(field), cur_flat.get(field)
        if _watch_significant(field, b, a, cur_info):
            diffs.append({"field": field, "before": b, "after": a})
    return diffs


def _watch_alerts(side, info, states, alert_load, alert_mem, ts):
    """Threshold transitions with hysteresis; events only on transitions."""
    events = []
    if alert_load is None and alert_mem is None:
        return events
    try:
        load1 = float((info.get("loadavg") or [None])[0])
    except (TypeError, ValueError, IndexError):
        load1 = None
    total = info.get("mem_total_kb")
    avail = info.get("mem_avail_kb")
    try:
        mem_pct = (100.0 * avail / total) \
            if total and avail is not None else None
    except TypeError:
        mem_pct = None
    checks = []
    if alert_load is not None and load1 is not None:
        checks.append(("load1", round(load1, 2), alert_load,
                       load1 > alert_load, load1 <= alert_load * 0.9))
    if alert_mem is not None and mem_pct is not None:
        checks.append(("mem_avail_pct", round(mem_pct, 1), alert_mem,
                       mem_pct < alert_mem, mem_pct >= alert_mem + 5.0))
    for metric, value, thr, is_breach, is_clear in checks:
        key = (side, metric)
        prev_state = states.get(key, "ok")
        if is_breach and prev_state != "breach":
            states[key] = "breach"
            events.append({"event": "alert", "ts": ts, "side": side,
                           "metric": metric, "state": "breach",
                           "value": value, "threshold": thr})
        elif is_clear and prev_state == "breach":
            states[key] = "ok"
            events.append({"event": "alert", "ts": ts, "side": side,
                           "metric": metric, "state": "cleared",
                           "value": value, "threshold": thr})
    return events


def _watch_loop(interval, read_timeout, alert_load, alert_mem):
    """Agentic event stream over both sides. Ctrl-C exits 0."""
    def emit(ev):
        print(json.dumps(ev), flush=True)

    snap = _sysinfo_snapshot(read_timeout)
    emit({"event": "snapshot", "ts": snap["ts"],
          "hatch": snap["hatch"], "yote": snap["yote"]})
    prev = {s: _watch_flat(snap[s]) for s in ("hatch", "yote")}
    state = {}
    now = time.time()
    for s in ("hatch", "yote"):
        ok = bool(snap[s].get("ok", True))
        state[s] = {"ok": ok,
                    "fail_n": 0,
                    "last_error": snap[s].get("error"),
                    "down_since": None if ok else now,
                    "auth_backoff": bool(snap[s].get("auth_failed")),
                    "next_retry": now + _WATCH_AUTH_RETRY_S
                    if snap[s].get("auth_failed") else 0.0}
    alert_states = {}
    cycles = 0
    overruns = 0
    next_heartbeat = time.monotonic() + _WATCH_HEARTBEAT_S
    try:
        while True:
            t0 = time.monotonic()
            now = time.time()
            ts = _utc_ts()
            infos = {}
            for s in ("hatch", "yote"):
                st = state[s]
                if not st["ok"] and st["auth_backoff"] \
                        and now < st["next_retry"]:
                    # Auth failures may be transient (self-healing blips ~3 min
                    # observed per AGENTS.md): hold the last error,
                    # re-probe at most every _WATCH_AUTH_RETRY_S; escalate to
                    # token resubmit only if the 401 survives the transient
                    # window.
                    infos[s] = {"side": s, "ok": False,
                                "backoff": True,
                                "error": st["last_error"]}
                    continue
                info = _sysinfo_hatch() if s == "hatch" \
                    else _sysinfo_yote(read_timeout)
                infos[s] = info
                ok = bool(info.get("ok", True))
                err = info.get("error")
                auth = bool(info.get("auth_failed"))
                if ok and not st["ok"]:
                    emit({"event": "recovered", "ts": ts, "side": s,
                          "downtime_s": round(now - (st["down_since"] or now),
                                              1)})
                    st.update(ok=True, fail_n=0, last_error=None,
                              down_since=None, auth_backoff=False,
                              next_retry=0.0)
                elif not ok:
                    if st["ok"]:
                        st["down_since"] = now
                    st["fail_n"] += 1
                    if err != st["last_error"] or st["ok"]:
                        emit({"event": "error", "ts": ts, "side": s,
                              "error": err, "auth_failed": auth,
                              "fail_n": st["fail_n"]})
                    st["last_error"] = err
                    st["ok"] = False
                    if auth:
                        st["auth_backoff"] = True
                        st["next_retry"] = now + _WATCH_AUTH_RETRY_S
                else:
                    st["fail_n"] = 0
            for s in ("hatch", "yote"):
                info = infos[s]
                if not info.get("ok"):
                    continue
                flat = _watch_flat(info)
                diffs = _watch_diffs(prev.get(s, {}), flat, info)
                if diffs:
                    emit({"event": "change", "ts": ts, "side": s,
                          "diffs": diffs})
                prev[s] = flat
                for ev in _watch_alerts(s, info, alert_states,
                                        alert_load, alert_mem, ts):
                    emit(ev)
            cycles += 1
            if time.monotonic() >= next_heartbeat:
                emit({"event": "heartbeat", "ts": ts, "cycles": cycles,
                      "overruns": overruns,
                      "hatch_ok": state["hatch"]["ok"],
                      "yote_ok": state["yote"]["ok"]})
                next_heartbeat = time.monotonic() + _WATCH_HEARTBEAT_S
            if time.monotonic() - t0 > interval:
                overruns += 1
            time.sleep(max(0.5, interval - (time.monotonic() - t0)))
    except KeyboardInterrupt:
        pass
    return 0


def main() -> int:
    # exec.py "cmd" [workdir]
    # exec.py --argv cmd arg... [--timeout N] [--read-timeout SECS] [--json]
    # exec.py --sysinfo | --poll [SECS] | --watch [SECS]
    #   --watch takes --alert-load N (1m loadavg) and --alert-mem PCT
    args = sys.argv[1:]
    timeout = None
    json_mode = False
    read_timeout = _DEFAULT_READ_TIMEOUT
    if "--json" in args:
        json_mode = True
        args.remove("--json")
    if "--timeout" in args:
        i = args.index("--timeout")
        try:
            timeout = int(args[i + 1])
        except (IndexError, ValueError):
            print("exec.py: --timeout needs an integer", file=sys.stderr)
            return 2
        del args[i:i + 2]
    if "--read-timeout" in args:
        i = args.index("--read-timeout")
        try:
            read_timeout = int(args[i + 1])
            if read_timeout <= 0:
                raise ValueError
        except (IndexError, ValueError):
            print("exec.py: --read-timeout needs a positive integer "
                  "(seconds)", file=sys.stderr)
            return 2
        del args[i:i + 2]
    sysinfo_once = False
    if "--sysinfo" in args:
        sysinfo_once = True
        args.remove("--sysinfo")
    poll_interval = None
    if "--poll" in args:
        i = args.index("--poll")
        try:
            poll_interval = float(args[i + 1])
            if poll_interval <= 0:
                raise ValueError
            del args[i:i + 2]
        except (IndexError, ValueError):
            # Bare --poll (or a non-numeric next arg): default 5s, keep the
            # next arg for the normal command path (a mode flag still wins).
            poll_interval = 5.0
            del args[i:i + 1]
    watch_interval = None
    if "--watch" in args:
        i = args.index("--watch")
        try:
            watch_interval = float(args[i + 1])
            if watch_interval <= 0:
                raise ValueError
            del args[i:i + 2]
        except (IndexError, ValueError):
            watch_interval = 5.0
            del args[i:i + 1]
    alert_load = None
    if "--alert-load" in args:
        i = args.index("--alert-load")
        try:
            alert_load = float(args[i + 1])
            if alert_load <= 0:
                raise ValueError
        except (IndexError, ValueError):
            print("exec.py: --alert-load needs a positive number",
                  file=sys.stderr)
            return 2
        del args[i:i + 2]
    alert_mem = None
    if "--alert-mem" in args:
        i = args.index("--alert-mem")
        try:
            alert_mem = float(args[i + 1])
            if not 0 < alert_mem < 100:
                raise ValueError
        except (IndexError, ValueError):
            print("exec.py: --alert-mem needs a percent between 0 and 100",
                  file=sys.stderr)
            return 2
        del args[i:i + 2]
    modes = [sysinfo_once, poll_interval is not None,
             watch_interval is not None]
    if sum(1 for m in modes if m) > 1:
        print("exec.py: --sysinfo, --poll and --watch are mutually "
              "exclusive", file=sys.stderr)
        return 2
    if sysinfo_once:
        print(json.dumps(_sysinfo_snapshot(read_timeout)), flush=True)
        return 0
    if poll_interval is not None:
        return _sysinfo_loop(poll_interval, read_timeout)
    if watch_interval is not None:
        return _watch_loop(watch_interval, read_timeout,
                           alert_load, alert_mem)
    argv = None
    if args and args[0] == "--argv":
        argv = args[1:]
        cmd = ""
        workdir = "/home/toxic"
    else:
        cmd = args[0] if len(args) > 0 else "echo ok"
        workdir = args[1] if len(args) > 1 else "/home/toxic"

    # Transport selection. AWRAWR_TRANSPORT=https forces the legacy HTTPS
    # path (debugging). AWRAWR_RACE=0 forces the legacy sequential
    # WS-then-HTTPS path (A/B testing, escape hatch). Otherwise the HFT
    # race runs when both lanes are nominally healthy; a degraded lane
    # (down-markers) or a dominant WS winners-log streak takes the exact
    # legacy path instead — zero behavior change when racing can't help.
    transport = os.environ.get("AWRAWR_TRANSPORT", "ws")
    race_on = os.environ.get("AWRAWR_RACE", "1") != "0"
    result = None
    if transport != "https":
        down_ws = _ws_known_down()
        down_https, _ = _https_known_down()
        if (race_on and not down_ws and not down_https
                and not _race_should_skip()):
            result = _race_exec(cmd, workdir, argv, timeout, read_timeout,
                                json_mode)
            if result is _RACE_FALLBACK:
                result = None  # nothing dispatched: run the legacy path
        if result is None:
            result = _ws_exec(cmd, workdir, argv, timeout, capture=json_mode)
    if not json_mode:
        if result is not None:
            return result
    elif result is not None:
        return _emit_json(result)
    # Degraded steady-state for the HTTPS lane: a lane that recently
    # IncompleteRead, stalled, blew its read deadline, or failed
    # correlation is skipped fast instead of burning another full read
    # cycle; the marker expires on its own (recovery).
    down, why = _https_known_down()
    if down:
        raise RuntimeError(
            "https transport degraded (%s); failing fast, retry shortly"
            % why)
    if argv is not None or timeout is not None:
        # The HTTPS fallback only speaks shell `cmd` with the server's fixed
        # ceiling. --argv is translated losslessly with shlex.join so the
        # remote argv is byte-identical (raced: shlex.join round-trip verified
        # against the WS daemon path). A custom --timeout is dropped to the
        # server ceiling with a warning instead of refusing outright —
        # refusing a working transport is a defect, not a feature.
        import shlex
        if timeout is not None and not json_mode:
            print("exec.py: --timeout %d dropped; HTTPS path uses the "
                  "server ceiling" % timeout, file=sys.stderr)
        cmd = shlex.join(argv) if argv is not None else cmd
        argv = None
        timeout = None
    # Fall through to the HTTPS path only when the WS daemon is unavailable.
    if json_mode:
        return _emit_json(_https_exec_capture(cmd, workdir, read_timeout))
    return _https_exec(cmd, workdir, read_timeout)


def _emit_json(result: dict) -> int:
    """Print one structured result object; cap runaway outputs."""
    out, err = result.get("stdout", ""), result.get("stderr", "")
    truncated = bool(result.get("truncated"))
    if len(out) + len(err) > 200_000:
        keep = 200_000
        out = out[:keep]
        err = err[: max(0, keep - len(out))]
        truncated = True
    result = dict(result)
    result["stdout"], result["stderr"], result["truncated"] = out, err, truncated
    result["ok"] = result.get("code", 1) == 0 and not result.get("error")
    print(json.dumps(result))
    return 0


def _https_exec_capture(cmd: str, workdir: str,
                        read_timeout: float = _DEFAULT_READ_TIMEOUT) -> dict:
    """HTTPS fallback returning a result dict instead of printing."""
    t0 = time.monotonic()
    buf: list[str] = []
    code = _https_exec(cmd, workdir, read_timeout, _sink=buf.append)
    return {
        "code": code,
        "stdout": "".join(buf),
        "stderr": "",
        "duration_ms": int((time.monotonic() - t0) * 1000),
        "transport": "https",
        "error": None,
    }


def _https_exec(cmd: str, workdir: str,
                read_timeout: float = _DEFAULT_READ_TIMEOUT,
                _sink=None) -> int:
    import re
    out = _sink or (lambda s: print(s))
    session_id = _load_session()
    if not session_id:
        session_id = _initialize(read_timeout)

    call = {
        "jsonrpc": "2.0",
        "id": _new_id(),
        "method": "tools/call",
        "params": {
            "name": "exec",
            "arguments": {"cmd": cmd, "workdir": workdir},
        },
    }
    try:
        result, _ = _post(call, session_id, read_timeout)
    except RuntimeError as e:
        # Stale/dead session (server restarted) -> full handshake, one retry.
        # (Deadline/correlation/degraded failures never contain HTTP 400/404
        # and are never retried: the command may be non-idempotent.)
        if session_id and ("HTTP 400" in str(e) or "HTTP 404" in str(e)):
            session_id = _initialize(read_timeout)
            result, _ = _post(call, session_id, read_timeout)
        else:
            raise
    if "error" in result:
        # Some servers report unknown-session as a JSON-RPC error instead.
        err = result["error"]
        if session_id and err.get("code") in (-32000, -32600):
            session_id = _initialize(read_timeout)
            result, _ = _post(call, session_id, read_timeout)
        if "error" in result:
            print(f"RPC error: {result['error']}", file=sys.stderr)
            return 1
    res = result.get("result", {})
    code = None
    for block in res.get("content", []):
        if isinstance(block, dict) and "text" in block:
            text = block["text"]
            # The legacy MCP exec tool reports the remote exit in a
            # "[exit=N] ..." wrapper instead of isError; propagate it.
            m = re.match(r"\[exit=(\d+)\]\s*", text)
            if m:
                code = int(m.group(1))
                text = text[m.end():]
            out(text)
    if code is None:
        code = 1 if res.get("isError") else 0
    return code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"awrawr-mcp: {e}", file=sys.stderr)
        sys.exit(2)
