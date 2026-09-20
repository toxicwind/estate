#!/usr/bin/env python3
"""Exa price leg: find literal dollar pricing for the Madeon VIP packages."""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request, read_response_body
sys.path.insert(0, os.path.expanduser("~/workspace/skills/emergent-enrich/bin"))
import exa_audit

EXA_HOSTS = ["api.exa.ai"]


def search(q, n=10):
    t0 = time.perf_counter()
    req = urllib.request.Request(
        "https://api.exa.ai/search",
        data=json.dumps({"query": q, "type": "auto", "numResults": n,
                         "text": {"maxCharacters": 3000}}).encode("utf-8"),
        method="POST")
    req.add_header("Content-Type", "application/json")
    add_surrogate_to_request(req, "custom.exa", allowed_hosts=EXA_HOSTS)
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(read_response_body(resp).decode("utf-8"))
    exa_audit.log_call("/search", n, results_returned=len(data.get("results", [])),
                       elapsed_ms=(time.perf_counter() - t0) * 1000,
                       ok=True, query=q,
                       cost_usd=(data.get("costDollars") or {}).get("total"))
    return data.get("results", [])


QUERIES = [
    "Madeon Super Platinum Soundcheck VIP Experience price dollars",
    "Madeon Victory VIP Experience package price cost",
    "Madeon VIP ticket price AXS Mission Ballroom",
]

out = []
for q in QUERIES:
    rows = []
    for r in search(q):
        rows.append({"title": r.get("title"), "url": r.get("url"),
                     "text": (r.get("text") or "")[:2500]})
    out.append({"query": q, "results": rows})

print(json.dumps(out, indent=1))
