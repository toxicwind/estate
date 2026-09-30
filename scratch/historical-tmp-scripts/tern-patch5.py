#!/usr/bin/env python3
"""tern 2026-09-21: _redact_text bytes fix (correct anchor)."""
P = "/home/toxic/sovereign/agents/oracle-market/bin/bidder.py"
src = open(P, encoding="utf-8").read()

old = '''    if not s:
        return s
    pats = ['''
new = '''    if not s:
        return s
    if isinstance(s, bytes):
        # 2026-09-21 (tern): TimeoutExpired.stdout/stderr are bytes;
        # decode before regex (was TypeError on tern-proof-005).
        s = s.decode("utf-8", errors="replace")
    pats = ['''
assert src.count(old) == 1, "anchor, got %d" % src.count(old)
src = src.replace(old, new)

with open(P, "w", encoding="utf-8") as f:
    f.write(src)
print("bytes fix OK")
