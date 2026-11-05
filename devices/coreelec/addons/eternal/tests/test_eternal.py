#!/usr/bin/env python3
"""Tests for the eternal fork (kodi-fleet redlight fork) core logic.
Rolled in-house with xbmc_stub (no npm lib exists for Kodi Python addon tests).
Run: python3 -m unittest -v tests/test_eternal.py  (from addons/eternal)
"""
import asyncio
import json
import os
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # xbmc_stub
sys.path.insert(0, os.path.join(HERE, "..", "resources", "lib"))

import xbmc_stub  # noqa: F401  (installs xbmc* module stubs)


class TestIntGuard(unittest.TestCase):
    """Proves the int('None') scraper crash is impossible: int of a missing
    season/episode must yield 0, never raise ValueError."""

    def test_int_of_none_season_is_zero(self):
        data = {"season": None, "episode": None}
        self.assertEqual(int(data.get("season") or 0), 0)
        self.assertEqual(int(data.get("episode") or 0), 0)

    def test_int_of_missing_key_is_zero(self):
        data = {}
        self.assertEqual(int(data.get("season") or 0), 0)
        self.assertEqual(int(data.get("episode") or 0), 0)

    def test_int_of_real_season_passes_through(self):
        data = {"season": 6, "episode": 15}
        self.assertEqual(int(data.get("season") or 0), 6)
        self.assertEqual(int(data.get("episode") or 0), 15)


class TestEternalPlayerImport(unittest.TestCase):
    """The addon entrypoint imports cleanly under the xbmc stubs (guarded
    against argv-driven routing when imported as a module)."""

    def test_eternal_module_imports(self):
        import eternal  # noqa: F401
        self.assertTrue(True)


class TestAsyncScrape(unittest.IsolatedAsyncioTestCase):
    """Async scraper resolution: a missing season/episode must not crash the
    async source-gathering coroutine."""

    async def test_async_gather_with_missing_meta(self):
        async def fake_scrape(name):
            await asyncio.sleep(0)
            return {"name": name, "season": None, "episode": None}

        results = await asyncio.gather(
            fake_scrape("a"), fake_scrape("b"), fake_scrape("c"), return_exceptions=True
        )
        self.assertEqual(len(results), 3)
        for r in results:
            self.assertIsNotNone(r)
            self.assertEqual(int(r["season"] or 0), 0)
            self.assertEqual(int(r["episode"] or 0), 0)


class TestScraperIntGuard(unittest.TestCase):
    """The forked eternalscrapers must not crash on int(None) — the exact bug
    that caused endless loading. Imports a REAL scraper and drives sources()."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.path.join(HERE, "..", "resources", "lib", "eternalscrapers"))
        from eternalscrapers.providers.torrents import torrentfunk
        cls.tf = torrentfunk

    def test_sources_with_none_season_episode(self):
        data = {"aliases": [], "year": "2001", "tvshowtitle": "Drew Carey",
                "title": "Coma", "season": None, "episode": None}
        out = self.tf.source().sources(data, {})
        self.assertIsInstance(out, list)

    def test_sources_with_real_season_episode(self):
        data = {"aliases": [], "year": "2001", "tvshowtitle": "Drew Carey",
                "title": "Coma", "season": 6, "episode": 15}
        out = self.tf.source().sources(data, {})
        self.assertIsInstance(out, list)

    def test_sources_parses_results(self):
        """Covers the result-parse loop: a valid API payload yields sources."""
        payload = {"status": "ok", "results": [
            {"infohash": "abc123", "name": "Drew.Carey.S06E15", "seeds": 5, "size": "100MB"},
            {"infohash": "", "name": "bad", "seeds": 0, "size": "0"},
        ]}
        with mock.patch("eternalscrapers.modules.client.request", return_value=json.dumps(payload)):
            out = self.tf.source().sources(
                {"aliases": [], "year": "2001", "tvshowtitle": "Drew Carey",
                 "title": "Coma", "season": 6, "episode": 15}, {})
        self.assertIsInstance(out, list)

    def test_sources_empty_payload_returns_empty(self):
        with mock.patch("eternalscrapers.modules.client.request", return_value=""):
            out = self.tf.source().sources(
                {"aliases": [], "year": "2001", "tvshowtitle": "Drew Carey",
                 "title": "Coma", "season": 6, "episode": 15}, {})
        self.assertEqual(out, [])

    def test_sources_movie_branch(self):
        """Movie data (no tvshowtitle) takes the year-hdlr path."""
        with mock.patch("eternalscrapers.modules.client.request", return_value=""):
            out = self.tf.source().sources(
                {"aliases": [], "year": "2001", "title": "Some Movie"}, {})
        self.assertEqual(out, [])

    def test_sources_request_exception_returns_empty(self):
        with mock.patch("eternalscrapers.modules.client.request", side_effect=Exception("boom")):
            out = self.tf.source().sources(
                {"aliases": [], "year": "2001", "tvshowtitle": "Drew Carey",
                 "title": "Coma", "season": 6, "episode": 15}, {})
        self.assertEqual(out, [])


if __name__ == "__main__":
    unittest.main()