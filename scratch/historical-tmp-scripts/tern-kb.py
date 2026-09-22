#!/usr/bin/env python3
"""tern 2026-09-21: mark KB row DONE."""
import re
P = "/home/toxic/sovereign/docs/fleet-knowledgebase.md"
src = open(P, encoding="utf-8").read()
lines = src.split("\n")
for i, l in enumerate(lines):
    if "| tern" in l.lower() and "RUNNING" in l:
        print("ROW %d: %s" % (i, l[:110]))
        lines[i] = l.replace("RUNNING", "DONE").replace(
            "fb730dd111b08d093ed246c88b904f7535d1008e",
            "fb730dd111b08d093ed246c88b904f7535d1008e, 8024654a27b900bbf58b332e76d45421b4da7b84")
        print("NEW: %s" % lines[i][:130])
        break
open(P, "w", encoding="utf-8").write("\n".join(lines))
print("KB updated")
