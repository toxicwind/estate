#!/usr/bin/env python3
"""squawk-feed: bearer-authed fat long-poll for Squawk (stdlib only).

Endpoints (all under /squawk-feed):

  GET /squawk-feed/ping                public, content-free -> {"seq": N}
  GET /squawk-feed/wait?since=N        bearer auth -> {"seq": M, "messages": [...]}
  GET /squawk-feed/subscribe?since=N   same handler as /wait (alias)

Auth: `Authorization: Bearer <token>`, constant-time compare
(hmac.compare_digest); missing or invalid -> 404 with an empty body, never
revealing the endpoint exists. The token auto-configures server-style:
$ SQUAWK_FEED_TOKEN env var first, then the canonical token file
(~/.shingle/squawk-relay/feed-token), else a secure random token is
generated, persisted (0600) to the token file, and used. The server never
refuses to start for a missing token -- it is a server, it configures
itself. Additional keys for future use go in the settings file
(~/.shingle/squawk-relay/settings.conf, KEY=VALUE lines). The token is
never logged and never committed.

Fat response: {"seq": M, "messages": [relay-record envelopes, ...]} where
every envelope carries its own per-message "seq". Messages with seq >
since, oldest first, capped at 50 per response; the returned "seq" is the
seq of the LAST message in the batch, so the client re-polls with it to
drain the rest. Each message text is truncated to 500 chars. Sealed
messages are unsealed server-side with the relay identity (the hosting
lane provisions relay.seal.key); unopenable ones ride as
{"sealed": true, "body": null} -- ciphertext is never served.

Wake: Linux inotify on the channel dir bumps the high-water mark the
instant a post lands; parked long-polls (hold ~55s) answer immediately.
Timeout with no new messages -> {"seq": <current>, "messages": []}.

HARD RULE: no unauthenticated unsealed content, ever. No exceptions.
"""

import argparse
import ctypes
import ctypes.util
import hmac
import http.server
import json
import os
import re
import secrets
import select
import socketserver
import sys
import threading
import urllib.parse
from pathlib import Path

import fleet_relay

# ---------------------------------------------------------------------------
# process/boot/exit telemetry (2026-09-18)
# Logs boot ID, PID, PPID, start/exit times to distinguish clean exits from
# crashes and correlate PID transitions with cell recycles (boots).
# ---------------------------------------------------------------------------
import atexit
import signal
import time

TELEMETRY_LOG = Path("/home/toxic/.local/state/squawk-feed/telemetry.jsonl")
_telemetry_start_wall = time.time()
_telemetry_start_mono = time.monotonic()

def _boot_id():
    try:
        return Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    except Exception:
        return "unknown"

def _telemetry_emit(event, **fields):
    try:
        TELEMETRY_LOG.parent.mkdir(parents=True, exist_ok=True)
        rec = {
            "event": event,
            "boot_id": _boot_id(),
            "pid": os.getpid(),
            "ppid": os.getppid(),
            "wall": time.time(),
            "mono": time.monotonic(),
        }
        rec.update(fields)
        with open(TELEMETRY_LOG, "a") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception:
        pass  # telemetry never breaks the server

def _telemetry_start():
    _telemetry_emit("start",
        start_wall=_telemetry_start_wall,
        start_mono=_telemetry_start_mono)

def _telemetry_exit(exit_code=None, sig=None, exc=None):
    cls = "clean" if (exit_code in (0, None) and sig is None and exc is None) else "abnormal"
    _telemetry_emit("exit",
        exit_code=exit_code, signal=sig,
        exception=str(exc)[:500] if exc else None,
        classification=cls,
        uptime_wall=time.time() - _telemetry_start_wall,
        uptime_mono=time.monotonic() - _telemetry_start_mono)

def _install_telemetry():
    _telemetry_start()
    # atexit for clean exits
    atexit.register(lambda: _telemetry_exit(exit_code=0))
    # signal handlers for abnormal termination
    orig_term = signal.getsignal(signal.SIGTERM)
    def _on_term(signum, frame):
        _telemetry_exit(sig=signum)
        # chain to default: re-raise with default handler
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        os.kill(os.getpid(), signal.SIGTERM)
    try:
        signal.signal(signal.SIGTERM, _on_term)
    except Exception:
        pass

