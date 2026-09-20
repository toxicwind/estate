#!/usr/bin/env python3
"""GitHub code search: AXS API/XHR patterns for ticket pricing workarounds."""
import json
import os
import sys

sys.path.insert(0, os.path.expanduser("~/workspace/skills/emergent-enrich/bin"))
from route import github_code_search

QUERIES = [
    "api.axs.com",
    "promogroup axs",
    "axs tickets api inventory",
]

out = []
for q in QUERIES:
    try:
        r = github_code_search(q, 10)
    except Exception as e:
        r = {"ok": False, "error": str(e)[:200]}
    out.append({"query": q, "result": r})

print(json.dumps(out, indent=1)[:12000])
