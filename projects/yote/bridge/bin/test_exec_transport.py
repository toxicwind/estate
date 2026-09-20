#!/usr/bin/env python3
"""Unit tests for exec.py transport hardening (stdlib only, no network).

Covers:
  - unique JSON-RPC request ids (_new_id)
  - SSE response correlation: matching envelope accepted, foreign lines
    skipped/counted, fail-loud on no match
  - local read deadline: fires on a stalled stream (proves the 24-minute
    hang from finding #2 cannot recur)
  - degraded-transport signal: IncompleteRead / stall / deadline /
    correlation failure mark the HTTPS lane down; TTL expiry recovers;
    main() fails fast while the marker is fresh
"""
import http.client
import importlib.util
import json
import os
import re
import socket
import sys
import tempfile
import time
import unittest
from unittest import mock

BIN = os.path.dirname(os.path.abspath(__file__))


def load_exec():
    spec = importlib.util.spec_from_file_location(
        "exec_mod", os.path.join(BIN, "exec.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


exec_mod = load_exec()


class FakeSSE:
    """Minimal urlopen() response stub for the SSE branch."""

    def __init__(self, lines=None, readline_fn=None, ctype="text/event-stream",
                 sid="sess-1"):
        self._lines = list(lines or [])
        self._readline_fn = readline_fn
        self.headers = {"Content-Type": ctype, "Mcp-Session-Id": sid}
        self.readline_calls = 0
        self.closed = False

    def readline(self):
        self.readline_calls += 1
        if self._readline_fn is not None:
            return self._readline_fn()
        if self._lines:
            return self._lines.pop(0)
        return b""

    def read(self, n=-1):
        return b""

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.closed = True
        return False


class FakeJSON:
    """Minimal urlopen() response stub for the application/json branch."""

    def __init__(self, body: bytes, sid="sess-1"):
        self._body = body
        self.headers = {"Content-Type": "application/json",
                        "Mcp-Session-Id": sid}

    def read(self, n=65536):
        chunk, self._body = self._body[:n], self._body[n:]
        return chunk

    def readline(self):
        return b""

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def sse_line(doc):
    return ("data: " + json.dumps(doc) + "\n").encode()


class TestNewId(unittest.TestCase):
    def test_unique_and_format(self):
        ids = {exec_mod._new_id() for _ in range(2000)}
        self.assertEqual(len(ids), 2000)
        for i in ids:
            self.assertRegex(i, r"^exec-\d+-[0-9a-f]{12}$")


class TestSSECorrelation(unittest.TestCase):
    def test_match_accepted_foreign_skipped(self):
        want = "exec-999-abcdef123456"
        resp = FakeSSE([
            b": ping\n",
            b"\n",
            sse_line({"jsonrpc": "2.0", "id": "other-caller", "result": {}}),
            b"data: not-json\n",
            sse_line({"jsonrpc": "2.0", "id": want,
                      "result": {"content": [{"text": "[exit=0] hi"}]}}),
            sse_line({"jsonrpc": "2.0", "id": "late-foreign", "result": {}}),
        ])
        calls_before = resp.readline_calls
        doc, foreign = exec_mod._read_sse_correlated(
            resp, want, time.monotonic() + 30)
        self.assertEqual(doc["id"], want)
        self.assertEqual(doc["result"]["content"][0]["text"], "[exit=0] hi")
        self.assertEqual(foreign, 2)  # other-caller envelope + not-json
        # early return: the trailing foreign line must NOT be consumed
        self.assertEqual(resp.readline_calls, calls_before + 5)

    def test_eof_without_match_raises(self):
        want = "exec-999-abcdef123456"
        resp = FakeSSE([
            sse_line({"jsonrpc": "2.0", "id": "someone-else", "result": {}}),
        ])
        with self.assertRaises(exec_mod._CorrelationFailed) as ctx:
            exec_mod._read_sse_correlated(resp, want, time.monotonic() + 30)
        self.assertIn("correlation failed", str(ctx.exception))
        self.assertIn("1 foreign", str(ctx.exception))

    def test_notification_empty_stream_returns_empty(self):
        resp = FakeSSE([])
        doc, foreign = exec_mod._read_sse_correlated(
            resp, exec_mod._MISSING, time.monotonic() + 30)
        self.assertEqual(doc, {})
        self.assertEqual(foreign, 0)

    def test_notification_first_doc_returned(self):
        resp = FakeSSE([sse_line({"ok": True})])
        doc, _ = exec_mod._read_sse_correlated(
            resp, exec_mod._MISSING, time.monotonic() + 30)
        self.assertEqual(doc, {"ok": True})


class TestReadDeadline(unittest.TestCase):
    def test_deadline_fires_on_stalled_sse_stream(self):
        # The finding-#2 shape: a stream that never delivers our response
        # and never closes (keep-alive comments only).
        resp = FakeSSE(readline_fn=lambda: b": ping\n")
        t0 = time.monotonic()
        with self.assertRaises(exec_mod._ReadDeadlineExceeded):
            exec_mod._read_sse_correlated(resp, "exec-1-x",
                                          time.monotonic() + 0.3)
        elapsed = time.monotonic() - t0
        self.assertLess(elapsed, 10, "deadline must fire, not hang")

    def test_deadline_fires_on_stalled_body_read(self):
        resp = FakeJSON(b"x" * 16)
        # read() that never returns b"" -> would hang forever unbounded
        resp.read = lambda n=65536: b"y" * 8
        t0 = time.monotonic()
        with self.assertRaises(exec_mod._ReadDeadlineExceeded):
            exec_mod._read_body_bounded(resp, time.monotonic() + 0.3)
        self.assertLess(time.monotonic() - t0, 10)

    def test_body_bounded_reads_normally(self):
        resp = FakeJSON(b'{"a": 1}')
        self.assertEqual(
            exec_mod._read_body_bounded(resp, time.monotonic() + 30),
            b'{"a": 1}')


class TestPostDegradedLane(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="exec-test-")
        self.flag = os.path.join(self.tmp, "https-down")
        self._p1 = mock.patch.object(exec_mod, "_HTTPS_DOWN_FLAG", self.flag)
        self._p2 = mock.patch.object(exec_mod, "_HTTPS_DOWN_TTL", 60)
        self._p3 = mock.patch.object(exec_mod, "ensure_allowed_url",
                                     lambda *a, **k: None)
        self._p4 = mock.patch.object(exec_mod, "add_surrogate_to_request",
                                     lambda *a, **k: None)
        for p in (self._p1, self._p2, self._p3, self._p4):
            p.start()
        self.addCleanup(self._p1.stop)
        self.addCleanup(self._p2.stop)
        self.addCleanup(self._p3.stop)
        self.addCleanup(self._p4.stop)

    def _post(self, resp, payload_id="exec-7-deadbeef1234", timeout=5):
        payload = {"jsonrpc": "2.0", "id": payload_id, "method": "tools/call",
                   "params": {}}
        with mock.patch.object(exec_mod.urllib.request, "urlopen",
                               return_value=resp):
            return exec_mod._post(payload, "sess-1", timeout)

    def test_incomplete_read_marks_lane_degraded(self):
        def boom():
            raise http.client.IncompleteRead(b"partial", 2250)
        resp = FakeSSE(readline_fn=boom)
        with self.assertRaises(RuntimeError) as ctx:
            self._post(resp)
        msg = str(ctx.exception)
        self.assertIn("IncompleteRead", msg)
        self.assertIn("marked degraded", msg)
        down, reason = exec_mod._https_known_down()
        self.assertTrue(down)
        self.assertIn("IncompleteRead", reason)

    def test_socket_timeout_marks_lane_degraded(self):
        def boom():
            raise socket.timeout("timed out")
        resp = FakeSSE(readline_fn=boom)
        with self.assertRaises(RuntimeError) as ctx:
            self._post(resp)
        self.assertIn("timed out", str(ctx.exception))
        down, _ = exec_mod._https_known_down()
        self.assertTrue(down)

    def test_read_deadline_marks_lane_degraded(self):
        resp = FakeSSE(readline_fn=lambda: b": ping\n")
        t0 = time.monotonic()
        with self.assertRaises(RuntimeError) as ctx:
            self._post(resp, timeout=0.3)
        self.assertIn("read deadline exceeded", str(ctx.exception))
        self.assertLess(time.monotonic() - t0, 10)
        down, reason = exec_mod._https_known_down()
        self.assertTrue(down)
        self.assertIn("deadline", reason)

    def test_correlation_failure_marks_lane_degraded(self):
        resp = FakeSSE([sse_line({"jsonrpc": "2.0", "id": "foreign",
                                  "result": {}})])
        with self.assertRaises(RuntimeError) as ctx:
            self._post(resp)
        self.assertIn("correlation failed", str(ctx.exception))
        down, _ = exec_mod._https_known_down()
        self.assertTrue(down)

    def test_json_branch_id_mismatch_marks_degraded(self):
        body = json.dumps({"jsonrpc": "2.0", "id": "someone-else",
                           "result": {}}).encode()
        with self.assertRaises(RuntimeError) as ctx:
            self._post(FakeJSON(body))
        self.assertIn("correlation failed", str(ctx.exception))
        down, _ = exec_mod._https_known_down()
        self.assertTrue(down)

    def test_json_branch_match_ok(self):
        body = json.dumps({"jsonrpc": "2.0", "id": "exec-7-deadbeef1234",
                           "result": {"ok": 1}}).encode()
        doc, sid = self._post(FakeJSON(body))
        self.assertEqual(doc["result"], {"ok": 1})
        self.assertEqual(sid, "sess-1")
        down, _ = exec_mod._https_known_down()
        self.assertFalse(down)

    def test_degraded_marker_ttl_expiry_recovers(self):
        exec_mod._https_mark_down("test")
        down, _ = exec_mod._https_known_down()
        self.assertTrue(down)
        # backdate past the TTL: lane recovers on its own
        with open(self.flag) as f:
            rec = json.load(f)
        rec["ts"] = time.time() - 3600
        with open(self.flag, "w") as f:
            json.dump(rec, f)
        down, _ = exec_mod._https_known_down()
        self.assertFalse(down)

    def test_main_fails_fast_while_degraded(self):
        exec_mod._https_mark_down("read stall: IncompleteRead")
        with mock.patch.object(exec_mod, "_ws_exec", return_value=None), \
             mock.patch.object(sys, "argv",
                               ["exec.py", "--json", "--argv", "echo", "hi"]):
            with self.assertRaises(RuntimeError) as ctx:
                exec_mod.main()
        self.assertIn("failing fast", str(ctx.exception))
        self.assertIn("IncompleteRead", str(ctx.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
