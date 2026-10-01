#!/usr/bin/env python3
"""Lesson router: score a durable lesson against the six standing files
and recommend where it belongs. Stdlib only.

Used by identity_router/mcp_server.py for the `route_lesson` tool.
Keyword scoring with phrase weights; ties break toward the more
specific file (order below). Never raises on odd input.
"""
from __future__ import annotations
from typing import Dict, Any, List, Tuple

# Standing file -> what belongs there. mcp_server.py serves this as JSON
# for the `standing_files` tool.
OWNERSHIP_TABLE: Dict[str, str] = {
    "SOUL.md": (
        "Persona and doctrine: how Ember knows things, how Ember works, "
        "how Ember leads the pack, how Ember talks, how Ember takes "
        "correction, and hard boundaries. Changes only on Chris's direct word."
    ),
    "USER.md": (
        "Who Chris is: name, what to call him, timezone, and durable context "
        "about the person — habits, register, how he communicates."
    ),
    "MEMORY.md": (
        "Curated long-term memory: durable facts, preferences, commitments, "
        "decisions. Day-to-day detail lives in ~/memory/ daily notes."
    ),
    "AGENTS.md": (
        "Workspace operating manual: how work gets done here — execution "
        "doctrine, delegation and pack rules, fleet knowledge, box/bridge "
        "operations, investigation method. Chris's word overrides it."
    ),
    "IDENTITY.md": (
        "Who the main agent is: name, character, vibe, signature emoji, "
        "estate, scars. Changes only on Chris's direct word."
    ),
    "TOOLS.md": (
        "Local tool notes: device nicknames, host aliases, environment "
        "quirks, per-box binary locations and gotchas."
    ),
}

# Standing file -> [(phrase, weight)]. Matched case-insensitively against
# the lesson text; weights reward multi-word doctrine phrases over bare words.
_SIGNALS: Dict[str, List[Tuple[str, int]]] = {
    "USER.md": [
        ("chris", 3), ("lives in", 3), ("my person", 3), ("call them", 3),
        ("call him", 3), ("timezone", 2), ("colorado", 2), ("denver", 2),
        ("night owl", 2), ("night-owl", 2), ("android app", 2),
        ("what to call", 2),
    ],
    "SOUL.md": [
        ("never ask", 4), ("ask chris", 3), ("hesitance", 3),
        ("doctrine", 3), ("unreliable narrator", 3), ("persona", 2),
        ("vibe", 2), ("ember", 2), ("dad energy", 2),
        ("autonomous execution", 2), ("obtuse", 2), ("boundaries", 2),
        ("how i talk", 2), ("how i work", 2),
    ],
    "AGENTS.md": [
        ("subagent", 3), ("spawn brief", 3), ("fleet", 2), ("squawk", 2),
        ("yote-conn", 2), ("bridge", 2), ("swarm", 2), ("orchestrat", 2),
        ("pack", 2), ("coordinator", 2), ("standing-edit", 3),
        ("classifier", 2), ("durability", 2), ("unshare", 2),
    ],
    "TOOLS.md": [
        ("adb", 3), ("httpx", 3), ("pdtm", 3), ("binary", 2), ("atool", 2),
        ("command", 1), ("tool", 1), ("quirk", 2), ("tmpfs", 2),
        ("egress proxy", 2),
    ],
    "IDENTITY.md": [
        ("my name", 3), ("who i am", 3), ("identity", 2), ("i am ember", 3),
        ("character", 2), ("fursona", 2), ("emoji", 2),
    ],
    "MEMORY.md": [
        ("preference", 2), ("commitment", 2), ("decision", 1), ("fact", 1),
        ("remember", 1),
    ],
}

# Tie-break order: most specific file first.
_PRIORITY = ["USER.md", "IDENTITY.md", "SOUL.md", "AGENTS.md", "TOOLS.md", "MEMORY.md"]


class LessonRouter:
    """Score a lesson against the standing files."""

    def __init__(self, signals: Dict[str, List[Tuple[str, int]]] | None = None):
        self.signals = signals or _SIGNALS

    def score(self, lesson: str) -> Dict[str, int]:
        text = (lesson or "").lower()
        return {
            target: sum(w for phrase, w in phrases if phrase in text)
            for target, phrases in self.signals.items()
        }

    def route(self, lesson: str) -> Dict[str, Any]:
        scores = self.score(lesson)
        best = max(_PRIORITY, key=lambda t: (scores[t], -_PRIORITY.index(t)))
        if scores[best] == 0:
            best = "MEMORY.md"  # durable-fact fallback
        return {
            "recommended_target": best,
            "scores": scores,
            "lesson": lesson,
            "ownership": OWNERSHIP_TABLE[best],
        }


if __name__ == "__main__":
    import json, sys
    lesson = " ".join(sys.argv[1:]) or "Never ask Chris to close a gap that tools can close"
    print(json.dumps(LessonRouter().route(lesson), indent=2))
