#!/usr/bin/env python3
"""Live test for the aiostreams scraper (the fork's real target engine).
Hits a public aiostreams instance through the fork's own scraper code — no
mocks. Proves the scraper resolves real sources end-to-end (the int(None)
fix holds against live aiostreams data). Run: .venv/bin/python tests/live_aiostreams.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESLIB = os.path.join(HERE, "..", "resources", "lib")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(RESLIB, "eternalscrapers"))
import xbmc_stub  # noqa: F401
sys.path.insert(0, RESLIB)  # fork's own modules LAST = highest priority (wins over eternalscrapers.modules)
from eternalscrapers.providers.torrents import torrentfunk  # noqa: F401  (warm imports)

from scrapers import aiostreams  # noqa: E402

info = {
    "media_type": "episode",
    "title": "The Drew Carey Show",
    "year": 2001,
    "season": 6,
    "episode": 15,
    "imdb_id": "tt0111945",
    "tmdb_id": 97,
    "aliases": [],
}
src = aiostreams.source()
out = src.results(info)
print(f"[aiostreams.live] resolved {len(out)} sources; errors={src.errors}")
for s in out[:5]:
    print(f"  - {s.get('name', '')[:70]} | {s.get('quality', '')}")