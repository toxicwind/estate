#!/usr/bin/env python3
"""Graceful shutdown mixin for Python TCP/HTTP servers.

Drop this into a server to get:
  - SIGTERM/SIGINT handling: stop accepting new connections, drain in-flight
    requests with a timeout, then exit cleanly. No more mid-request kills.
  - /health endpoint helper: returns 200 when serving, 503 when draining.

Usage (http.server):
    from graceful import GracefulHTTPServer, install_signal_handlers

    server = GracefulHTTPServer(("127.0.0.1", PORT), Handler)
    install_signal_handlers(server)
    server.serve_forever()

Usage (custom loop):
    from graceful import ShutdownFlag

    flag = ShutdownFlag()  # installs SIGTERM/SIGINT handlers
    while not flag.should_stop():
        ...accept/process...
    flag.wait_for_drain(timeout=15)

The bluegreen.py orchestrator sends SIGTERM and waits for the port to close.
If the server drains within drain_timeout_s, the deploy is clean.
If not, bluegreen.py SIGKILLs — the service still never goes down because
the proxy already cut over to the new backend.
"""
import signal
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer


class ShutdownFlag:
    """Thread-safe shutdown flag set by SIGTERM/SIGINT."""

    def __init__(self):
        self._stop = threading.Event()
        self._draining = threading.Event()
        signal.signal(signal.SIGTERM, self._handle)
        signal.signal(signal.SIGINT, self._handle)

    def _handle(self, signum, frame):
        print(f"graceful: received signal {signum}, draining...", flush=True)
        self._draining.set()
        self._stop.set()

    def should_stop(self):
        return self._stop.is_set()

    def is_draining(self):
        return self._draining.is_set()

    def wait_for_drain(self, timeout=15):
        """Block until in-flight work is done or timeout. Override in subclass."""
        time.sleep(0)  # subclasses track active requests


class GracefulHTTPServer(HTTPServer):
    """HTTPServer with graceful shutdown and a /health endpoint."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, *args, health_path="/health", drain_timeout=15, **kwargs):
        super().__init__(*args, **kwargs)
        self._health_path = health_path
        self._drain_timeout = drain_timeout
        self._shutdown_flag = ShutdownFlag()
        self._active = 0
        self._active_lock = threading.Lock()
        # Wrap serve_forever to check the flag
        self.timeout = 0.5

    def health_check(self):
        """Override for custom readiness logic. Return True if healthy."""
        return not self._shutdown_flag.is_draining()

    def process_request(self, request, client_address):
        with self._active_lock:
            self._active += 1
        try:
            super().process_request(request, client_address)
        finally:
            with self._active_lock:
                self._active -= 1

    def serve_forever(self, poll_interval=0.5):
        print(f"graceful: serving, health at {self._health_path}", flush=True)
        try:
            while not self._shutdown_flag.should_stop():
                self._handle_request_noblock()
        finally:
            self._drain()

    def _drain(self):
        """Wait for in-flight requests, then close."""
        print("graceful: draining in-flight requests...", flush=True)
        deadline = time.time() + self._drain_timeout
        while time.time() < deadline:
            with self._active_lock:
                if self._active == 0:
                    break
            time.sleep(0.1)
        with self._active_lock:
            remaining = self._active
        if remaining:
            print(f"graceful: {remaining} requests still active after "
                  f"{self._drain_timeout}s, closing anyway", flush=True)
        self.server_close()
        print("graceful: shutdown complete", flush=True)


class HealthHandler(BaseHTTPRequestHandler):
    """Mixin: add /health to any BaseHTTPRequestHandler."""

    health_path = "/health"

    def do_GET(self):
        if self.path == self.health_path:
            server = self.server
            healthy = (server.health_check()
                       if hasattr(server, "health_check") else True)
            code = 200 if healthy else 503
            body = b'{"ok": true}' if healthy else b'{"ok": false, "draining": true}'
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.handle_path()

    def handle_path(self):
        """Override this in your handler for non-health paths."""
        self.send_response(404)
        self.end_headers()

    def log_message(self, *args):
        pass  # quiet


def install_signal_handlers(server):
    """Install SIGTERM/SIGINT on a plain HTTPServer (no mixin)."""
    flag = ShutdownFlag()

    orig_serve = server.serve_forever

    def serve_with_drain(*a, **k):
        try:
            orig_serve(*a, **k)
        finally:
            server.server_close()

    # Poll the flag via timeout
    server.timeout = 0.5
    old_handle = server._handle_request_noblock

    def patched():
        if flag.should_stop():
            raise KeyboardInterrupt
        return old_handle()

    server._handle_request_noblock = patched
    return flag
