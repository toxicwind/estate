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
"""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error

sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import (
    add_surrogate_to_request,
    ensure_allowed_url,
    read_json_response,
)

CRED = "custom.awrawr-mcp"
HOSTS = ["github-mcp-host.tailc9ac71.ts.net"]
BASE = "https://github-mcp-host.tailc9ac71.ts.net/mcp"
TIMEOUT = 120
SESSION_FILE = os.path.expanduser("~/.cache/awrawr-mcp-session.json")
WS_SOCK = os.path.expanduser("~/.cache/awrawr-ws-bridge.sock")
WS_DAEMON = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "ws_daemon.py")


def _ws_exec(cmd: str, workdir: str, argv=None,
             timeout: int | None = None) -> int | None:
    """Run via the local ws_daemon. Returns exit code, or None to fall back."""
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
        s.sendall((json.dumps(payload) + "\n").encode())
        buf = b""
        # The socket must stay silent-tolerant for the whole requested
        # command timeout: a quiet `sleep 600` sends no chunks, and a fixed
        # 120s ceiling here would kill it before the server's own timeout.
        s.settimeout(max(TIMEOUT, (timeout or 0) + 60))
        while True:
            blk = s.recv(65536)
            if not blk:
                return None
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
                    sys.stdout.write(doc.get("data", ""))
                    sys.stdout.flush()
                elif t == "done":
                    if doc.get("error"):
                        print(doc["error"], file=sys.stderr)
                    return int(doc.get("code", 0))
                elif t == "error":
                    return None  # bridge down -> HTTPS fallback
    except (OSError, ValueError):
        return None
    finally:
        try:
            s.close()
        except Exception:
            pass


def _post(payload: dict, session_id: str | None) -> tuple[dict, str | None]:
    ensure_allowed_url(BASE, HOSTS)
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
    with resp:
        ctype = resp.headers.get("Content-Type", "")
        sid = resp.headers.get("Mcp-Session-Id") or session_id
        if "text/event-stream" in ctype:
            raw = resp.read().decode("utf-8", "replace")
            for line in raw.splitlines():
                if line.startswith("data:"):
                    return json.loads(line[5:].strip()), sid
            return {}, sid
        try:
            return read_json_response(resp), sid
        except Exception:
            return {}, sid  # e.g. 202 empty body on notifications


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


def _initialize() -> str | None:
    init = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "awrawr-mcp-skill", "version": "1.1"},
        },
    }
    _, session_id = _post(init, None)
    _post({"jsonrpc": "2.0", "method": "notifications/initialized"}, session_id)
    if session_id:
        _save_session(session_id)
    return session_id


def main() -> int:
    # exec.py "cmd" [workdir] | exec.py --argv cmd arg... [--timeout N]
    args = sys.argv[1:]
    timeout = None
    if "--timeout" in args:
        i = args.index("--timeout")
        try:
            timeout = int(args[i + 1])
        except (IndexError, ValueError):
            print("exec.py: --timeout needs an integer", file=sys.stderr)
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
    rc = None
    if os.environ.get("AWRAWR_TRANSPORT", "ws") != "https":
        rc = _ws_exec(cmd, workdir, argv, timeout)
    if rc is not None:
        return rc
    if argv is not None or timeout is not None:
        # The HTTPS fallback only speaks shell `cmd` with the server's fixed
        # ceiling: it cannot honor --argv (would run an EMPTY command) or a
        # custom timeout. Fail loudly instead of silently losing semantics.
        print("exec.py: WS bridge unavailable; --argv/--timeout require it, "
              "refusing HTTPS fallback", file=sys.stderr)
        return 3
    # Fall through to the HTTPS path only when the WS daemon is unavailable.
    return _https_exec(cmd, workdir)


def _https_exec(cmd: str, workdir: str) -> int:
    session_id = _load_session()
    if not session_id:
        session_id = _initialize()

    call = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "exec",
            "arguments": {"cmd": cmd, "workdir": workdir},
        },
    }
    try:
        result, _ = _post(call, session_id)
    except RuntimeError as e:
        # Stale/dead session (server restarted) -> full handshake, one retry.
        if session_id and ("HTTP 400" in str(e) or "HTTP 404" in str(e)):
            session_id = _initialize()
            result, _ = _post(call, session_id)
        else:
            raise
    if "error" in result:
        # Some servers report unknown-session as a JSON-RPC error instead.
        err = result["error"]
        if session_id and err.get("code") in (-32000, -32600):
            session_id = _initialize()
            result, _ = _post(call, session_id)
        if "error" in result:
            print(f"RPC error: {result['error']}", file=sys.stderr)
            return 1
    res = result.get("result", {})
    for block in res.get("content", []):
        if isinstance(block, dict) and "text" in block:
            print(block["text"])
    return 1 if res.get("isError") else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"awrawr-mcp: {e}", file=sys.stderr)
        sys.exit(2)
