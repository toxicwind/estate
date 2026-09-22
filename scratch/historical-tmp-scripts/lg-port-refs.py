#!/usr/bin/env python3
"""Find all references to specific port vars (read-only)."""
import os
import re
import sys

root = "/tmp/lg-wt"
targets = sys.argv[1:]
rx = re.compile(r"\$\{(" + "|".join(targets) + r")\}"
                r"|\$(" + "|".join(targets) + r")\b"
                r"|require_(?:port|env)\s+(" + "|".join(targets) + r")"
                r"|env\s*=\s*\{[^}]*\b(" + "|".join(targets) + r")\b")
for dirpath, dirnames, files in os.walk(root):
    if ".git" in dirnames:
        dirnames.remove(".git")
    for f in files:
        if not f.endswith((".sh", ".toml", ".yaml", ".yml", ".py", ".env")):
            continue
        p = os.path.join(dirpath, f)
        try:
            text = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for i, line in enumerate(text.split("\n"), 1):
            m = rx.search(line)
            if m:
                v = next(g for g in m.groups() if g)
                print("%s:%d: %s -> %s" % (
                    os.path.relpath(p, root), i, v, line.strip()[:100]))
