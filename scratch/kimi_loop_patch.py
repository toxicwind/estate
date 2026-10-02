#!/usr/bin/env python3
"""Add canonical secrets sourcing to kimi-auto loop.sh (worktree)."""
import sys

PATH = "/home/toxic/wt-kimi-routing-ka/loop.sh"

OLD = """set -u
INTERVAL="${KIMI_AUTO_INTERVAL:-900}"
"""

NEW = """set -u
# Canonical secrets for presence detection (names only; values never handled).
# Mirrors the herd.sh pattern: source, never copy.
if [ -f /home/toxic/.secrets ]; then
  set +u
  . /home/toxic/.secrets
  set -u
fi
INTERVAL="${KIMI_AUTO_INTERVAL:-900}"
"""

with open(PATH, encoding="utf-8") as fh:
    text = fh.read()

if ". /home/toxic/.secrets" in text:
    print("already present; no change")
    sys.exit(0)

if OLD not in text:
    print("ANCHOR NOT FOUND", file=sys.stderr)
    sys.exit(1)

text = text.replace(OLD, NEW, 1)

with open(PATH, "w", encoding="utf-8") as fh:
    fh.write(text)

print("loop.sh updated")
