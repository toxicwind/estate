#!/usr/bin/env python3
"""Coordinator patch 3b: fix log append call (fleet_log takes key=, not hmac=).

Decision: the log record goes unsigned. log.jsonl is a parallel index, not a
trust boundary -- integrity is verified against the signed .md files, and a
lost/corrupt log is always rebuildable from them.
"""
from pathlib import Path

CHAT = Path("/home/toxic/.shingle/chat/chat.py")
src = CHAT.read_text(encoding="utf-8")

old = """            fleet_log.append(
                root,
                channel,
                seq=seq,
                agent=sender,
                type="message",
                body=body,
                ts=timestamp,
                hmac=sig,
            )"""
new = """            fleet_log.append(
                root,
                channel,
                seq=seq,
                agent=sender,
                type="message",
                body=body,
                ts=timestamp,
            )"""
n = src.count(old)
assert n == 1, f"anchor found {n}x"
src = src.replace(old, new, 1)
CHAT.write_text(src, encoding="utf-8")
print("fixed")
