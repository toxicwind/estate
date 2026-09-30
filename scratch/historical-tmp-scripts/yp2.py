#!/usr/bin/env python3
import yaml
# shape of the ORIGINAL: previous peer block, then comments, then the divider
doc2 = """
peers:
  aaa:
    proxy: https://x
    timeouts:
      connect: 30
  # comment block
  # more comments
   --- divider: hello ---
  # even more
  bbb:
    proxy: https://y
"""
d = yaml.safe_load(doc2)
print("doc2 OK:", list(d["peers"].keys()))
