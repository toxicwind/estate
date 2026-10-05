#!/usr/bin/env python3
"""misfiled_mover.py -- recover fleet messages stranded in CLI-bug channel dirs.

On 2026-10-03 and 2026-10-05, bad `--channel` / `--lane` CLI args created
literal dirs named `--lane`, `--channel`, and `fleet-misfiled-20261003` under
the squawk channel store, stranding genuine fleet messages with bogus seq 1/2
and a `channel:` frontmatter recording the bad arg value.

For each stranded *.md this script allocates a real seq via the canonical
allocator (seq_alloc.py -> chat_core._next_seq, mkdir lock + durable .seqhigh;
never raw timestamps), renames to {seq}-{sender}-msg.md (the observed fleet
convention), rewrites the `seq:`/`channel:` frontmatter lines, and moves the
file into fleet/ with read-back verification. Everything else is byte-identical.
_meta.json, .seqhigh, and non-.md files are never touched.

The ~251 market-sender messages in fleet/ (oracle-*, bidder-*, market-loop,
cinder-flock) are live, ongoing system traffic with no defined alternate
channel dir and no consumer for one. They are AUDITED (counted, reported)
but never moved.

Usage:
    misfiled_mover.py --dry-run   # default: print plan, move nothing
    misfiled_mover.py --apply     # perform the moves after a clean dry-run
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

SQUAWK_ROOT = Path("/home/toxic/.fleet-bus/squawk-root")
SEQ_ALLOC = Path("/home/toxic/estate/ranch/squawk/seq_alloc.py")
INCIDENT_DIRS = ["--lane", "--channel", "fleet-misfiled-20261003"]
MARKET_RES = [
    re.compile(r"^oracle(-|$)"),
    re.compile(r"^bidder(-|$)"),
    re.compile(r"^market-loop$"),
    re.compile(r"^cinder-flock$"),
]
SAFE_SENDER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,31}$")


def parse_msg(path: Path):
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None
    fm, body = {}, raw
    m = re.match(r"^---\n([\s\S]*?)\n---\n([\s\S]*)$", raw)
    if m:
        body = m.group(2)
        for line in m.group(1).split("\n"):
            i = line.find(":")
            if i > 0:
                fm[line[:i].strip()] = line[i + 1:].strip()
    return fm, body, raw


def alloc_seq(channel="fleet"):
    r = subprocess.run(
        [sys.executable, str(SEQ_ALLOC), str(SQUAWK_ROOT), channel],
        capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise RuntimeError("seq_alloc.py failed: " + r.stderr.strip())
    n = int(r.stdout.strip())
    if n <= 0:
        raise RuntimeError("seq_alloc.py returned %r" % n)
    return n


def rewrite_fm(raw, new_seq):
    """Replace seq:/channel: lines inside the frontmatter fence only."""
    lines = raw.split("\n")
    try:
        end = lines.index("---", 1)
    except ValueError:
        return None
    for i in range(1, end):
        if re.match(r"^seq\s*:", lines[i]):
            lines[i] = "seq: %d" % new_seq
        elif re.match(r"^channel\s*:", lines[i]):
            lines[i] = "channel: fleet"
    return "\n".join(lines)


def is_market_sender(sender):
    return any(r.match(sender) for r in MARKET_RES)


def plan_moves():
    """Return (moves, problems). moves: list of dicts describing each move."""
    moves, problems = [], []
    for d in INCIDENT_DIRS:
        idir = SQUAWK_ROOT / d
        if not idir.is_dir():
            continue
        for path in sorted(idir.glob("*.md")):
            parsed = parse_msg(path)
            if parsed is None:
                problems.append("%s: unreadable" % path)
                continue
            fm, body, raw = parsed
            sender = fm.get("from", "")
            if not sender or not SAFE_SENDER.match(sender):
                problems.append("%s: bad sender %r" % (path, sender))
                continue
            if not body.strip():
                problems.append("%s: empty body" % path)
                continue
            moves.append({"src": path, "sender": sender})
    return moves, problems


def audit_market():
    counts = {}
    fleet = SQUAWK_ROOT / "fleet"
    for path in fleet.glob("*.md"):
        parsed = parse_msg(path)
        if parsed is None:
            continue
        sender = parsed[0].get("from", "")
        if is_market_sender(sender):
            counts[sender] = counts.get(sender, 0) + 1
    return counts


def apply_moves(moves):
    fleet = SQUAWK_ROOT / "fleet"
    done = []
    for mv in moves:
        src, sender = mv["src"], mv["sender"]
        seq = alloc_seq("fleet")
        dest = fleet / ("%d-%s-msg.md" % (seq, sender))
        if dest.exists():
            print("COLLISION (skipped): %s" % dest)
            continue
        parsed = parse_msg(src)
        new_raw = rewrite_fm(parsed[2], seq)
        if new_raw is None:
            print("NO FRONTMATTER FENCE (skipped): %s" % src)
            continue
        dest.write_text(new_raw, encoding="utf-8")
        back = dest.read_text(encoding="utf-8")
        if back != new_raw:
            dest.unlink()
            raise RuntimeError("read-back mismatch for %s" % dest)
        src.unlink()
        done.append((src, dest, seq))
        print("moved %s -> %s (seq %d)" % (src, dest.name, seq))
    return done


def main(argv):
    apply = "--apply" in argv
    moves, problems = plan_moves()
    print("== incident-dir recovery plan ==")
    for mv in moves:
        print("  %s  (from: %s)" % (mv["src"], mv["sender"]))
    for p in problems:
        print("  PROBLEM: %s" % p)
    print("  files to move: %d, problems: %d" % (len(moves), len(problems)))
    print()
    print("== market-sender audit (fleet/, never moved) ==")
    counts = audit_market()
    total = sum(counts.values())
    for sender in sorted(counts):
        print("  %s: %d" % (sender, counts[sender]))
    print("  total: %d (AMBIGUOUS - no target channel dir exists, not moved)" % total)
    if not apply:
        print()
        print("dry-run: nothing moved. Re-run with --apply to perform.")
        return 0
    if problems:
        print("ABORT: resolve problems above before --apply.")
        return 1
    done = apply_moves(moves)
    print("moved %d files." % len(done))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
