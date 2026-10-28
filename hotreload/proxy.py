#!/usr/bin/env python3
"""Stable-port TCP proxy with hot-swappable backend.

Listens on STABLE_PORT, forwards all traffic to the current active backend
(host:port). The backend can be switched at runtime without dropping the
listener — this is what makes blue-green deploys zero-downtime.

Backend switching:
  - Via control file: write "host:port" to <statedir>/backend (watched with polling).
  - Via SIGHUP: re-read the control file.

Usage:
  proxy.py <stable_port> <statedir>
  proxy.py 25147 /home/toxic/estate/hotreload/state/squawk-ws

The bluegreen.py orchestrator writes the control file to cut over.
"""
import os
import select
import signal
import socket
import sys
import threading
import time

BUF = 65536


class Proxy:
    def __init__(self, stable_port, statedir):
        self.stable_port = stable_port
        self.statedir = statedir
        self.backend_file = os.path.join(statedir, "backend")
        self.backend = self._read_backend()
        self.lock = threading.Lock()
        self.running = True

    def _read_backend(self):
        try:
            with open(self.backend_file) as f:
                host, port = f.read().strip().split(":")
                return (host.strip(), int(port.strip()))
        except Exception as e:
            print(f"proxy: cannot read backend file: {e}", file=sys.stderr)
            return None

    def refresh_backend(self):
        b = self._read_backend()
        if b:
            with self.lock:
                self.backend = b
            print(f"proxy: backend -> {b[0]}:{b[1]}", flush=True)

    def _pipe(self, src, dst):
        try:
            while self.running:
                data = src.recv(BUF)
                if not data:
                    break
                dst.sendall(data)
        except OSError:
            pass
        finally:
            try:
                src.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                dst.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

    def _handle(self, client):
        with self.lock:
            backend = self.backend
        if not backend:
            client.close()
            return
        try:
            up = socket.create_connection(backend, timeout=10)
        except OSError as e:
            print(f"proxy: backend {backend} unreachable: {e}", file=sys.stderr)
            client.close()
            return
        t1 = threading.Thread(target=self._pipe, args=(client, up), daemon=True)
        t2 = threading.Thread(target=self._pipe, args=(up, client), daemon=True)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        client.close()
        up.close()

    def serve(self):
        os.makedirs(self.statedir, exist_ok=True)
        # Ensure a backend file exists (bluegreen.py manages it, but don't crash)
        if not os.path.exists(self.backend_file):
            print(f"proxy: no backend file at {self.backend_file}, waiting...",
                  file=sys.stderr)

        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("127.0.0.1", self.stable_port))
        srv.listen(128)
        srv.settimeout(1.0)

        def on_hup(signum, frame):
            self.refresh_backend()

        signal.signal(signal.SIGHUP, on_hup)

        # Poll the backend file for changes (simple, no inotify dependency)
        last_mtime = 0
        print(f"proxy: listening on 127.0.0.1:{self.stable_port}", flush=True)

        while self.running:
            try:
                client, _ = srv.accept()
            except socket.timeout:
                pass
            except OSError:
                break
            else:
                threading.Thread(target=self._handle, args=(client,),
                                 daemon=True).start()

            try:
                mtime = os.path.getmtime(self.backend_file)
                if mtime != last_mtime:
                    last_mtime = mtime
                    self.refresh_backend()
            except OSError:
                pass


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    stable_port = int(sys.argv[1])
    statedir = sys.argv[2]
    Proxy(stable_port, statedir).serve()


if __name__ == "__main__":
    main()
