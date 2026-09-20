#!/usr/bin/env python3
"""Add [daemons.squawk-feed] to pitchfork.toml (idempotent)."""
import re
from pathlib import Path

TOML = Path("/home/toxic/sovereign/pitchfork.toml")
text = TOML.read_text()

# 1. Add to [groups.all] daemons list (idempotent)
def add_to_all(m):
    lst = m.group(1)
    if '"squawk-feed"' in lst:
        return m.group(0)
    # insert before closing bracket
    new = re.sub(r'"([^"]+)"(\s*\])$', r'"\1", "squawk-feed"\2', lst)
    return m.group(0).replace(lst, new)

new_text, n = re.subn(r'(\[groups\.all\]\ndaemons = \[[^\]]*\])', add_to_all, text, count=1)
if n == 0:
    raise SystemExit("groups.all not found")
text = new_text

# 2. Append stanza if missing
if "[daemons.squawk-feed]" not in text:
    text = text.rstrip("\n") + "\n\n" + """[daemons.squawk-feed]
run = "exec python3 /home/toxic/.shingle/squawk-relay/feed.py"
dir = "/home/toxic/.shingle/squawk-relay"
mise = false
retry = true
boot_start = true
env = { SQUAWK_FEED_PORT = "25135", SQUAWK_CHAT_ROOT = "/home/toxic/.shingle/squawk-root" }
auto = ["start"]
"""

TOML.write_text(text)
print("pitchfork.toml updated")
