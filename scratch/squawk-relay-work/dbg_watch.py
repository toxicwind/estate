#!/usr/bin/env python3
"""Debug: full FeedState + watch loop + post, like the test."""
import tempfile
import threading
import time
import traceback
from pathlib import Path
from types import SimpleNamespace

import chat
import fleet_identity
import squawk_feed

tmp = tempfile.TemporaryDirectory()
root = Path(tmp.name) / "chat-root"
keys = Path(tmp.name) / "keys"
keys.mkdir()
chat.cmd_init(root, SimpleNamespace(channel="fleet", members="relay,alice",
                                    topic="test", ephemeral=None))
fleet_identity.keygen("relay", kd=keys)

state = squawk_feed.FeedState(root / "fleet", "fleet", "relay", keys)
print("initial high:", state.high, flush=True)

def watch():
    try:
        squawk_feed._watch_loop(state)
    except Exception:
        traceback.print_exc()

t = threading.Thread(target=watch, daemon=True)
t.start()
time.sleep(0.5)
print("watcher alive:", t.is_alive(), flush=True)

seq, fname = chat._post_message(root, "fleet", body="hello debug",
                                sender="relay", title="t", key_dir=keys)
print("posted", seq, fname, flush=True)
for i in range(10):
    time.sleep(0.3)
    print(f"t={0.3*(i+1):.1f}s high={state.high} watcher_alive={t.is_alive()}",
          flush=True)
    if state.high >= seq:
        break
print("final high:", state.high, flush=True)
