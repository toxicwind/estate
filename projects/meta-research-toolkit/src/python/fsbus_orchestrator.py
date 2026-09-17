#!/usr/bin/env python3
"""fsbus_orchestrator.py -- dual-track filesystem message-bus orchestrator.
Zero dependencies (stdlib only). See companion spec for invariants."""
import json, os, signal, sys, threading, time, uuid, shutil, errno
from pathlib import Path

BUS      = Path(os.environ.get("FSBUS_DIR", "./fsbus"))
INBOX    = BUS / "inbox"       # immutable task payloads
CLAIMED  = BUS / "claimed"     # worker-claimed (atomic rename target)
OUTBOX   = BUS / "outbox"      # result payloads (tmp -> rename)
DEAD     = BUS / "dead"        # poison pills / terminal failure
MANIFEST = BUS / "manifest.jsonl"
MAX_ATTEMPTS = 3
LEASE_SEC    = 30.0            # claim lease; reclaim after expiry
STOP = threading.Event()

def _mkdir(p): p.mkdir(parents=True, exist_ok=True)

def init_bus():
    for d in (BUS, INBOX, CLAIMED, OUTBOX, DEAD): _mkdir(d)
    if not MANIFEST.exists(): MANIFEST.touch()

def fsync_dir(path):
    fd = os.open(path, os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)

def atomic_write_final(dest: Path, data: bytes):
    """Immutable-file contract: tmp + fsync + rename + dir fsync."""
    tmp = dest.with_name(dest.name + ".tmp-" + uuid.uuid4().hex[:8])
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, data); os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, dest)          # atomic on same fs
    fsync_dir(dest.parent)

def append_manifest(record: dict) -> None:
    """Append-only contract: one write() syscall under O_APPEND => atomic tail.
    Readers tolerate a torn final line (see spec 4.3)."""
    line = json.dumps(record, separators=(",", ":")) + "\n"
    fd = os.open(MANIFEST, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        n = os.write(fd, line.encode())          # single syscall, <= PIPE_BUF-ish
        if n != len(line): raise IOError("short manifest write")
        os.fsync(fd)
    finally:
        os.close(fd)

def submit(task: dict) -> str:
    tid = task.setdefault("id", uuid.uuid4().hex[:12])
    atomic_write_final(INBOX / f"{tid}.json", json.dumps(task).encode())
    append_manifest({"type": "submitted", "id": tid, "ts": time.time()})
    return tid

def claim(worker: str) -> tuple[str, dict] | None:
    """Atomic claim: rename inbox/<id>.json -> claimed/<id>.<wid>.
    rename(2) is atomic; exactly one claimant succeeds."""
    for f in sorted(INBOX.glob("*.json")):
        dest = CLAIMED / f"{f.stem}.{worker}.json"
        try: os.rename(f, dest)
        except OSError: continue                 # lost race or lease-valid claim
        fsync_dir(INBOX); fsync_dir(CLAIMED)
        return f.stem, json.loads(dest.read_text())
    return None

def finish(tid: str, worker: str, ok: bool, result: dict, error=None):
    attempts = 1 + count_attempts(tid)
    if ok:
        atomic_write_final(OUTBOX / f"{tid}.json", json.dumps(result).encode())
        append_manifest({"type": "succeeded", "id": tid, "attempt": attempts, "ts": time.time()})
        (CLAIMED / f"{tid}.{worker}.json").unlink(missing_ok=True)
    elif attempts >= MAX_ATTEMPTS:
        atomic_write_final(DEAD / f"{tid}.json",
            json.dumps({"error": error, "attempts": attempts}).encode())
        append_manifest({"type": "dead", "id": tid, "attempts": attempts, "ts": time.time()})
        (CLAIMED / f"{tid}.{worker}.json").unlink(missing_ok=True)
    else:
        # retryable: relinquish claim so any worker may re-claim
        os.replace(CLAIMED / f"{tid}.{worker}.json", INBOX / f"{tid}.json")
        fsync_dir(INBOX)
        append_manifest({"type": "retry_scheduled", "id": tid, "attempt": attempts, "ts": time.time()})

def count_attempts(tid: str) -> int:
    """Replay manifest; skip torn tail line (spec 4.3)."""
    n = 0
    try:
        with open(MANIFEST, "rb") as fh:
            for raw in fh:
                try: rec = json.loads(raw)
                except json.JSONDecodeError:
                    continue                     # torn tail only possible at EOF
                if rec.get("id") == tid and rec["type"] in ("retry_scheduled",):
                    n += 1
    except FileNotFoundError:
        pass
    return n

def reap_expired(now=None):
    """Lease recovery: claims older than LEASE_SEC are returned to inbox."""
    now = now or time.time()
    for f in CLAIMED.glob("*.json"):
        if now - f.stat().st_mtime > LEASE_SEC:
            tid = f.name.split(".")[0]
            os.replace(f, INBOX / f"{tid}.json")
            append_manifest({"type": "reclaimed", "id": tid, "ts": now})

def worker_loop(worker: str, handler):
    while not STOP.is_set():
        job = claim(worker)
        if job is None: time.sleep(0.05); continue
        tid, task = job
        if STOP.is_set():                        # graceful: relinquish, no half-claim
            os.replace(CLAIMED / f"{tid}.{worker}.json", INBOX / f"{tid}.json"); return
        try:
            res = handler(task)
            finish(tid, worker, True, {"result": res})
        except Exception as e:
            finish(tid, worker, False, {}, error=repr(e))

def coordinator(handler, n_workers=4):
    init_bus()
    reap_timer = threading.Thread(target=lambda: [reap_expired(), time.sleep(5.0)]
                                  if not STOP.is_set() else None, daemon=True)
    def sig(_sig, _frm):
        STOP.set()                               # bounded shutdown, no new claims
    signal.signal(signal.SIGINT, sig); signal.signal(signal.SIGTERM, sig)
    threads = [threading.Thread(target=worker_loop, args=(f"w{i}", handler), daemon=True)
               for i in range(n_workers)]
    for t in threads: t.start()
    while not STOP.is_set():
        time.sleep(0.1) if any(t.is_alive() for t in threads) else STOP.set()
    for t in threads: t.join(timeout=LEASE_SEC + 5.0)
    append_manifest({"type": "coordinator_exit", "ts": time.time()})

if __name__ == "__main__":
    demo = lambda task: {"echo": task.get("payload"), "pid": os.getpid()}
    submit({"payload": "alpha"}); submit({"payload": "beta"})
    coordinator(demo)
