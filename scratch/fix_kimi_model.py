#!/usr/bin/env python3
"""Resolve kimi-auto -> kimi-k3 (the actual kimi model in herd catalog)."""
import sys

def patch(path, old, new):
    with open(path) as f:
        c = f.read()
    assert c.count(old) == 1, (path, old[:50], c.count(old))
    with open(path, "w") as f:
        f.write(c.replace(old, new))
    print("OK", path)

patch("/home/toxic/sovereign/src/coyote/coyote-loop.py",
      'default=os.environ.get("COYOTE_MODEL", "kimi-auto")',
      'default=os.environ.get("COYOTE_MODEL", "kimi-k3")')
patch("/home/toxic/sovereign/stack/services/coyote.sh",
      'export COYOTE_MODEL="${COYOTE_MODEL:-kimi-auto}"',
      'export COYOTE_MODEL="${COYOTE_MODEL:-kimi-k3}"')
print("DONE")
