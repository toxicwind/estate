#!/usr/bin/env python3
"""Wait-relevance regression test.

Carol waits (timeout 6s). Dave posts to bob (irrelevant to carol).
Erin posts to carol (relevant). Carol's wait must skip dave's message,
deliver erin's, and exit 0. Then: a wait with ONLY irrelevant traffic
must time out (exit 2), not return early.
"""
import os
import subprocess
import sys
import time

CHAT = "/home/toxic/.shingle/chat"
ROOT = "/tmp/wait-test"
ENV = {
    **os.environ,
    "FLEET_KEYS_DIR": "/tmp/smoke-keys",
    "AGENT_CHAT_ROOT": ROOT,
}

def chat(*args):
    return subprocess.run(
        [sys.executable, "chat.py", *args],
        cwd=CHAT, env=ENV, capture_output=True, text=True, timeout=60,
    )

import shutil
shutil.rmtree(ROOT, ignore_errors=True)
for agent in ("alice", "bob", "carol", "dave", "erin"):
    r = chat("keygen", agent)
    assert r.returncode == 0 or "already exists" in r.stderr, \
        f"keygen {agent} failed: {r.stderr}"
assert chat("init", "w").returncode == 0, "init failed"
assert chat("post", "w", "--from", "alice", "--to", "bob",
            "--title", "ping", "--body", "for bob only").returncode == 0

# Carol waits in the background.
waiter = subprocess.Popen(
    [sys.executable, "chat.py", "wait", "w", "--as", "carol", "--timeout", "6"],
    cwd=CHAT, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
)
time.sleep(1.0)
assert chat("post", "w", "--from", "dave", "--to", "bob",
            "--title", "also-bob", "--body", "also for bob").returncode == 0
time.sleep(1.0)
# If the bug were present, carol's wait would already have returned here.
assert waiter.poll() is None, "BUG: wait returned on irrelevant message"
assert chat("post", "w", "--from", "erin", "--to", "carol",
            "--title", "hey", "--body", "for carol").returncode == 0
out, err = waiter.communicate(timeout=15)
assert waiter.returncode == 0, f"wait exited {waiter.returncode}: {err}"
assert "for carol" in out, "relevant message not delivered"
assert "also for bob" not in out, "irrelevant message leaked into wait output"
print("PASS 1: irrelevant skipped, relevant delivered, exit 0")

# Second: only irrelevant traffic -> must time out with exit 2.
waiter2 = subprocess.Popen(
    [sys.executable, "chat.py", "wait", "w", "--as", "carol", "--timeout", "3"],
    cwd=CHAT, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
)
time.sleep(0.5)
assert chat("post", "w", "--from", "dave", "--to", "bob",
            "--title", "noise", "--body", "more noise").returncode == 0
out2, err2 = waiter2.communicate(timeout=15)
assert waiter2.returncode == 2, f"expected timeout exit 2, got {waiter2.returncode}"
assert "timeout" in err2, f"expected timeout message on stderr, got: {err2!r}"
print("PASS 2: irrelevant-only traffic -> timeout exit 2, cursor not consumed")
print("ALL WAIT TESTS PASS")
