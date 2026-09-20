#!/usr/bin/env python3
"""Deep price extraction: Madeon Mission Ballroom VIP packages on AXS.
Hits the direct promogroup/40 VIP pages for both event IDs found via Exa,
and the 100x Buy Now path, to pull literal package names + prices."""
import json
import re
import sys

sys.path.insert(0, "/home/hatch/workspace/skills/shared")
from stealth_browser import launch_stealth, humanize

PAGES = [
    ("vip-1433020", "https://www.axs.com/events/1433020/madeon-tickets/promogroup/40"),
    ("vip-1438072", "https://www.axs.com/events/1438072/madeon-tickets/promogroup/40"),
]

out = {"pages": []}

with launch_stealth(headless=True) as page:
    for tag, url in PAGES:
        rec = {"tag": tag, "url": url}
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            rec["goto_error"] = str(e)[:200]
        page.wait_for_timeout(8000)
        humanize(page, scrolls=3)
        rec["title"] = page.title()
        rec["final_url"] = page.url
        try:
            body = page.evaluate(
                "() => document.body ? document.body.innerText.slice(0, 25000) : 'NO BODY'")
        except Exception as e:
            body = "ERR " + str(e)[:200]
        rec["text"] = body[:6000]
        # price-like strings
        prices = re.findall(r"\$\s?\d[\d,]*(?:\.\d{2})?", body)
        def key(s):
            return float(s.replace("$", "").replace(",", "").strip())
        rec["prices"] = sorted(set(prices), key=key)[:30]
        # package-ish headings near price mentions
        rec["has_super_platinum"] = "super platinum" in body.lower()
        rec["has_victory"] = "victory vip" in body.lower()
        out["pages"].append(rec)

    # 100x tour hub: where does Denver's Buy Now go?
    try:
        page.goto("https://madeon.100xhospitality.com/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(6000)
        links = page.evaluate("""() => Array.from(document.querySelectorAll('a'))
          .map(a => ({text: (a.innerText||'').trim().slice(0,120), href: a.href}))
          .filter(a => /buy|ticket|denver|mission/i.test(a.text + ' ' + a.href))
          .slice(0, 40)""")
        out["hundredx_links"] = links
    except Exception as e:
        out["hundredx_error"] = str(e)[:200]

print(json.dumps(out, indent=1))
