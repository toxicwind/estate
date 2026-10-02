"""Unit tests for kodi-resume (stdlib only). Run: python3 -m unittest -v."""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))

import importlib.util

from importlib.machinery import SourceFileLoader

loader = SourceFileLoader(
    "kodi_resume",
    os.path.join(os.path.dirname(__file__), "..", "bin", "kodi-resume"))
spec = importlib.util.spec_from_loader("kodi_resume", loader)
kr = importlib.util.module_from_spec(spec)
loader.exec_module(kr)


def canned(*responses):
    """Build a urlopen mock yielding canned JSON-RPC bodies in order."""
    calls = []

    def fake(req, timeout=None):
        calls.append(json.loads(req.data.decode()))
        body = responses[min(len(calls) - 1, len(responses) - 1)]
        m = mock.Mock()
        m.read.return_value = json.dumps(body).encode()
        return m

    fake.calls = calls
    return fake


class TestPureLogic(unittest.TestCase):
    def test_seek_pct(self):
        self.assertAlmostEqual(kr.seek_pct(300, 1200), 25.0)
        self.assertAlmostEqual(kr.seek_pct(0, 100), 0.0)
        self.assertAlmostEqual(kr.seek_pct(99999, 100), 99.5)  # clamped
        self.assertIsNone(kr.seek_pct(10, 0))                   # live/unknown
        self.assertIsNone(kr.seek_pct(10, -5))

    def test_to_sec(self):
        self.assertAlmostEqual(
            kr.to_sec({"hours": 1, "minutes": 2, "seconds": 3,
                       "milliseconds": 500}), 3723.5)

    def test_merge_session_appends_new(self):
        s = []
        new = {"box": "246", "file": "plugin://x/play/1", "position_sec": 100.0,
               "title": "T", "total_sec": 600.0, "saved_at": "2026-09-19T10:00:00+00:00"}
        out, action = kr.merge_session(s, new)
        self.assertEqual(action, "recorded")
        self.assertEqual(len(out), 1)

    def test_merge_session_updates_in_place_within_window(self):
        s = [{"box": "246", "file": "plugin://x/play/1", "position_sec": 100.0,
              "title": "T", "total_sec": 600.0, "saved_at": "t0"}]
        new = dict(s[0], position_sec=140.0, saved_at="t1")  # +40s < 60s window
        out, action = kr.merge_session(s, new)
        self.assertEqual(action, "updated")
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["position_sec"], 140.0)
        self.assertEqual(out[0]["saved_at"], "t1")

    def test_merge_session_appends_after_window(self):
        s = [{"box": "246", "file": "plugin://x/play/1", "position_sec": 100.0,
              "title": "T", "total_sec": 600.0, "saved_at": "t0"}]
        new = dict(s[0], position_sec=500.0, saved_at="t1")  # +400s > window
        out, action = kr.merge_session(s, new)
        self.assertEqual(action, "recorded")
        self.assertEqual(len(out), 2)

    def test_merge_session_distinguishes_boxes(self):
        s = [{"box": "246", "file": "plugin://x/play/1", "position_sec": 100.0,
              "title": "T", "total_sec": 600.0, "saved_at": "t0"}]
        new = dict(s[0], box="225", position_sec=120.0, saved_at="t1")
        out, action = kr.merge_session(s, new)
        self.assertEqual(action, "recorded")
        self.assertEqual(len(out), 2)

    def test_pick_session_newest_other_box(self):
        sessions = [
            {"box": "225", "file": "a", "saved_at": "2026-09-19T09:00:00+00:00"},
            {"box": "246", "file": "b", "saved_at": "2026-09-19T10:00:00+00:00"},
            {"box": "225", "file": "c", "saved_at": "2026-09-19T11:00:00+00:00"},
        ]
        picked = kr.pick_session(sessions, "246")
        self.assertEqual(picked["file"], "c")  # newest not from 246

    def test_pick_session_none_when_only_same_box(self):
        sessions = [{"box": "225", "file": "a", "saved_at": "t"}]
        self.assertIsNone(kr.pick_session(sessions, "225"))

    def test_pick_session_skips_empty_file(self):
        sessions = [{"box": "246", "file": "", "saved_at": "t2"},
                    {"box": "246", "file": "b", "saved_at": "t1"}]
        self.assertEqual(kr.pick_session(sessions, "225")["file"], "b")

    def test_prune_keeps_newest(self):
        with tempfile.TemporaryDirectory() as d:
            kr.STATE_FILE = os.path.join(d, "resume.json")
            kr.STATE_DIR = d
            sessions = [{"box": "246", "file": f"f{i}",
                         "saved_at": f"2026-09-19T10:{i:02d}:00+00:00"}
                        for i in range(5)]
            kr.save_state(sessions)
            kr.prune(keep=3)
            kept = kr.load_state()
            self.assertEqual(len(kept), 3)
            self.assertEqual(kept[0]["file"], "f2")
            self.assertEqual(kept[-1]["file"], "f4")


