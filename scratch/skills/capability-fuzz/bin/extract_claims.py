#!/usr/bin/env python3
"""Extract unreliable-narrator candidate claims from ~/docs/*.md.

Pulls sentences containing can't/cannot/unable/never/no-agent-access style
phrases. Each becomes a fuzz case for the claim matrix (Step 2).
Writes JSONL to stdout: {file, line, claim}.
"""
import json
import os
import re
import sys

DOCDIR = os.path.expanduser("~/docs")
PAT = re.compile(
    r"\b(can't|cannot|can not|unable to|never |no way to|not (?:able|permitted|allowed)|"
    r"does not (?:have|support|allow|permit)|is not (?:able|permitted|allowed|possible)|"
    r"without (?:the user|approval)|only the user can|the agent (?:can ?not|cannot))",
    re.IGNORECASE,
)


def main():
    for fname in sorted(os.listdir(DOCDIR)):
        if not fname.endswith(".md"):
            continue
        path = os.path.join(DOCDIR, fname)
        with open(path, encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if len(line) < 20:
                    continue
                if PAT.search(line):
                    sys.stdout.write(
                        json.dumps({"file": fname, "line": i, "claim": line[:500]})
                        + "\n"
                    )


if __name__ == "__main__":
    main()
