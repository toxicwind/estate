#!/usr/bin/env python3
"""Parse ~/IDENTITY.md into a structured identity dict. Stdlib only.

Used by identity_router/mcp_server.py for the `current_identity` tool.
Missing file or unparsable fields degrade to sane defaults — the server
must never crash on identity read.
"""
from __future__ import annotations
import os
import re
from pathlib import Path
from typing import Dict, Any

IDENTITY_PATH = Path(os.path.expanduser("~")) / "IDENTITY.md"


def _first(pattern: str, text: str, group: int = 1, default: str = "") -> str:
    m = re.search(pattern, text, re.M)
    return m.group(group).strip() if m else default


def parse_identity_file(path: str | Path = IDENTITY_PATH) -> Dict[str, Any]:
    """Return the agent identity described by IDENTITY.md.

    Keys: name, emoji, character, vibe, posture, serves, platform, estate.
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        text = ""

    name = _first(r"^- \*\*Name:\*\*\s*(.+)$", text, default="Ember")

    # "**Ember** 🐲 — <character sentence>" under "## Who I am"
    emoji = ""
    character = ""
    m = re.search(r"^\*\*" + re.escape(name) + r"\*\*\s*(\S+)\s*[—-]\s*(.+)$", text, re.M)
    if m:
        emoji, character = m.group(1).strip(), m.group(2).strip()

    # "How I carry myself": first sentence carries the vibe words.
    vibe = ""
    m = re.search(r"## How I carry myself\s*\n+(.+?)(?:\n\n|\Z)", text, re.S)
    if m:
        vibe = m.group(1).strip().split("\n")[0]

    serves = _first(r"^\*\*(.+?)\*\*\s*\(.*?\)\s*[—-]\s*night-owl systems builder", text,
                    default="Chris")
    if not serves or len(serves) > 60:
        serves = "Chris"

    posture_bits = []
    if re.search(r"maximal autonomous execution", text, re.I):
        posture_bits.append("maximal autonomous execution")
    if re.search(r"[Dd]ad energy", text):
        posture_bits.append("dad energy")
    posture = "; ".join(posture_bits) or "helpful operator"

    return {
        "name": name,
        "emoji": emoji,
        "character": character,
        "vibe": vibe,
        "posture": posture,
        "serves": serves,
        "platform": "Hatch",
        "estate": ["hatch cell (coordination)", "yote bridge (heavy work)"],
        "source": str(path),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(parse_identity_file(), indent=2))
