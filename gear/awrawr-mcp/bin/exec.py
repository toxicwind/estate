#!/usr/bin/env python3
"""Run a shell command on awrawr-pc through its MCP exec bridge.

Usage:
    exec.py "echo ok && whoami" [workdir]

Auth: Secure Vault connector custom.awrawr-mcp. The raw token is never
readable here; only its hsurr:* surrogate is sent, and only to the bridge
host. The surrogate travels in the X-MCP-Token header (the connector's
placement), which is the bridge's auth boundary. Sentinel swaps the
surrogate for the real credential on approved egress.

Performance: transport priority is
  1. local ws_daemon (one persistent wss:// connection to /exec-ws, ~0.1-0.3s
     per call, live streaming stdout/stderr) — started lazily on first use;
  2. HTTPS MCP with cached session id (~0.6s) as fallback.
A stale session falls back to a full handshake automatically.

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

sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import (
    add_surrogate_to_request,
    ensure_allowed_url,
)

CRED = "custom.awrawr-mcp"
HOSTS = ["github-mcp-host.tailc9ac71.ts.net"]
BASE = "https://github-mcp-host.tailc9ac71.ts.net/mcp"
TIMEOUT = 120
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
    if _ws_known_down():
        return None  # degraded steady-state: straight to HTTPS
    t0 = time.monotonic()
    out_parts: list[str] = []
    err_parts: list[str] = []
    def try_once() -> socket.socket | None:
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect(WS_SOCK)
            return s
        except OSError:
            return None

    s = try_once()
    if s is None:
        # Lazy-start the daemon (singleflight: stale socket file is unlinked
        # by the daemon itself on start; a second starter just fails to bind
        # and the connect below still succeeds).
        try:
            logf = open(os.path.expanduser("~/.cache/awrawr-ws-bridge.log"),
                        "a")
            subprocess.Popen(
                [sys.executable, WS_DAEMON],
                stdin=subprocess.DEVNULL, stdout=logf, stderr=logf,
                start_new_session=True)
        except Exception:
            return None
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            s = try_once()
            if s is not None:
                break
            time.sleep(0.25)
        if s is None:
            return None
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
                    # so HTTPS re-dispatch is safe.
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
        return None
        try:
            s.close()
        except Exception:
            pass


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
        resp = urllib.request.urlopen(req, timeout=TIMEOUT)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        raise RuntimeError(f"HTTP {e.code} from bridge: {detail}")
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


def main() -> int:
    # exec.py "cmd" [workdir]
    # exec.py --argv cmd arg... [--timeout N] [--read-timeout SECS] [--json]
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
    argv = None
    if args and args[0] == "--argv":
        argv = args[1:]
        cmd = ""
        workdir = "/home/toxic"
    else:
        cmd = args[0] if len(args) > 0 else "echo ok"
        workdir = args[1] if len(args) > 1 else "/home/toxic"

    # AWRAWR_TRANSPORT=https forces the legacy HTTPS path (debugging/race).
    result = None
    if os.environ.get("AWRAWR_TRANSPORT", "ws") != "https":
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
