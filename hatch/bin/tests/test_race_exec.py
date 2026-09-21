#!/usr/bin/env python3
"""13-test suite for race_exec.py (bridge auto-racer with dispatch-gating).

All tests use an injected fake exec module — no sockets, no network,
no yote. The one real-socket touch is a bound unix socket file standing
in for the WS daemon socket, so the WS readiness probe runs for real.

Run: python3 test_race_exec.py
"""

import json
import os
import socket
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import race_exec


class FakeExec:
    """Controllable stand-in for exec.py's lane primitives."""

    def __init__(self):
        self.WS_SOCK = "/nonexistent-ws-race-test.sock"
        self._DEFAULT_READ_TIMEOUT = 150
        self.ws_down = False
        self.https_down = (False, "")
        self.ws_dispatches: list = []
        self.https_dispatches: list = []
        self.ws_behavior = "ok"  # ok | none (pre-dispatch) | raise
        self.ws_delay = 0.0
        self.https_delay = 0.0
        self.session = "sess-1"
        self.active = 0
        self.max_active = 0
        self._lock = threading.Lock()

    # -- lane flags -----------------------------------------------------
    def _ws_known_down(self):
        return self.ws_down

    def _https_known_down(self):
        return self.https_down

    def _load_session(self):
        return self.session

    def _initialize(self, read_timeout):
        self.session = "sess-2"
        return self.session

    # -- dispatch --------------------------------------------------------
    def _ws_exec(self, cmd, workdir, argv, timeout, capture):
        with self._lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        try:
            time.sleep(self.ws_delay)
            self.ws_dispatches.append(cmd)
            if self.ws_behavior == "none":
                return None
            if self.ws_behavior == "raise":
                raise RuntimeError("correlation failed: id mismatch")
            return {"code": 0, "stdout": "ws:" + cmd, "stderr": "",
                    "ok": True, "transport": "ws", "error": None}
        finally:
            with self._lock:
                self.active -= 1

    def _https_exec_capture(self, cmd, workdir, read_timeout):
        with self._lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        try:
            time.sleep(self.https_delay)
            self.https_dispatches.append(cmd)
            return {"code": 0, "stdout": "https:" + cmd, "stderr": "",
                    "ok": True, "transport": "https", "error": None,
                    "duration_ms": 1}
        finally:
            with self._lock:
                self.active -= 1