TOKEN_ENV = "SQUAWK_FEED_TOKEN"
# Canonical token file (auto-created on first run, 0600). Overridable via
# --token-file or $SQUAWK_FEED_TOKEN_FILE. Server-like: never ask, configure.
TOKEN_FILE_DEFAULT = str(Path.home() / ".shingle" / "squawk-relay" / "feed-token")
# Settings file for future keys: KEY=VALUE lines, sourced on startup.
# Add other keys here as needed; the server reads them into the environment.
SETTINGS_FILE_DEFAULT = str(Path.home() / ".shingle" / "squawk-relay" / "settings.conf")
HOLD_SECONDS = 55.0
MAX_MESSAGES = 50
TEXT_CAP = 500
WATCH_MASK = 0x00000008 | 0x00000100  # IN_CLOSE_WRITE | IN_MOVED_TO
_MSG_RE = re.compile(r"^(\d+)-.*\.md$")


# ---------------------------------------------------------------------------
# channel tail (inotify hot path)
# ---------------------------------------------------------------------------

class _Inotify:
    """Minimal ctypes wrapper: inotify_init1 + add_watch + read."""

    def __init__(self, path: Path, mask: int):
        libc_name = ctypes.util.find_library("c") or "libc.so.6"
        self._libc = ctypes.CDLL(libc_name, use_errno=True)
        self._libc.inotify_init1.argtypes = [ctypes.c_int]
        self._libc.inotify_init1.restype = ctypes.c_int
        self._libc.inotify_add_watch.argtypes = [
            ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
        self._libc.inotify_add_watch.restype = ctypes.c_int
        fd = self._libc.inotify_init1(0)
        if fd < 0:
            raise OSError(ctypes.get_errno(), "inotify_init1 failed")
        self.fd = fd
        wd = self._libc.inotify_add_watch(
            fd, str(path).encode("utf-8"), ctypes.c_uint32(mask))
        if wd < 0:
            err = ctypes.get_errno()
            os.close(fd)
            raise OSError(err, f"inotify_add_watch failed for {path}")

    def read_events(self) -> bool:
        """Drain pending events. Returns True if anything was waiting."""
        try:
            data = os.read(self.fd, 65536)
        except BlockingIOError:
            return False
        return bool(data)

    def close(self):
        try:
            os.close(self.fd)
        except OSError:
            pass


def _channel_high(chan_dir: Path) -> int:
    top = 0
    try:
        names = os.listdir(chan_dir)
    except OSError:
        return 0
    for name in names:
        m = _MSG_RE.match(name)
        if m:
            top = max(top, int(m.group(1)))
    return top


def _new_messages(chan_dir: Path, since: int) -> list:
    out = []
    try:
        names = os.listdir(chan_dir)
    except OSError:
        return out
    for name in sorted(names):
        m = _MSG_RE.match(name)
        if m and int(m.group(1)) > since:
            out.append(chan_dir / name)
    return out


class FeedState:
    """Channel tail state: high-water seq + a cond signalled by the watcher."""

    def __init__(self, chan_dir: Path, channel: str, identity: str, key_dir: Path):
        self.chan_dir = chan_dir
        self.channel = channel
        self.identity = identity
        self.key_dir = key_dir
        self.high = _channel_high(chan_dir)
        self.cond = threading.Condition()
        self.stop = threading.Event()

    def note_advanced(self):
        with self.cond:
            cur = _channel_high(self.chan_dir)
            if cur > self.high:
                self.high = cur
                self.cond.notify_all()


def _watch_loop(state: FeedState):
    """inotify on the channel dir; bumps state.high the instant a post lands."""
    try:
        ino = _Inotify(state.chan_dir, WATCH_MASK)
    except OSError as e:
        print(f"squawk-feed: inotify unavailable ({e}); poll fallback",
              file=sys.stderr)
        while not state.stop.is_set():
            state.note_advanced()
            state.stop.wait(2.0)
        return
    try:
        while not state.stop.is_set():
            r, _, _ = select.select([ino.fd], [], [], 1.0)
            if state.stop.is_set():
                break
            if not r:
                continue
            try:
                if not ino.read_events():
                    continue
            except OSError:
                break
            state.note_advanced()
    finally:
        ino.close()


# ---------------------------------------------------------------------------
# fat response builder
# ---------------------------------------------------------------------------

def _truncate(text, cap: int = TEXT_CAP) -> str:
    if text is None:
        return None
    if len(text) > cap:
        return text[: cap - 1] + "…"
    return text


def build_fat(since: int, state: FeedState,
              max_messages: int = MAX_MESSAGES) -> dict:
    """{"seq": M, "messages": [...]} for messages with seq > since.

    M is the seq of the last message in the batch (== channel high-water
    when nothing was capped), so the client can re-poll to drain.
    """
    paths = _new_messages(state.chan_dir, since)[:max_messages]
    messages = []
    last = since
    for p in paths:
        rec = fleet_relay.build_relay_record(
            p, channel=state.channel,
            identity=state.identity, key_dir=state.key_dir)
        rec["body"] = _truncate(rec.get("body"))
        messages.append(rec)
        last = max(last, int(rec["seq"]))
    if not messages:
        with state.cond:
            last = state.high
    return {"seq": last, "messages": messages}


# ---------------------------------------------------------------------------
# HTTP: one port, bearer-authed fat endpoints + public ping
# ---------------------------------------------------------------------------

class _Handler(http.server.BaseHTTPRequestHandler):
    server_version = "squawk-feed/1.0"

    def log_message(self, fmt, *args):  # keep stderr quiet; no token logging
        sys.stderr.write("squawk-feed: " + fmt % args + "\n")

    def _send_json(self, code: int, obj: dict):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_404(self):
        # Never reveal the endpoint exists: bare 404, empty body.
        self.send_response(404)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _send_ui(self):
        # Web UI shell: static HTML, zero secrets inside. Feed data still
        # needs the Bearer token, which the page itself gates on.
        try:
            data = self.server.ui_file.read_bytes()
        except OSError:
            self._send_404()
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _authed(self) -> bool:
        token = self.server.token
        presented = self.headers.get("Authorization") or ""
        want = "Bearer " + token
        return bool(token) and hmac.compare_digest(presented, want)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path in ("/squawk-feed/ping", "/squawk-feed/seq"):  # /seq kept for the relay agent
            with self.server.state.cond:
                high = self.server.state.high
            self._send_json(200, {"seq": high})
            return
        if path in ("/squawk-feed/wait", "/squawk-feed/subscribe"):
            if not self._authed():
                self._send_404()
                return
            qs = urllib.parse.parse_qs(parsed.query)
            try:
                since = int(qs.get("since", ["0"])[0])
            except (TypeError, ValueError):
                since = 0
            since = max(since, 0)
            state = self.server.state
            with state.cond:
                if state.high <= since:
                    state.cond.wait(timeout=self.server.hold)
            self._send_json(200, build_fat(since, state))
            return
        if path in ("/squawk-feed/", "/squawk-feed/ui"):
            self._send_ui()
            return
        self._send_404()


class FeedServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, addr, state: FeedState, token: str,
                 hold: float = HOLD_SECONDS, ui_file=None):
        self.state = state
        self.token = token
        self.hold = hold
        self.ui_file = Path(ui_file) if ui_file else Path(__file__).with_name("ui.html")
        super().__init__(addr, _Handler)


