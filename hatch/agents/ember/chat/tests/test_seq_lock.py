"""Regression tests for _acquire_lock stale-steal (chat.py).

The old defaults (timeout=10.0, stale=30.0) made the steal branch
unreachable: no poster waited long enough to see a stealable lock, so one
crashed poster wedged the channel permanently.
"""
import os
import tempfile
import time
import unittest
from pathlib import Path

import chat


def _plant_lock(chan: Path, owner_pid: int, age_s: float) -> Path:
    lock = chan / "_seq.lock"
    lock.mkdir(exist_ok=True)
    (lock / "owner").write_text(f"{owner_pid}\n", encoding="utf-8")
    old = time.time() - age_s
    os.utime(lock, (old, old))
    return lock


class SeqLockTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.chan = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_stale_ge_timeout_rejected(self):
        # the exact old misconfiguration must fail fast, not wedge silently
        with self.assertRaises(ValueError):
            chat._acquire_lock(self.chan, timeout=10.0, stale=30.0)

    def test_crashed_poster_lock_stolen(self):
        _plant_lock(self.chan, owner_pid=99999999, age_s=60.0)  # dead pid
        t0 = time.time()
        lock = chat._acquire_lock(self.chan, timeout=5.0, stale=0.1)
        self.assertLess(time.time() - t0, 5.0)
        try:
            owner = int((lock / "owner").read_text().strip())
            self.assertEqual(owner, os.getpid())
        finally:
            chat._release_lock(lock)
        self.assertFalse((self.chan / "_seq.lock").exists())

    def test_live_owner_never_stolen(self):
        _plant_lock(self.chan, owner_pid=os.getpid(), age_s=3600.0)
        with self.assertRaises(chat.AgentChatError):
            chat._acquire_lock(self.chan, timeout=0.4, stale=0.05)
        # lock still there, owned by us
        self.assertTrue((self.chan / "_seq.lock" / "owner").exists())

    def test_acquire_release_roundtrip(self):
        lock = chat._acquire_lock(self.chan, timeout=2.0, stale=0.1)
        chat._release_lock(lock)
        self.assertFalse((self.chan / "_seq.lock").exists())
        # and straight back in
        lock2 = chat._acquire_lock(self.chan, timeout=2.0, stale=0.1)
        chat._release_lock(lock2)
        self.assertFalse((self.chan / "_seq.lock").exists())


if __name__ == "__main__":
    unittest.main()
