#!/usr/bin/env python3
import subprocess, sys

sha = sys.argv[1]
row = (
    "| bookworm-chatnative | Chat-native agent research: paper-backed buildable design for "
    "event-driven squawk agents (no polling). Ships @fleet/chat-native Bun/TS module: recursive "
    "long-poll subscribe, tiered attention, TASK directives, AsyncQueue handoff; OpenFang verdict "
    "(stays as runtime, squawk adapter is future work); Solace pattern borrow (reference only) "
    "| Bookworm (Ember's crew) | DONE (2026-09-21) -- commit "
    + sha
    + ", origin/main verified via git ls-remote |"
)

kb = subprocess.run(
    ["git", "-C", "/home/toxic/sovereign", "show", sha + ":docs/fleet-knowledgebase.md"],
    capture_output=True, text=True, check=True,
).stdout

anchor = "Retired/completed crews stay listed here"
assert anchor in kb, "anchor missing"
kb = kb.replace(anchor, row + "\n" + anchor, 1)

with open("/tmp/kb-done.md", "w") as f:
    f.write(kb)
print("wrote /tmp/kb-done.md")
