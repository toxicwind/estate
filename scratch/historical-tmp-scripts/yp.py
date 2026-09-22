#!/usr/bin/env python3
import yaml
doc1 = """
peers:
  aaa:
    proxy: https://x
   --- divider: hello ---
  bbb:
    proxy: https://y
"""
d = yaml.safe_load(doc1)
print("doc1 OK:", list(d["peers"].keys()))