def _ensure_keys_env(root: Path) -> None:
    """squawk_seal reads FLEET_KEYS_DIR at import; make sure it resolves.

    Never overrides an explicit setting -- the service definition should
    set FLEET_KEYS_DIR=/home/toxic/.shingle/squawk-root/keys.
    """
    if "FLEET_KEYS_DIR" not in os.environ:
        os.environ["FLEET_KEYS_DIR"] = str(
            fleet_relay.resolve_key_dir(None, root=root))


def serve(*, root: Path, channel: str, identity: str, key_dir: Path,
          bind: str, port: int, token: str,
          hold: float = HOLD_SECONDS, ui_file=None) -> FeedServer:
    """Build (not start) the server; caller runs serve_forever()."""
    chan_dir = root / channel
    if not chan_dir.is_dir():
        raise RuntimeError(f"channel '{channel}' not found under {root}")
    _ensure_keys_env(root)
    state = FeedState(chan_dir, channel, identity, key_dir)
    watcher = threading.Thread(target=_watch_loop, args=(state,),
                               daemon=True)
    watcher.start()
    server = FeedServer((bind, port), state, token, hold, ui_file)
    server.feed_state = state
    return server


def _load_settings_file(path):
    """Load KEY=VALUE settings for future keys. Missing file is fine."""
    try:
        p = Path(path)
        if not p.is_file():
            return
        for line in p.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v
    except Exception as e:
        print(f"squawk-feed: settings file {path}: {e}", file=sys.stderr)


