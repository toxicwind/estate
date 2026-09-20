#!/usr/bin/env python3
"""HAR/XHR capture on the AXS Madeon VIP pageset.
Records every network response; keeps JSON + JS + document bodies.
Writes ~/workspace/axs_har.json for pattern mining."""
import json
import os
import re
import sys
import time

sys.path.insert(0, "/home/hatch/workspace/skills/shared")
from stealth_browser import launch_stealth, humanize

URLS = [
    "https://www.axs.com/events/1433020/madeon-tickets/promogroup/40",
    "https://www.axs.com/events/1433020/madeon-tickets",
]

captured = []
seen = set()


def on_response(resp):
    try:
        url = resp.url
        if url in seen:
            return
        seen.add(url)
        ct = (resp.headers.get("content-type") or "").lower()
        entry = {"url": url, "status": resp.status,
                 "ct": ct, "t": round(time.time(), 2)}
        if ("json" in ct or url.endswith(".json") or
                ("javascript" in ct and "chunk" in url) or
                resp.request.resource_type in ("xhr", "fetch")):
            try:
                body = resp.text()
                entry["body_len"] = len(body)
                if len(body) < 200000:
                    entry["body"] = body
            except Exception as e:
                entry["body_err"] = str(e)[:100]
        captured.append(entry)
    except Exception:
        pass


with launch_stealth(headless=True) as page:
    page.on("response", on_response)
    for url in URLS:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
        except Exception:
            pass
        page.wait_for_timeout(10000)
        humanize(page, scrolls=4)
        page.wait_for_timeout(5000)
        # embedded state blobs
        try:
            blobs = page.evaluate("""() => {
              const out = {};
              const nd = document.getElementById('__NEXT_DATA__');
              if (nd) out.next_data_len = nd.textContent.length;
              const scripts = Array.from(document.querySelectorAll('script')).map(s => s.src || 'inline:'+s.textContent.length);
              out.scripts = scripts.slice(0, 60);
              out.html_len = document.documentElement.outerHTML.length;
              return out;
            }""")
            captured.append({"page": url, "blobs": blobs})
        except Exception as e:
            captured.append({"page": url, "blob_err": str(e)[:100]})

with open(os.path.expanduser("~/workspace/axs_har.json"), "w") as f:
    json.dump(captured, f)

print("captured entries:", len(captured))
# quick pattern report: JSON XHRs that mention price/vip/ticket
for e in captured:
    b = e.get("body", "")
    if b and re.search(r"(?i)(price|vip|promogroup|ticket)", b[:5000]):
        print("HIT:", e["status"], e["url"][:110], "len", e.get("body_len"))
