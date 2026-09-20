#!/usr/bin/env python3
"""Exa contents fetch: pull markdown of TM explore + event pages, grep prices."""
import json
import os
import re
import sys
import time
import urllib.request

sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request, read_response_body
sys.path.insert(0, os.path.expanduser("~/workspace/skills/emergent-enrich/bin"))
import exa_audit

EXA_HOSTS = ["api.exa.ai"]
URLS = [
    "https://www.ticketmaster.com/explore/madeon-vip",
    "https://www.ticketmaster.com/madeon-presents-victory-live-san-diego-california-10-23-2026/event/0A0064A40B897F48",
    "https://www.ticketmaster.com/madeon-presents-victory-live-washington-district-of-columbia-11-07-2026/event/150064A7A35BA151",
    "https://www.koobit.com/madeon-e188415",
    "https://www.prekindle.com/event/32997-madeon-presents-victory-live-san-luis-obispo",
    "https://www.ticketweb.com/event/madeon-presents-victory-live-with-cargo-concert-hall-tickets/14900553",
]


def contents(urls):
    t0 = time.perf_counter()
    req = urllib.request.Request(
        "https://api.exa.ai/contents",
        data=json.dumps({"urls": urls, "text": {"maxCharacters": 15000}}).encode("utf-8"),
        method="POST")
    req.add_header("Content-Type", "application/json")
    add_surrogate_to_request(req, "custom.exa", allowed_hosts=EXA_HOSTS)
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(read_response_body(resp).decode("utf-8"))
    exa_audit.log_call("/contents", len(urls),
                       results_returned=len(data.get("results", [])),
                       elapsed_ms=(time.perf_counter() - t0) * 1000,
                       ok=True, query=";".join(urls)[:80],
                       cost_usd=(data.get("costDollars") or {}).get("total"))
    return data.get("results", [])


for r in contents(URLS):
    text = r.get("text") or ""
    prices = sorted(set(re.findall(r"\$\s?\d[\d,]*(?:\.\d{2})?", text)),
                    key=lambda s: float(s.replace("$", "").replace(",", "").strip()))[:25]
    print("=" * 70)
    print(r.get("url"))
    print("prices:", prices)
    # VIP-adjacent lines
    for m in re.finditer(r"(?i)(super platinum|victory vip|vip package).{0,120}", text):
        print("  VIP>", m.group(0).replace("\n", " ")[:160])
