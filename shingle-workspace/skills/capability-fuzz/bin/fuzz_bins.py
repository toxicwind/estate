#!/usr/bin/env python3
"""Sweep every /opt/hatch/bin entry: --help exit code + first lines.

Writes JSONL to stdout: {name, help_exit, help_head, version_exit, notes}.
Fail-fast: 5s per probe. Part of capability-fuzz Step 1 (Discovery).
"""
import json
import os
import subprocess
import sys

BINDIR = "/opt/hatch/bin"
TIMEOUT = 5


def probe(path, args):
    try:
        p = subprocess.run(
            [path] + args, capture_output=True, text=True, timeout=TIMEOUT
        )
        out = (p.stdout or "") + (p.stderr or "")
        return p.returncode, out[:800].strip()
    except subprocess.TimeoutExpired:
        return "timeout", ""
    except Exception as e:  # noqa: BLE001 - record, don't crash the sweep
        return "error", str(e)[:200]


def main():
    names = sorted(
        n for n in os.listdir(BINDIR) if os.access(os.path.join(BINDIR, n), os.X_OK)
    )
    for name in names:
        path = os.path.join(BINDIR, name)
        help_exit, help_head = probe(path, ["--help"])
        notes = []
        if help_exit == "timeout":
            notes.append("help-hung")
        rec = {
            "name": name,
            "help_exit": help_exit,
            "help_head": help_head,
            "notes": notes,
        }
        sys.stdout.write(json.dumps(rec) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
