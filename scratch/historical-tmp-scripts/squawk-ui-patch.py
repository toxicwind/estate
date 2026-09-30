"""One-shot patch: serve the squawk web UI from squawk_feed.py.

Adds a --ui-file arg (default: ui.html next to this script) and serves it
unauthenticated at /squawk-feed/ and /squawk-feed/ui. The HTML shell holds no
secrets; the data endpoints stay Bearer-gated and the page gates on the token.
Idempotent: refuses to run twice.
"""
import sys

P = "/home/toxic/sovereign/projects/mesh/squawk/squawk_feed.py"
src = open(P).read()
if "_send_ui" in src:
    print("already patched; nothing to do")
    sys.exit(0)

def rep(old, new):
    global src
    assert src.count(old) == 1, "anchor not unique/found: %r" % old[:60]
    src = src.replace(old, new)

# 1. CLI arg
rep('''    ap.add_argument("--hold", type=float, default=HOLD_SECONDS,
                    help="long-poll hold seconds (default: 55)")''',
    '''    ap.add_argument("--hold", type=float, default=HOLD_SECONDS,
                    help="long-poll hold seconds (default: 55)")
    ap.add_argument("--ui-file", default=None,
                    help="squawk web UI html (default: ui.html next to this script)")''')

# 2. FeedServer stores the UI path
rep('''    def __init__(self, addr, state: FeedState, token: str,
                 hold: float = HOLD_SECONDS):
        self.state = state
        self.token = token
        self.hold = hold
        super().__init__(addr, _Handler)''',
    '''    def __init__(self, addr, state: FeedState, token: str,
                 hold: float = HOLD_SECONDS, ui_file=None):
        self.state = state
        self.token = token
        self.hold = hold
        self.ui_file = Path(ui_file) if ui_file else Path(__file__).with_name("ui.html")
        super().__init__(addr, _Handler)''')

# 3. serve() passes it through
rep('''def serve(*, root: Path, channel: str, identity: str, key_dir: Path,
          bind: str, port: int, token: str,
          hold: float = HOLD_SECONDS) -> FeedServer:''',
    '''def serve(*, root: Path, channel: str, identity: str, key_dir: Path,
          bind: str, port: int, token: str,
          hold: float = HOLD_SECONDS, ui_file=None) -> FeedServer:''')
rep('''    server = FeedServer((bind, port), state, token, hold)''',
    '''    server = FeedServer((bind, port), state, token, hold, ui_file)''')
rep('''                   hold=a.hold)''',
    '''                   hold=a.hold, ui_file=a.ui_file)''')

# 4. route: UI shell (public), data stays authed
rep('''            self._send_json(200, build_fat(since, state))
            return
        self._send_404()''',
    '''            self._send_json(200, build_fat(since, state))
            return
        if path in ("/squawk-feed/", "/squawk-feed/ui"):
            self._send_ui()
            return
        self._send_404()''')

# 5. the sender
rep('''    def _send_404(self):
        # Never reveal the endpoint exists: bare 404, empty body.
        self.send_response(404)
        self.send_header("Content-Length", "0")
        self.end_headers()''',
    '''    def _send_404(self):
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
        self.wfile.write(data)''')

open(P, "w").write(src)
print("patched OK")
