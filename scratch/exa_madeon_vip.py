#!/usr/bin/env python3
"""Deep Exa OSINT sweep: every reference to the Madeon 'Super Platinum
Soundcheck VIP Experience' for Mission Ballroom, Denver."""
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
UA = "shingle-exa-osint/1.0"
LEDGER = os.path.expanduser("~/.cache/shingle/exa_audit.jsonl")


def api(path, payload):
    t0 = time.perf_counter()
    req = urllib.request.Request(
        "https://api.exa.ai" + path,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
    )
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", UA)
    add_surrogate_to_request(req, "custom.exa", allowed_hosts=EXA_HOSTS)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(read_response_body(resp).decode("utf-8"))
    except Exception as e:
        exa_audit.log_call(path, payload.get("numResults"),
                           elapsed_ms=(time.perf_counter() - t0) * 1000,
                           ok=False, error=e, query=payload.get("query"))
        return {"ok": False, "error": str(e)}
    exa_audit.log_call(path, payload.get("numResults"),
                       results_returned=len(data.get("results", [])),
                       elapsed_ms=(time.perf_counter() - t0) * 1000,
                       ok=True, query=payload.get("query"),
                       cost_usd=(data.get("costDollars") or {}).get("total"))
    return {"ok": True, "data": data}


out = {"queries": [], "contents": None}

QUERIES = [
    "Super Platinum Soundcheck VIP Experience Madeon Mission Ballroom",
    "Madeon Victory Live VIP Mission Ballroom Denver tickets",
    "Madeon Mission Ballroom October 8 2026 VIP package on sale",
    "100x Hospitality Madeon Victory Live Super Platinum VIP",
]

for q in QUERIES:
    r = api("/search", {"query": q, "type": "auto", "numResults": 10,
                        "includeDomains": None})
    block = {"query": q, "ok": r["ok"]}
    if r["ok"]:
        block["results"] = [
            {"title": x.get("title"), "url": x.get("url"),
             "publishedDate": x.get("publishedDate"), "score": x.get("score")}
            for x in r["data"].get("results", [])
        ]
    else:
        block["error"] = r["error"]
    out["queries"].append(block)

# Deep read: fetch the 100x tour hub page as markdown
r = api("/contents", {"urls": ["https://madeon.100xhospitality.com/"],
                      "text": {"maxCharacters": 12000}})
if r["ok"]:
    res = r["data"].get("results", [])
    out["contents"] = [{"url": x.get("url"),
                        "text": (x.get("text") or "")[:8000]} for x in res]

print(json.dumps(out, indent=1))
