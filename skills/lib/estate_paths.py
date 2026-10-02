"""estate_paths — canonical path resolution for every skill on this box.

No skill hardcodes an estate path. They import this module and ask it.

Resolution order for each root:

  1. explicit environment override   (ESTATE_HOME, RANCH_HOME, ...)
  2. sibling-of-this-file discovery  (works inside ranch/, inside a clone)
  3. $HOME/<name>                    (the awrawr-pc default)

Every returned path is resolved, so the compat symlinks
(/home/toxic/estate -> estate, /home/toxic/projects -> estate/ranch)
never leak into a report or a comparison.

    from estate_paths import ESTATE, RANCH, SKILLS, VENDORED, PORTS_ENV
"""

from __future__ import annotations

import os
from pathlib import Path

__all__ = [
    "HOME",
    "ESTATE",
    "RANCH",
    "VENDORED",
    "VAR",
    "MANOR",
    "SKILLS",
    "PORTS_ENV",
    "KNOWLEDGEBASE",
    "TAU_DIR",
    "PORT_SSOT",
    "find_skills_root",
    "iter_skills",
    "resolve_root",
]

HOME = Path.home()

# Skills may live in ~/.tau/skills or ~/workspace/skills. Discover, don't assume.
_SELF = Path(__file__).resolve().parent
_CANDIDATE_SKILL_ROOTS = [
    _SELF.parent,                       # <skills>/lib/estate_paths.py -> <skills>
    _SELF.parent.parent,                # nested one level deeper
    HOME / ".tau" / "skills",
    HOME / "workspace" / "skills",
]


def find_skills_root(start: Path | None = None) -> Path:
    """Walk up from `start` until a directory containing skill:// content is found."""
    here = (start or _SELF).resolve()
    for candidate in here.parents:
        if (candidate / "lib" / "estate_paths.py").exists() or (
            (candidate / "pattern-forge").exists()
        ):
            return candidate
    for candidate in _CANDIDATE_SKILL_ROOTS:
        if candidate.is_dir():
            return candidate.resolve()
    raise FileNotFoundError("could not locate the skills root; set SKILLS_HOME")


def _resolve(env_var: str, *fallbacks: Path) -> Path:
    override = os.environ.get(env_var)
    if override:
        return Path(override).expanduser().resolve()
    for candidate in fallbacks:
        if candidate.exists():
            return candidate.resolve()
    # Nothing on disk: return the first fallback so error messages name a real path.
    return fallbacks[0].resolve() if fallbacks else Path(".").resolve()


SKILLS = find_skills_root()
ESTATE = _resolve("ESTATE_HOME", SKILLS.parent / "estate", HOME / "estate", HOME / "sovereign")
RANCH = _resolve("RANCH_HOME", ESTATE / "ranch", HOME / "ranch", HOME / "projects")
VENDORED = _resolve("VENDORED_HOME", ESTATE / "vendored")
VAR = ESTATE / "var"
MANOR = _resolve("MANOR_HOME", ESTATE / "manor")

PORTS_ENV = ESTATE / "config" / "ports.env"
KNOWLEDGEBASE = ESTATE / "docs" / "fleet-knowledgebase.md"
TAU_DIR = _resolve("TAU_HOME", RANCH / "tau")

# Historical name kept for import compatibility with existing skills.
PORT_SSOT = PORTS_ENV


def iter_skills():
    """Yield (name, path) for every installed skill."""
    if not SKILLS.is_dir():
        return
    for entry in sorted(SKILLS.iterdir()):
        if entry.is_dir() and (entry / "SKILL.md").exists():
            yield entry.name, entry