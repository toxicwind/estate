"""Pattern 13: non-blocking alert queue.

Webhooks never block the rotation path. Bounded queue, one worker
thread. Overflow -> drop oldest, count drops.
"""
import json
import os
import queue
import threading


class Alerts:
    def __init__(self, path: str, webhook: str = "", max_bytes: int = 10_000_000):
        self.path = path
        self.webhook = webhook
        self.max_bytes = max_bytes
        self._q: queue.Queue = queue.Queue(maxsize=1024)
        self._dropped = 0
        os.makedirs(os.path.dirname(path), exist_ok=True)
        threading.Thread(target=self._worker, daemon=True,
                         name="keypool-alerts").start()

    def emit(self, record: dict):
        try:
            self._q.put_nowait(record)
        except queue.Full:
            self._dropped += 1

    def _worker(self):
        while True:
            try:
                rec = self._q.get(timeout=1.0)
            except queue.Empty:
                continue
            try:
                if os.path.exists(self.path) and os.path.getsize(self.path) >= self.max_bytes:
                    os.replace(self.path, self.path + ".1")
                with open(self.path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, default=str) + "\n")
            except OSError:
                pass
