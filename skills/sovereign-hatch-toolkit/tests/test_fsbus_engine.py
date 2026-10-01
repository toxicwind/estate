"""Tests for orchestrator/fsbus_engine.py — atomic POSIX filesystem message bus."""
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from orchestrator.fsbus_engine import FSBusEngine


class TestFSBusEngine(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="fsbus_test_"))
        self.bus = FSBusEngine(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_dirs_and_manifest_created(self):
        for d in ("inbox", "claimed", "outbox", "dead"):
            self.assertTrue((self.tmp / d).is_dir())
        self.assertTrue((self.tmp / "manifest.jsonl").exists())

    def test_submit_claim_finish_ok(self):
        tid = self.bus.submit({"cmd": "echo", "arg": "hi"})
        claimed = self.bus.claim("worker_1")
        self.assertIsNotNone(claimed)
        cid, payload = claimed
        self.assertEqual(cid, tid)
        self.assertEqual(payload["arg"], "hi")
        self.bus.finish(cid, "worker_1", ok=True, result={"ok": True})
        out = self.tmp / "outbox" / f"{cid}.json"
        self.assertTrue(out.exists())
        self.assertEqual(json.loads(out.read_text())["ok"], True)
        # claimed file cleaned up
        self.assertFalse((self.tmp / "claimed" / f"{cid}.worker_1.json").exists())

    def test_claim_empty_returns_none(self):
        self.assertIsNone(self.bus.claim("worker_1"))

    def test_claim_race_single_winner(self):
        tid = self.bus.submit({"cmd": "x"})
        results = []
        barrier = threading.Barrier(8)

        def worker(wid):
            barrier.wait()
            r = self.bus.claim(wid)
            if r is not None:
                results.append(r[0])

        threads = [threading.Thread(target=worker, args=(f"w{i}",)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], tid)

    def test_retry_then_dead_letter(self):
        bus = FSBusEngine(self.tmp, max_attempts=2)
        tid = bus.submit({"cmd": "flaky"})
        cid, _ = bus.claim("w1")
        bus.finish(cid, "w1", ok=False, result={}, error="boom")
        # requeued to inbox
        self.assertTrue((self.tmp / "inbox" / f"{tid}.json").exists())
        cid2, _ = bus.claim("w1")
        self.assertEqual(cid2, tid)
        bus.finish(cid2, "w1", ok=False, result={}, error="boom again")
        dead = self.tmp / "dead" / f"{tid}.json"
        self.assertTrue(dead.exists())
        rec = json.loads(dead.read_text())
        self.assertEqual(rec["attempts"], 2)
        self.assertIn("boom", rec["error"])

    def test_reap_expired_returns_to_inbox(self):
        bus = FSBusEngine(self.tmp, lease_sec=0.05)
        tid = bus.submit({"cmd": "slow"})
        bus.claim("w1")
        self.assertFalse(list(bus.inbox.glob("*.json")))
        time.sleep(0.08)
        bus.reap_expired()
        self.assertTrue((self.tmp / "inbox" / f"{tid}.json").exists())

    def test_manifest_records_lifecycle(self):
        tid = self.bus.submit({"cmd": "echo"})
        self.bus.claim("w1")
        self.bus.finish(tid, "w1", ok=True, result={})
        types = [
            json.loads(line)["type"]
            for line in (self.tmp / "manifest.jsonl").read_text().splitlines()
        ]
        self.assertEqual(types, ["submitted", "succeeded"])

    def test_atomic_write_durable(self):
        dest = self.tmp / "probe.bin"
        self.bus.atomic_write(dest, b"\x00\x01\x02" * 1000)
        self.assertEqual(dest.read_bytes(), b"\x00\x01\x02" * 1000)
        # no tmp litter left behind
        self.assertEqual(list(self.tmp.glob("*.tmp-*")), [])

    def test_worker_thread_end_to_end(self):
        seen = []
        t = self.bus.start_worker("w1", lambda task: seen.append(task["n"]) or {"done": True})
        for i in range(5):
            self.bus.submit({"n": i})
        deadline = time.time() + 5
        while len(seen) < 5 and time.time() < deadline:
            time.sleep(0.05)
        self.bus.stop_event.set()
        t.join(timeout=5)
        self.assertEqual(sorted(seen), [0, 1, 2, 3, 4])
        self.assertEqual(len(list((self.tmp / "outbox").glob("*.json"))), 5)


if __name__ == "__main__":
    unittest.main()
