#!/usr/bin/env python3
"""Smoke test for the three hardening modules, run ON awrawr-pc."""
import os
import sys
import tempfile
import threading
import time

sys.path.insert(0, "/home/toxic/.shingle/chat")
os.environ["FLEET_KEYS_DIR"] = tempfile.mkdtemp(prefix="fk_")

import fleet_identity as fi
import fleet_wait as fw
import fleet_watch as fwt

fi.keygen("smoke-agent")
root = tempfile.mkdtemp(prefix="chat_")
chan = os.path.join(root, "ops")
os.makedirs(chan)

seq, sender = 1, "smoke-agent"
body = "hello fleet"
canon = fi.canonical_message(
    seq=seq, sender=sender, to="all", reply_to=None, channel="ops",
    ts="2026-09-14T05:10:00+00:00", status="discussion", title="smoke", body=body,
)
fm = [
    "---",
    "seq: %d" % seq,
    "from: %s" % sender,
    "to: all",
    "channel: ops",
    "ts: 2026-09-14T05:10:00+00:00",
    "status: discussion",
    "title: smoke",
    "hmac: %s" % fi.sign(sender, canon),
    "---",
    "",
]
mp = os.path.join(chan, "0001-smoke-agent-smoke.md")
with open(mp, "w", encoding="utf-8") as f:
    f.write("\n".join(fm) + body.rstrip() + "\n")
m = fi.verify_on_read(mp)
assert m["from"] == "smoke-agent", m


def poster():
    time.sleep(0.5)
    with open(os.path.join(chan, "0002-smoke-agent-late.md"), "w") as f:
        f.write("x")


threading.Thread(target=poster).start()
t0 = time.monotonic()
res = fw.wait_for_new_messages(chan, 1, 10)
dt = time.monotonic() - t0
assert len(res) == 1 and dt < 5, (res, dt)

fwt.note_channel(root, "ops")
got = list(fwt.watch_channels(root, 0))
assert [n for _, n in got] == ["ops"], got

print("SMOKE-OK verify+inotify(%.2fs)+watch" % dt)
