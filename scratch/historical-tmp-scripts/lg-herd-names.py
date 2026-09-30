#!/usr/bin/env python3
"""Inspect herd.yaml peer + route naming (read-only)."""
import re
import sys

txt = open("/tmp/lg-wt/config/herd.yaml", encoding="utf-8").read()
lines = txt.split("\n")

# top-level keys
tops = [l for l in lines if re.match(r"^[a-z_]+:", l)]
print("TOP-LEVEL:", [l.rstrip(":") for l in tops])

# peers: keys at 2-space indent under peers:
in_peers = False
peers = []
for l in lines:
    if l == "peers:":
        in_peers = True
        continue
    if in_peers:
        if re.match(r"^[a-z_]+:", l):
            break
        m = re.match(r"^  ([a-zA-Z0-9_-]+):$", l)
        if m:
            peers.append(m.group(1))
print("PEERS (%d):" % len(peers), peers)

# modelMap route names
in_mm = False
routes = []
for l in lines:
    if re.match(r"^modelMap:", l):
        in_mm = True
        continue
    if in_mm:
        if re.match(r"^[a-z_]+:", l):
            break
        m = re.match(r"^  ([a-zA-Z0-9_.-]+):$", l)
        if m:
            routes.append(m.group(1))
print("ROUTES (%d):" % len(routes))
odd = [r for r in routes if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]*", r)]
print("NON-KEBAB/SNAKE ROUTES:", odd[:20])
