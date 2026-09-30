#!/usr/bin/env python3
"""Fix gemini-mcp stale 8378 default -> 25202 (code + docstring)."""
p = "/home/toxic/gemini-mcp/server.py"
t = open(p).read()
a = t.count('"8378"')
b = t.count("(8378)")
assert a == 1 and b == 1, f"unexpected counts: {a}, {b}"
t = t.replace('"8378"', '"25202"').replace("(8378)", "(25202)")
open(p, "w").write(t)
print("gemini-mcp default 8378 -> 25202 (code + docstring)")