class TestRpcLayer(unittest.TestCase):
    def test_scan_box_idle(self):
        fake = canned({"id": 1, "jsonrpc": "2.0", "result": []})
        with mock.patch.object(kr.urllib.request, "urlopen", fake):
            self.assertIsNone(kr.scan_box("246"))
        self.assertEqual(fake.calls[0]["method"], "Player.GetActivePlayers")

    def test_scan_box_playing(self):
        fake = canned(
            {"id": 1, "jsonrpc": "2.0",
             "result": [{"playerid": 1, "type": "video"}]},
            {"id": 1, "jsonrpc": "2.0",
             "result": {"time": {"hours": 0, "minutes": 5, "seconds": 0,
                                 "milliseconds": 0},
                        "totaltime": {"hours": 0, "minutes": 50, "seconds": 0,
                                      "milliseconds": 0}}},
            {"id": 1, "jsonrpc": "2.0",
             "result": {"item": {"file": "plugin://plugin.video.x/play/9",
                                 "title": "Cool Show"}}},
        )
        with mock.patch.object(kr.urllib.request, "urlopen", fake):
            snap = kr.scan_box("246")
        self.assertEqual(snap["box"], "246")
        self.assertEqual(snap["title"], "Cool Show")
        self.assertEqual(snap["position_sec"], 300.0)
        self.assertEqual(snap["total_sec"], 3000.0)
        methods = [c["method"] for c in fake.calls]
        self.assertEqual(methods, ["Player.GetActivePlayers",
                                   "Player.GetProperties", "Player.GetItem"])

    def test_scan_box_ignores_barely_started(self):
        fake = canned(
            {"id": 1, "jsonrpc": "2.0",
             "result": [{"playerid": 1, "type": "video"}]},
            {"id": 1, "jsonrpc": "2.0",
             "result": {"time": {"hours": 0, "minutes": 0, "seconds": 5,
                                 "milliseconds": 0},
                        "totaltime": {"hours": 1, "minutes": 0, "seconds": 0,
                                      "milliseconds": 0}}},
            {"id": 1, "jsonrpc": "2.0",
             "result": {"item": {"file": "x", "title": "T"}}},
        )
        with mock.patch.object(kr.urllib.request, "urlopen", fake):
            self.assertIsNone(kr.scan_box("246"))  # 5s < MIN_POSITION_SEC

    def test_rpc_raises_on_error(self):
        fake = canned({"id": 1, "jsonrpc": "2.0",
                       "error": {"code": -32602, "message": "bad"}})
        with mock.patch.object(kr.urllib.request, "urlopen", fake):
            with self.assertRaises(RuntimeError):
                kr.rpc("10.0.0.246", "Player.Seek")

    def test_open_and_seek_dry_run_payloads(self):
        session = {"box": "246", "title": "T", "file": "plugin://x/play/1",
                   "position_sec": 300.0, "total_sec": 1200.0,
                   "saved_at": "t"}
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            kr.open_and_seek("10.0.0.225", session, play=False, dry_run=True)
        out = buf.getvalue()
        self.assertIn("plugin://x/play/1", out)   # open payload
        self.assertIn("25.0%", out)               # wrapped percentage seek
        self.assertIn("leave paused", out)

    def test_open_and_seek_live_stream_no_seek(self):
        session = {"box": "246", "title": "Live", "file": "plugin://x/live",
                   "position_sec": 300.0, "total_sec": 0.0, "saved_at": "t"}
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            kr.open_and_seek("10.0.0.225", session, dry_run=True)
        self.assertIn("no seek after open", buf.getvalue())

    def test_continue_refuses_when_target_playing(self):
        fake = canned({"id": 1, "jsonrpc": "2.0",
                       "result": [{"playerid": 1, "type": "video"}]})
        with tempfile.TemporaryDirectory() as d:
            kr.STATE_FILE = os.path.join(d, "resume.json")
            kr.STATE_DIR = d
            kr.save_state([{"box": "246", "file": "f",
                            "saved_at": "2026-09-19T10:00:00+00:00",
                            "title": "T", "position_sec": 60,
                            "total_sec": 600}])
            with mock.patch.object(kr.urllib.request, "urlopen", fake):
                with self.assertRaises(SystemExit) as cm:
                    kr.continue_on("225", apply=False)
            self.assertIn("refusing", str(cm.exception))

    def test_continue_no_session_exits(self):
        with tempfile.TemporaryDirectory() as d:
            kr.STATE_FILE = os.path.join(d, "resume.json")
            kr.STATE_DIR = d
            kr.save_state([])
            fake = canned({"id": 1, "jsonrpc": "2.0", "result": []})
            with mock.patch.object(kr.urllib.request, "urlopen", fake):
                with self.assertRaises(SystemExit):
                    kr.continue_on("225", apply=False)


if __name__ == "__main__":
    unittest.main()
