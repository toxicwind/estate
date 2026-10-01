"""
FSBus Dual-Track Filesystem Message Bus Orchestrator.
Zero-dependency, production-grade POSIX message-passing engine.
Complies strictly with immutable-file, atomic-rename, and append-only contracts.
"""
from __future__ import annotations
import json
import os
import signal
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Callable, List


class FSBusEngine:
    """
    Filesystem-backed message queue with lease recovery, poison pill handling,
    and atomic manifest streaming.
    """

    def __init__(self, base_dir: Path, lease_sec: float = 30.0, max_attempts: int = 3):
        self.base_dir = Path(base_dir)
        self.inbox = self.base_dir / "inbox"
        self.claimed = self.base_dir / "claimed"
        self.outbox = self.base_dir / "outbox"
        self.dead = self.base_dir / "dead"
        self.manifest = self.base_dir / "manifest.jsonl"
        self.lease_sec = lease_sec
        self.max_attempts = max_attempts
        self.stop_event = threading.Event()
        self._init_bus()

    def _init_bus(self):
        for d in (self.base_dir, self.inbox, self.claimed, self.outbox, self.dead):
            d.mkdir(parents=True, exist_ok=True)
        if not self.manifest.exists():
            self.manifest.touch()

    @staticmethod
    def _fsync_dir(path: Path):
        fd = os.open(str(path), os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def atomic_write(self, dest: Path, data: bytes):
        """Immutable write contract: write to tmp, fsync, atomic replace, fsync parent."""
        tmp = dest.with_name(f"{dest.name}.tmp-{uuid.uuid4().hex[:8]}")
        fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        try:
            os.write(fd, data)
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(tmp, dest)
        self._fsync_dir(dest.parent)

    def append_manifest(self, record: Dict[str, Any]):
        """Append-only contract: single O_APPEND write syscall is atomic up to PIPE_BUF."""
        line = json.dumps(record, separators=(",", ":")) + "\n"
        fd = os.open(str(self.manifest), os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
        try:
            written = os.write(fd, line.encode("utf-8"))
            if written != len(line.encode("utf-8")):
                raise IOError("Short manifest write detected")
            os.fsync(fd)
        finally:
            os.close(fd)

    def submit(self, payload: Dict[str, Any], task_id: Optional[str] = None) -> str:
        tid = task_id or payload.get("id") or uuid.uuid4().hex[:12]
        payload["id"] = tid
        self.atomic_write(self.inbox / f"{tid}.json", json.dumps(payload).encode("utf-8"))
        self.append_manifest({"type": "submitted", "id": tid, "ts": time.time()})
        return tid

    def claim(self, worker_id: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Atomic claim via POSIX rename(2). Exactly one worker wins race."""
        for f in sorted(self.inbox.glob("*.json")):
            dest = self.claimed / f"{f.stem}.{worker_id}.json"
            try:
                os.rename(f, dest)
            except OSError:
                continue  # Lost race to another worker
            self._fsync_dir(self.inbox)
            self._fsync_dir(self.claimed)
            content = json.loads(dest.read_text(encoding="utf-8"))
            return f.stem, content
        return None

    def count_attempts(self, tid: str) -> int:
        """Replay manifest ignoring torn final lines."""
        n = 0
        if not self.manifest.exists():
            return 0
        with open(self.manifest, "rb") as fh:
            for raw in fh:
                try:
                    rec = json.loads(raw)
                    if rec.get("id") == tid and rec.get("type") in ("retry_scheduled", "reclaimed"):
                        n += 1
                except Exception:
                    continue  # Tolerate torn final line
        return n

    def finish(self, tid: str, worker_id: str, ok: bool, result: Dict[str, Any], error: Optional[str] = None):
        attempts = 1 + self.count_attempts(tid)
        claimed_path = self.claimed / f"{tid}.{worker_id}.json"
        if ok:
            self.atomic_write(self.outbox / f"{tid}.json", json.dumps(result).encode("utf-8"))
            self.append_manifest({"type": "succeeded", "id": tid, "attempt": attempts, "ts": time.time()})
            claimed_path.unlink(missing_ok=True)
        elif attempts >= self.max_attempts:
            # Poison pill threshold exceeded -> move to dead letter queue
            self.atomic_write(self.dead / f"{tid}.json", json.dumps({"error": error, "attempts": attempts}).encode("utf-8"))
            self.append_manifest({"type": "dead", "id": tid, "attempts": attempts, "error": error, "ts": time.time()})
            claimed_path.unlink(missing_ok=True)
        else:
            # Re-enqueue for retry
            os.replace(claimed_path, self.inbox / f"{tid}.json")
            self._fsync_dir(self.inbox)
            self.append_manifest({"type": "retry_scheduled", "id": tid, "attempt": attempts, "ts": time.time()})

    def reap_expired(self, now: Optional[float] = None):
        """Lease recovery: claims older than lease_sec are returned to inbox."""
        current_time = now or time.time()
        for f in self.claimed.glob("*.json"):
            try:
                mtime = f.stat().st_mtime
                if current_time - mtime > self.lease_sec:
                    tid = f.name.split(".")[0]
                    os.replace(f, self.inbox / f"{tid}.json")
                    self.append_manifest({"type": "reclaimed", "id": tid, "ts": current_time})
            except OSError:
                continue

    def start_worker(self, worker_id: str, handler: Callable[[Dict[str, Any]], Dict[str, Any]]) -> threading.Thread:
        def loop():
            while not self.stop_event.is_set():
                job = self.claim(worker_id)
                if job is None:
                    time.sleep(0.05)
                    continue
                tid, task = job
                if self.stop_event.is_set():
                    # Relinquish claim on shutdown
                    os.replace(self.claimed / f"{tid}.{worker_id}.json", self.inbox / f"{tid}.json")
                    return
                try:
                    res = handler(task)
                    self.finish(tid, worker_id, True, res)
                except Exception as e:
                    self.finish(tid, worker_id, False, {}, error=str(e))

        t = threading.Thread(target=loop, name=f"FSBusWorker-{worker_id}", daemon=True)
        t.start()
        return t
