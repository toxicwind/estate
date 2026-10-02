#!/usr/bin/env python3
"""Check Madeon @ Mission Ballroom VIP package availability on AXS (stealth)."""
import json
import re
import sys
import time

sys.path.insert(0, "/home/hatch/workspace/skills/shared")
from stealth_browser import launch_stealth, humanize

URL = "https://www.axs.com/events/1433020/madeon-tickets"

result = {"url": URL, "ok": False, "vip": None, "notes": []}


def dump(page, tag):
    result["notes"].append(f"[{tag}] title={page.title()!r} url={page.url!r}")


with launch_stealth(headless=True) as page:
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        result["notes"].append(f"goto failed: {e}")
    page.wait_for_timeout(6000)
    humanize(page, scrolls=2)
    dump(page, "event-page")

    body = page.evaluate("() => document.body ? document.body.innerText.slice(0, 20000) : 'NO BODY'")
    result["event_text"] = body[:4000]

    # Find and click the VIP Packages section / link
    vip_locator = None
    for needle in ["VIP Packages", "VIP packages"]:
        loc = page.get_by_text(re.compile(needle, re.I), exact=False)
        try:
            if loc.count() > 0:
                vip_locator = loc.first
                result["notes"].append(f"found text match: {needle!r} count={loc.count()}")
                break
        except Exception as e:
            result["notes"].append(f"locator err: {e}")

    if vip_locator is None:
        result["notes"].append("no VIP Packages text found on event page")
    else:
        try:
            vip_locator.click(timeout=15000)
        except Exception as e:
            result["notes"].append(f"click failed: {e}")
        page.wait_for_timeout(7000)
        dump(page, "after-vip-click")
        vip_body = page.evaluate("() => document.body ? document.body.innerText.slice(0, 20000) : 'NO BODY'")
        result["vip_text"] = vip_body[:6000]

        # Look for availability signals
        text = vip_body.lower()
        signals = {}
        for pat in ["sold out", "not available", "on sale", "from $", "available", "vip", "package"]:
            signals[pat] = len(re.findall(re.escape(pat), text))
        result["signals"] = signals

        # Grab any price-ish strings near VIP mentions
        prices = re.findall(r"\$\s?\d[\d,]*(?:\.\d{2})?", vip_body)
        result["prices_seen"] = sorted(set(prices), key=lambda s: float(s.replace("$", "").replace(",", "").replace(" ", "")))[:20]

    result["ok"] = True

print(json.dumps(result, indent=1))
