#!/usr/bin/env python3
"""Persistent Playwright MITM proxy on :80/:443 via CDP interception."""
import asyncio, json, os, sys
from pathlib import Path

MITM_LOG = "/mnt/agents/mitm-proxy/traffic.jsonl"

def log_entry(entry):
    with open(MITM_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")

async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            "/mnt/agents/mitm-proxy/chromium-data",
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--remote-debugging-port=9222",
                "--proxy-server=direct://",
            ],
            ignore_https_errors=True,
        )
        page = await browser.new_page()
        
        async def handle_route(route, request):
            entry = {
                "ts": asyncio.get_event_loop().time(),
                "method": request.method,
                "url": request.url,
                "headers": dict(request.headers),
            }
            log_entry(entry)
            await route.continue_()
        
        await page.route("**/*", handle_route)
        
        while True:
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