def _resolve_token(token_file):
    """Server-style token resolution: env > file > auto-generate.

    Never asks, never refuses to start. A generated token is persisted
    (0600) to the canonical file so restarts reuse it.
    """
    token = os.environ.get(TOKEN_ENV, "").strip()
    if token:
        return token
    p = Path(token_file)
    try:
        if p.is_file():
            token = p.read_text().strip()
            if token:
                return token
    except Exception as e:
        print(f"squawk-feed: reading token file {token_file}: {e}",
              file=sys.stderr)
    # Auto-generate: the server configures itself.
    token = secrets.token_urlsafe(32)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(token + "\n")
        try:
            os.chmod(p, 0o600)
        except Exception:
            pass
        print(f"squawk-feed: generated new bearer token -> {token_file}",
              file=sys.stderr)
    except Exception as e:
        print(f"squawk-feed: cannot persist token to {token_file}: {e} "
              f"(using ephemeral token for this run)", file=sys.stderr)
    return token


def main(argv=None) -> None:
    _install_telemetry()
    ap = argparse.ArgumentParser(
        description="squawk-feed: bearer-authed fat long-poll for Squawk")
    ap.add_argument("--root", required=True, help="chat root")
    ap.add_argument("--channel", default="fleet", help="channel to serve")
    ap.add_argument("--bind", default="127.0.0.1", help="bind address")
    ap.add_argument("--port", type=int, default=25131,
                    help="port to serve (default: 25131)")
    ap.add_argument("--identity", default=None,
                    help="relay identity used to unseal "
                         "(default: $SQUAWK_RELAY_IDENTITY or 'relay')")
    ap.add_argument("--key-dir", default=None,
                    help="fleet keys dir "
                         "(default: $FLEET_KEYS_DIR, else <root>/keys)")
    ap.add_argument("--hold", type=float, default=HOLD_SECONDS,
                    help="long-poll hold seconds (default: 55)")
    ap.add_argument("--ui-file", default=None,
                    help="squawk web UI html (default: ui.html next to this script)")
    ap.add_argument("--token-file", default=None,
                    help="bearer token file (default: $SQUAWK_FEED_TOKEN_FILE, "
                         "else ~/.shingle/squawk-relay/feed-token; "
                         "auto-generated on first run if missing)")
    ap.add_argument("--settings-file", default=None,
                    help="settings file for future keys, KEY=VALUE lines "
                         "(default: $SQUAWK_FEED_SETTINGS, else "
                         "~/.shingle/squawk-relay/settings.conf)")
    a = ap.parse_args(argv)

    token_file = (a.token_file
                or os.environ.get("SQUAWK_FEED_TOKEN_FILE", "").strip()
                or TOKEN_FILE_DEFAULT)
    settings_file = (a.settings_file
                     or os.environ.get("SQUAWK_FEED_SETTINGS", "").strip()
                     or SETTINGS_FILE_DEFAULT)
    # Settings first: future keys live here as KEY=VALUE lines.
    _load_settings_file(settings_file)
    # Token resolution, server-style: env > file > auto-generate. Never ask,
    # never refuse to start.
    token = _resolve_token(token_file)

    identity = fleet_relay.resolve_identity(a.identity)
    key_dir = fleet_relay.resolve_key_dir(a.key_dir, root=Path(a.root))
    server = serve(root=Path(a.root), channel=a.channel, identity=identity,
                   key_dir=key_dir, bind=a.bind, port=a.port, token=token,
                   hold=a.hold, ui_file=a.ui_file)
    sa = server.server_address
    print(f"squawk-feed: serving #{a.channel} on {sa[0]}:{sa[1]} "
          f"(hold={a.hold}s, bearer auth on /wait + /subscribe)",
          flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.feed_state.stop.set()


if __name__ == "__main__":
    main()
