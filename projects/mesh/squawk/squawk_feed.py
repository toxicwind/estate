#!/usr/bin/env python3
"""squawk-feed: bearer-authed fat long-poll for Squawk (stdlib only).

Endpoints (all under /squawk-feed):

  GET /squawk-feed/ping                public, content-free -> {"seq": N}
  GET /squawk-feed/wait?since=N        bearer auth -> {"seq": M, "messages": [...]}
  GET /squawk-feed/subscribe?since=N   same handler as /wait (alias)
  POST /squawk-feed/send               bearer auth, JSON {channel, text, from?, title?}
                                       -> {"ok": true, "seq": N, "file": name}

Query params on /wait (and /subscribe):
  since=N    cursor: messages with seq > N, oldest first, capped at 50 per
             response; returned "seq" is the last message's seq, so the
             client re-polls to drain the rest.
  tail=N     bounded recent snapshot: the N most recent messages in one
             shot, cursor set to the channel high-water mark. Fast initial
             load instead of draining all history. Capped at TAIL_CAP.
             Answers immediately (never parks).
  channel=C  which channel to read (default: the daemon's --channel).
             Restricted to [A-Za-z0-9_-]; unknown channel -> 404.

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
drain the rest. Full message bodies are served untruncated. Sealed
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
import datetime
import fcntl
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
import seq_alloc

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
TAIL_CAP = 1000  # server-side ceiling for ?tail=N snapshots
WATCH_MASK = 0x00000008 | 0x00000100  # IN_CLOSE_WRITE | IN_MOVED_TO
_MSG_RE = re.compile(r"^(\d+)-.*\.md$")
_CHANNEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


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
    """Paths of messages with seq > since, oldest first (numeric seq order).

    Numeric sort, not lexicographic: filenames are "<seq>-*.md" and seqs
    cross digit widths (9999 -> 10000), so plain sorted() misorders them.
    """
    hits = []
    try:
        names = os.listdir(chan_dir)
    except OSError:
        return []
    for name in names:
        m = _MSG_RE.match(name)
        if m:
            seq = int(m.group(1))
            if seq > since:
                hits.append((seq, name))
    hits.sort(key=lambda t: (t[0], t[1]))
    return [chan_dir / name for _, name in hits]


class FeedState:
    """Channel tail state: high-water seq + a cond signalled by the watcher."""

    def __init__(self, chan_dir: Path, channel: str, identity: str, key_dir: Path):
        self.chan_dir = chan_dir
        self.channel = channel
        self.identity = identity
        self.key_dir = key_dir
        # Durable high-water floor (2026-09-21): after message
        # deletions the disk-derived max can sit below seqs the
        # feed already broadcast, so seed from the monotonic
        # allocator too -- never start below it.
        self.high = max(_channel_high(chan_dir),
                        seq_alloc.read_high(chan_dir.parent, channel))
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


def build_fat(since: int, state: FeedState,
              max_messages: int = MAX_MESSAGES,
              tail: int | None = None) -> dict:
    """{"seq": M, "messages": [...]} for messages with seq > since.

    M is the seq of the last message in the batch (== channel high-water
    when nothing was capped), so the client can re-poll to drain.

    tail=N: bounded recent snapshot -- the N most recent messages in one
    shot (ignores the 50-cap, honours TAIL_CAP), M set to the channel
    high-water mark. For fast initial load; live updates then continue
    with plain since-cursor long-polls.
    """
    paths = _new_messages(state.chan_dir, since)
    if tail is not None and tail > 0:
        paths = paths[-min(tail, TAIL_CAP):]
    else:
        paths = paths[:max_messages]
    messages = []
    last = since
    for p in paths:
        rec = fleet_relay.build_relay_record(
            p, channel=state.channel,
            identity=state.identity, key_dir=state.key_dir)
        # full bodies served untruncated (Chris 2026-09-21: the "…" cut is useless;
        # tail=200 worst case ~100KB today -- trivial for one response + 200 cards)
        messages.append(rec)
        last = max(last, int(rec["seq"]))
    if paths:
        # Drain progress is driven by filename seqs too: even if a record
        # carries seq 0 (unparseable frontmatter), the files in this batch
        # are consumed and never re-fetched.
        last = max(last, max(int(_MSG_RE.match(p.name).group(1))
                             for p in paths))
    if not messages:
        with state.cond:
            last = state.high
    elif tail is not None and tail > 0:
        # Snapshot: cursor jumps straight to the live high-water mark so
        # the client long-polls from "now" instead of draining history.
        with state.cond:
            last = max(last, state.high)
    return {"seq": last, "messages": messages}


# ---------------------------------------------------------------------------
# publish: atomic seq allocation + file write (same shape as squawk CLI)
# ---------------------------------------------------------------------------

_SENDER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,31}$")


def _publish_message(root: Path, channel: str, sender: str, title: str, text: str):
    """Write one chat message file under <root>/<channel>/, seq-allocated
    under an exclusive per-channel flock. Returns (seq, filename).
    Mirrors the hatch squawk CLI's file shape so the inotify watcher,
    squawk-ws, and relay all pick it up identically."""
    chan_dir = root / channel
    chan_dir.mkdir(parents=True, exist_ok=True)
    lock_path = root / f".seq-{channel}.lock"
    try:
        lock_path.touch(exist_ok=True)
    except OSError:
        pass
    with open(lock_path, "w") as lockf:
        fcntl.flock(lockf, fcntl.LOCK_EX)
        try:
            # Monotonic durable allocation (2026-09-21): the old
            # disk-derived next-seq reused dead numbers after
            # deletions and the in-memory high-water mark then
            # suppressed those messages forever (seq <= high
            # looks already-delivered). alloc_seq serializes on
            # its own internal flock; safe inside this outer lock.
            seq = seq_alloc.alloc_seq(root, channel)
            slug = "".join(
                c if c.isalnum() else "-"
                for c in (title[:30].lower() if title else "msg")
            ).strip("-") or "msg"
            sender_slug = "".join(
                c if c.isalnum() else "-" for c in sender.lower()
            ).strip("-") or "agent"
            fname = f"{seq}-{sender_slug}-{slug}.md"
            ts = datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()

            def clean(v: str) -> str:
                return str(v).replace("\n", " ").replace("\r", " ")[:200]

            content = (
                "---\n"
                f"seq: {seq}\n"
                f"from: {clean(sender)}\n"
                "to: all\n"
                f"channel: {clean(channel)}\n"
                f"ts: {ts}\n"
                "status: discussion\n"
                f"title: {clean(title or slug)}\n"
                "---\n"
                f"{text}\n"
            )
            # atomic write via temp file then rename
            tmp = chan_dir / f".tmp-{seq}-{sender_slug}.md"
            tmp.write_text(content, encoding="utf-8")
            final = chan_dir / fname
            tmp.replace(final)
            if not final.is_file() or final.stat().st_size == 0:
                raise RuntimeError("write failed for %s" % fname)
            return seq, fname
        finally:
            try:
                fcntl.flock(lockf, fcntl.LOCK_UN)
            except OSError:
                pass


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

    def _channel_state(self, qs) -> "FeedState | None":
        """Resolve ?channel=C to a live FeedState (lazily watched).

        The UI has always sent ?channel=; previously the server ignored it.
        Names are restricted to [A-Za-z0-9_-] and must be an existing
        directory directly under the chat root -- no traversal, no 404
        oracle beyond "no such channel".
        """
        raw = (qs.get("channel", [self.server.default_channel])[0] or "").strip()
        if not _CHANNEL_RE.match(raw):
            return None
        return self.server.state_for(raw)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path in ("/squawk-feed/ping", "/squawk-feed/seq"):  # /seq kept for the relay agent
            qs = urllib.parse.parse_qs(parsed.query)
            state = self._channel_state(qs) or self.server.state_for(
                self.server.default_channel)
            with state.cond:
                high = state.high
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
            try:
                tail = int(qs.get("tail", ["0"])[0])
            except (TypeError, ValueError):
                tail = 0
            tail = min(max(tail, 0), TAIL_CAP) or None
            state = self._channel_state(qs)
            if state is None:
                self._send_404()
                return
            if tail is None:
                # Classic cursor long-poll: park until inotify wakes us or
                # the hold expires.
                with state.cond:
                    if state.high <= since:
                        state.cond.wait(timeout=self.server.hold)
            # tail snapshots answer immediately -- never park.
            self._send_json(200, build_fat(since, state, tail=tail))
            return
        if path in ("/squawk-feed/", "/squawk-feed/ui"):
            self._send_ui()
            return
        self._send_404()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path == "/squawk-feed/send":
            if not self._authed():
                self._send_404()
                return
            try:
                length = int(self.headers.get("Content-Length", "0") or "0")
            except (TypeError, ValueError):
                length = 0
            if length <= 0 or length > 100_000:
                self._send_json(400 if length > 0 else 411,
                                {"ok": False, "error": "bad length"})
                return
            try:
                raw = self.rfile.read(length)
                data = json.loads(raw.decode("utf-8") or "{}")
            except Exception:
                self._send_json(400, {"ok": False, "error": "invalid json"})
                return
            channel = str(data.get("channel") or self.server.default_channel).strip()
            text = str(data.get("text") or "")
            # keep newlines in body, strip only leading/trailing blank space
            if not text.strip():
                self._send_json(400, {"ok": False, "error": "empty text"})
                return
            if len(text) > 20000:
                self._send_json(400, {"ok": False, "error": "text too long"})
                return
            title = str(data.get("title") or "").strip()[:120]
            sender = str(data.get("from") or "chris").strip()[:32] or "chris"
            if not _CHANNEL_RE.match(channel):
                self._send_json(400, {"ok": False, "error": "bad channel"})
                return
            if not _SENDER_RE.match(sender):
                sender = "chris"
            state = self.server.state_for(channel)
            if state is None:
                self._send_json(404, {"ok": False, "error": "no such channel"})
                return
            try:
                seq, fname = _publish_message(
                    self.server.root, channel, sender, title, text.strip())
            except Exception as e:
                sys.stderr.write("squawk-feed: publish failed: %s\n" % e)
                self._send_json(500, {"ok": False, "error": "publish failed"})
                return
            try:
                state.note_advanced()
            except Exception:
                pass
            self._send_json(200, {"ok": True, "seq": seq,
                                  "file": fname, "channel": channel})
            return
        self._send_404()


class FeedServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, addr, root: Path, default_channel: str,
                 identity: str, key_dir: Path, token: str,
                 hold: float = HOLD_SECONDS, ui_file=None):
        self.root = root
        self.default_channel = default_channel
        self.identity = identity
        self.key_dir = key_dir
        self.token = token
        self.hold = hold
        self.ui_file = Path(ui_file) if ui_file else Path(__file__).with_name("ui.html")
        self._states: dict = {}
        self._states_lock = threading.Lock()
        super().__init__(addr, _Handler)
        # Pre-warm the default channel so /ping is hot at boot.
        self.state_for(default_channel)

    @property
    def state(self) -> FeedState:
        """Default channel state (back-compat for existing callers)."""
        return self.state_for(self.default_channel)

    def state_for(self, channel: str) -> "FeedState | None":
        """Lazily create (and inotify-watch) per-channel tail state."""
        with self._states_lock:
            state = self._states.get(channel)
            if state is not None:
                return state
            chan_dir = self.root / channel
            if not chan_dir.is_dir():
                return None
            state = FeedState(chan_dir, channel, self.identity, self.key_dir)
            watcher = threading.Thread(target=_watch_loop, args=(state,),
                                       daemon=True)
            watcher.start()
            self._states[channel] = state
            return state

    def stop_watchers(self):
        with self._states_lock:
            states = list(self._states.values())
        for state in states:
            state.stop.set()


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
    server = FeedServer((bind, port), root, channel, identity, key_dir,
                        token, hold, ui_file)
    server.feed_state = server.state  # back-compat alias (default channel)
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
        server.stop_watchers()


if __name__ == "__main__":
    main()