class RaceTest(unittest.TestCase):
    def setUp(self):
        self.fake = FakeExec()
        # a real bound unix socket standing in for the WS daemon socket
        self._tmp = tempfile.mkdtemp(prefix="race-test-")
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sock.bind(os.path.join(self._tmp, "ws.sock"))
        self._sock.listen(1)
        self.ws_live = os.path.join(self._tmp, "ws.sock")
        self._ledger = tempfile.NamedTemporaryFile(
            "w", suffix=".jsonl", delete=False)
        self._ledger.close()
        self._ledger_patch = mock.patch.object(
            race_exec, "LEDGER", self._ledger.name)
        self._ledger_patch.start()

    def tearDown(self):
        self._ledger_patch.stop()
        self._sock.close()
        try:
            os.unlink(self.ws_live)
            os.unlink(self._ledger.name)
            os.rmdir(self._tmp)
        except OSError:
            pass
        os.environ.pop("AWRAWR_TRANSPORT", None)

    def race(self, cmd="echo hi", **kw):
        kw.setdefault("_exec", self.fake)
        kw.setdefault("gate_ceiling", 5.0)
        return race_exec.race_exec(cmd, "/home/toxic", **kw)

    # 1
    def test_ws_wins_dispatch_race(self):
        self.fake.WS_SOCK = self.ws_live
        self.fake.https_down = (True, "degraded")
        r = self.race()
        self.assertEqual(r["race_winner"], "ws")
        self.assertEqual(r["stdout"], "ws:echo hi")
        self.assertFalse(r["fell_back"])

    # 2
    def test_https_wins_when_ws_unavailable(self):
        # (a) WS socket absent -> probe fails -> https dispatches
        r = self.race()
        self.assertEqual(r["race_winner"], "https")
        self.assertEqual(r["stdout"], "https:echo hi")
        self.assertEqual(self.fake.ws_dispatches, [])
        # (b) AWRAWR_TRANSPORT=https forces https even with ws healthy
        self.fake.WS_SOCK = self.ws_live
        with mock.patch.dict(os.environ, {"AWRAWR_TRANSPORT": "https"}):
            r = self.race()
        self.assertEqual(r["race_winner"], "https")
        self.assertEqual(self.fake.ws_dispatches, [])

    # 3
    def test_ws_down_flag_skips_ws_lane(self):
        self.fake.WS_SOCK = self.ws_live  # healthy socket, but flagged down
        self.fake.ws_down = True
        r = self.race()
        self.assertEqual(r["race_winner"], "https")
        self.assertIn("marked down", r["lanes_probed"]["ws"])
        self.assertEqual(self.fake.ws_dispatches, [])

    # 4
    def test_https_degraded_skips_https_lane(self):
        self.fake.WS_SOCK = self.ws_live
        self.fake.https_down = (True, "read stall")
        r = self.race()
        self.assertEqual(r["race_winner"], "ws")
        self.assertIn("read stall", r["lanes_probed"]["https"])

    # 5
    def test_both_down_raises_no_dispatch(self):
        self.fake.ws_down = True
        self.fake.https_down = (True, "both dead")
        with self.assertRaises(race_exec.RaceError):
            self.race()
        self.assertEqual(self.fake.ws_dispatches, [])
        self.assertEqual(self.fake.https_dispatches, [])

    # 6
    def test_idempotent_full_race_first_valid_wins(self):
        self.fake.WS_SOCK = self.ws_live
        self.fake.ws_delay = 0.4
        self.fake.https_delay = 0.0
        r = self.race(idempotent=True)
        self.assertEqual(r["race_mode"], "full-race")
        self.assertEqual(r["race_winner"], "https")
        self.assertEqual(r["stdout"], "https:echo hi")
        self.assertEqual(self.fake.https_dispatches, ["echo hi"])
        # the loser is ABANDONED at first-valid: it may never have
        # dispatched (idempotent mode makes that safe)
        self.assertLessEqual(len(self.fake.ws_dispatches), 1)

    # 7
    def test_non_idempotent_loser_never_dispatches(self):
        self.fake.WS_SOCK = self.ws_live
        self.fake.https_down = (True, "degraded")
        r = self.race()  # default: dispatch-race, NOT idempotent
        self.assertEqual(r["race_mode"], "dispatch-race")
        self.assertEqual(r["race_winner"], "ws")
        self.assertEqual(self.fake.ws_dispatches, ["echo hi"])
        self.assertEqual(self.fake.https_dispatches, [])

    # 8
    def test_gate_limits_concurrent_dispatch(self):
        self.fake.WS_SOCK = self.ws_live
        self.fake.ws_delay = 0.3
        errs = []

        def worker():
            try:
                self.race(gate_size=2)
            except Exception as e:  # noqa: BLE001
                errs.append(e)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=15)
        self.assertEqual(errs, [])
        self.assertLessEqual(self.fake.max_active, 2)
        # the probe race is nondeterministic (both probes instant), so the
        # 4 dispatches may split across lanes; the gate bounds the total
        total = len(self.fake.ws_dispatches) + len(self.fake.https_dispatches)
        self.assertEqual(total, 4)

    # 9
    def test_gate_timeout_fails_fast(self):
        g = race_exec.gate(1)
        g.acquire()  # hold the only gate token
        try:
            t0 = time.monotonic()
            with self.assertRaises(race_exec.GateTimeout):
                self.race(gate_size=1, gate_ceiling=0.2)
            self.assertLess(time.monotonic() - t0, 2.0)
        finally:
            g.release()
        self.assertEqual(self.fake.ws_dispatches, [])
        self.assertEqual(self.fake.https_dispatches, [])

    # 10
    def test_ws_predispatch_none_falls_back_to_https(self):
        self.fake.WS_SOCK = self.ws_live
        self.fake.ws_behavior = "none"  # daemon never saw the command
        r = self.race()
        self.assertEqual(r["race_winner"], "ws")
        self.assertTrue(r["fell_back"])
        self.assertEqual(r["fell_back_from"], "ws")
        self.assertEqual(r["stdout"], "https:echo hi")

    # 11
    def test_ws_dispatch_raise_no_double_dispatch(self):
        self.fake.WS_SOCK = self.ws_live
        self.fake.ws_behavior = "raise"  # post-dispatch failure
        r = self.race()
        self.assertEqual(r["race_winner"], "ws")
        self.assertFalse(r["fell_back"])
        self.assertIsNotNone(r["error"])
        # the command may have executed on ws: https MUST NOT re-run it
        self.assertEqual(self.fake.https_dispatches, [])

    # 12
    def test_ledger_appends_fsyncd_jsonl(self):
        self.fake.WS_SOCK = self.ws_live
        self.fake.https_down = (True, "degraded")
        self.race(cmd="echo ledger")
        with open(self._ledger.name, encoding="utf-8") as f:
            lines = f.read().strip().split("\n")
        self.assertEqual(len(lines), 1)
        e = json.loads(lines[0])
        self.assertEqual(e["race_winner"], "ws")
        self.assertEqual(e["race_mode"], "dispatch-race")
        self.assertIn("race_ms", e)
        self.assertIn("gate_wait_ms", e)
        self.assertTrue(e["lanes"]["ws"]["ok"])

    # 13
    def test_race_bounded_when_a_lane_hangs(self):
        def hang(_m):
            time.sleep(5)
            return False, 5000.0, "hung"

        with mock.patch.object(race_exec, "_probe_ws", side_effect=hang):
            t0 = time.monotonic()
            r = self.race()  # https probe is instant (cached session)
            dt = time.monotonic() - t0
        self.assertEqual(r["race_winner"], "https")
        self.assertLess(dt, 4.0,
                        "abandoned probe thread must not stall the race")


if __name__ == "__main__":
    unittest.main(verbosity=2)
