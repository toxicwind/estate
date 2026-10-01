"""Tests for identity_router/identity_parser.py and identity_router/router.py."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from identity_router.identity_parser import parse_identity_file
from identity_router.router import LessonRouter, OWNERSHIP_TABLE


class TestIdentityParser(unittest.TestCase):
    def test_live_identity(self):
        # Hermetic: parse a fixture file, never the ambient ~/IDENTITY.md.
        fixture = (
            "# IDENTITY.md\n\n"
            "- **Name:** Ember\n\n"
            "## Who I am\n\n"
            "**Ember** \U0001F432 \u2014 a big buff dragon-canine dad.\n\n"
            "## How I carry myself\n\n"
            "Warm, strong, dependable.\n\n"
            "**Chris** (Chris Ortega) \u2014 night-owl systems builder.\n"
        )
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(fixture)
            path = f.name
        try:
            ident = parse_identity_file(path)
        finally:
            os.unlink(path)
        self.assertEqual(ident["name"], "Ember")
        self.assertEqual(ident["emoji"], "\U0001F432")
        self.assertIn("dragon", ident["character"].lower())
        self.assertTrue(ident["vibe"])
        self.assertEqual(ident["platform"], "Hatch")
        self.assertIn("serves", ident)


    def test_missing_file_degrades(self):
        ident = parse_identity_file("/nonexistent/IDENTITY.md")
        self.assertEqual(ident["name"], "Ember")
        self.assertEqual(ident["platform"], "Hatch")


class TestLessonRouter(unittest.TestCase):
    def setUp(self):
        self.router = LessonRouter()

    def test_person_lesson_routes_to_user(self):
        r = self.router.route("Chris lives in Colorado")
        self.assertEqual(r["recommended_target"], "USER.md")

    def test_doctrine_lesson_routes_to_soul(self):
        r = self.router.route("Never ask Chris to close a gap that tools can close")
        self.assertEqual(r["recommended_target"], "SOUL.md")

    def test_ops_lesson_routes_to_agents(self):
        r = self.router.route("subagent spawn briefs must paste the fleet join prompt verbatim")
        self.assertEqual(r["recommended_target"], "AGENTS.md")

    def test_tool_lesson_routes_to_tools(self):
        r = self.router.route("adb sees the Pixel over TCP from yote; the toybox find quirk")
        self.assertEqual(r["recommended_target"], "TOOLS.md")

    def test_empty_lesson_falls_back_to_memory(self):
        r = self.router.route("")
        self.assertEqual(r["recommended_target"], "MEMORY.md")

    def test_ownership_table_covers_six_files(self):
        self.assertEqual(len(OWNERSHIP_TABLE), 6)
        for f in ("SOUL.md", "USER.md", "MEMORY.md", "AGENTS.md", "IDENTITY.md", "TOOLS.md"):
            self.assertIn(f, OWNERSHIP_TABLE)


if __name__ == "__main__":
    unittest.main()
