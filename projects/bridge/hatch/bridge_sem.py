"""Cell-side concurrency guard for heavy bridge operations.

The hatch cell has 2 vCPUs. Each concurrent yote-conn exec / bridge-put
holds a local Python bridge process that burns significant CPU while the
remote command runs. Unbounded fan-out across lanes pushed the cell to
load 8.7 (2026-09-29) and forced the watchdog to SIGSTOP workers.

This module implements a simple N-slot semaphore with flock: at most
MAX_CONCURRENT heavy bridge ops run at once; extras wait in a queue
instead of thrashing the cell. No task is ever cancelled or failed by
the guard — worst case it waits, then fails open after WAIT_TIMEOUT.

Usage:
    from bridge_sem import bridge_slot
    with bridge_slot():
        ...heavy bridge call...
"""
import fcntl
import os
import sys
import time

MAX_CONCURRENT = 3
WAIT_TIMEOUT = 600
SEM_DIR = os.path.expanduser("~/.bridge-sem")


class bridge_slot:
    """Context manager holding one bridge concurrency slot."""

    def __init__(self, timeout=WAIT_TIMEOUT):
        self.timeout = timeout
        self._fds = []

    def __enter__(self):
        try:
            os.makedirs(SEM_DIR, exist_ok=True)
        except OSError:
            return self  # fail open if we cannot even make the dir
        deadline = time.time() + self.timeout
        while True:
            for i in range(MAX_CONCURRENT):
                path = os.path.join(SEM_DIR, "slot-%d.lock" % i)
                try:
                    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o644)
                except OSError:
                    continue
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError:
                    os.close(fd)
                    continue
                self._fds.append(fd)
                return self
            if time.time() >= deadline:
                print("bridge_sem: slot wait timed out after %ds, "
                      "proceeding unguarded" % self.timeout,
                      file=sys.stderr, flush=True)
                return self
            time.sleep(0.2)

    def __exit__(self, exc_type, exc, tb):
        for fd in self._fds:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except OSError:
                pass
            try:
                os.close(fd)
            except OSError:
                pass
        self._fds = []
        return False
