#!/usr/bin/env python3
"""Add squawk-relay-sink + squawk-relay-forward daemons to pitchfork.toml.

Idempotent: skips entries that already exist.
"""
from pathlib import Path

TOML = Path("/home/toxic/sovereign/pitchfork.toml")
text = TOML.read_text()

SINK = '''[daemons.squawk-relay-sink]
run = "exec /home/toxic/.shingle/squawk-relay/run-sink.sh"
dir = "/home/toxic/.shingle/squawk-relay"
mise = false
retry = true
boot_start = true
auto = ["start"]
'''

FORWARD = '''[daemons.squawk-relay-forward]
run = "exec /home/toxic/.shingle/squawk-relay/run-forward.sh"
dir = "/home/toxic/.shingle/squawk-relay"
mise = false
retry = true
boot_start = true
auto = ["start"]
'''

changed = False
if "[daemons.squawk-relay-sink]" not in text:
    # insert before the squawk-feed section to keep relay daemons together
    anchor = "[daemons.squawk-feed]"
    assert anchor in text, "squawk-feed section not found"
    text = text.replace(anchor, SINK + "\n" + FORWARD + "\n" + anchor, 1)
    changed = True
    print("added daemon sections")

if '"squawk-relay-sink"' not in text:
    anchor = '"squawk-feed", "squawk-ws"'
    assert anchor in text, "groups.all anchor not found"
    text = text.replace(
        anchor, '"squawk-relay-sink", "squawk-relay-forward", "squawk-feed", "squawk-ws"', 1)
    changed = True
    print("added to groups.all")

if changed:
    TOML.write_text(text)
    print("pitchfork.toml updated")
else:
    print("already configured; no change")
