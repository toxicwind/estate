#!/usr/bin/env python3
"""Coordinator patch 5b: dedupe DAG parents (reply target == previous)."""
from pathlib import Path

CHAT = Path("/home/toxic/.shingle/chat/chat.py")
src = CHAT.read_text(encoding="utf-8")

old = """    target_id = _resolve_reply_target(d, reply) if reply else None
    return [x for x in (target_id, prev_id) if x]"""
new = """    target_id = _resolve_reply_target(d, reply) if reply else None
    # Dedupe preserving wire order: a reply to the immediately-previous
    # message would otherwise list the same parent twice.
    parents = []
    for x in (target_id, prev_id):
        if x and x not in parents:
            parents.append(x)
    return parents"""
assert src.count(old) == 1
src = src.replace(old, new, 1)
CHAT.write_text(src, encoding="utf-8")
print("fixed")
