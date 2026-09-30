#!/usr/bin/env python3
"""judge-evidence-vacuum.py -- logrotate-style vacuum for the P4 judge
failure-evidence JSONL log. (P4b, Nightjar cycle-5.)

Caps the append-only log at KEEP_LINES lines and KEEP_DAYS of age
(whichever keeps fewer), via an atomic copy-and-swap:

  1. stat the source (size S0)
  2. read lines, select survivors (ts >= cutoff, then tail KEEP_LINES)
  3. write survivors to a temp file on the SAME filesystem, fsync
  4. re-stat the source: if a writer appended while we worked (size != S0),
     re-read the new tail, append it to the temp file, and re-check
     (bounded retries)
  5. os.replace(temp, source) -- atomic directory-entry swap

The writer (oracle_ask._emit_failure_evidence) appends with open(path, "a")
and closes per emit -- it holds no lock and never re-reads the file, so an
atomic replace is safe: the only hazard is an append racing the swap, which
step 4 closes. Permissions are preserved from the source file.

Writes nothing else. Pure stdlib.

Usage:
  judge-evidence-vacuum.py [--path LOG] [--keep-lines N] [--keep-days D]
                           [--dry-run]

  --dry-run   print what would be dropped, change nothing.

Scheduling (PROPOSAL -- not installed by this script): run daily from
pitchfork cron (or a goal-owned cron) at a low-traffic hour, e.g.
  python3 /home/toxic/sovereign/hatch/agents/ember/coord/tools/judge-evidence-vacuum.py
      --keep-lines 50000 --keep-days 30 >> work/judge-evidence-vacuum.log 2>&1
Alert if the run log shows repeated race retries -- that signals write
volume the caps cannot bound.
"""
import argparse
import json
import os
import sys
import tempfile
import time
from datetime import datetime, timezone

DEFAULT_PATH = "/home/toxic/sovereign/agents/oracle-market/work/judge-failure-evidence.jsonl"
MAX_RACE_RETRIES = 5


def parse_ts(value):
    if not value:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text).timestamp()
    except ValueError:
        return None


def read_tail_new_lines(path, offset):
    """Lines appended to path after byte offset. Whole-line only."""
    with open(path, "r", encoding="utf-8") as f:
        f.seek(offset)
        chunk = f.read()
    if not chunk:
        return []
    lines = chunk.split("\n")
    # a trailing partial line (writer mid-emit) is left for the next read
    if lines and lines[-1] != "":
        lines = lines[:-1]
    return [l for l in lines if l]


def vacuum(path, keep_lines, keep_days, dry_run=False):
    now = time.time()
    cutoff = now - keep_days * 86400.0

    if not os.path.exists(path):
        return {"status": "no-file", "path": path}

    st0 = os.stat(path)
    size0 = st0.st_size
    if size0 == 0:
        return {"status": "empty", "path": path}

    with open(path, "r", encoding="utf-8") as f:
        raw_lines = [l for l in f.read().split("\n") if l]
    read_offset = size0  # byte offset we have consumed (== size0: read whole file)

    # select survivors: age filter, then tail cap. Malformed lines are kept
    # (they are evidence too, and tiny); unparseable ts keeps the row.
    survivors = []
    dropped_age, dropped_cap = 0, 0
    for line in raw_lines:
        try:
            ts = parse_ts(json.loads(line).get("ts"))
        except Exception:
            ts = None
        if ts is not None and ts < cutoff:
            dropped_age += 1
            continue
        survivors.append(line)
    if len(survivors) > keep_lines:
        dropped_cap = len(survivors) - keep_lines
        survivors = survivors[-keep_lines:]

    report = {
        "status": "ok",
        "path": path,
        "before_lines": len(raw_lines),
        "after_lines": len(survivors),
        "dropped_age": dropped_age,
        "dropped_cap": dropped_cap,
        "before_bytes": size0,
        "race_retries": 0,
        "dry_run": dry_run,
    }

    if dry_run:
        report["status"] = "dry-run"
        return report
    if dropped_age == 0 and dropped_cap == 0:
        report["status"] = "no-op"
        return report

    d = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".judge-evidence-vacuum-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for line in survivors:
                f.write(line + "\n")
            # race window: writer may have appended while we read/wrote.
            # Fold the new tail in (bounded retries), then fsync.
            retries = 0
            while retries < MAX_RACE_RETRIES:
                cur = os.stat(path).st_size
                if cur == read_offset:
                    break
                for line in read_tail_new_lines(path, read_offset):
                    f.write(line + "\n")
                    report["after_lines"] += 1
                read_offset = os.stat(path).st_size
                retries += 1
            report["race_retries"] = retries
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, st0.st_mode & 0o777)  # preserve source permissions
        os.replace(tmp, path)               # atomic swap
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--path", default=DEFAULT_PATH)
    ap.add_argument("--keep-lines", type=int, default=50000)
    ap.add_argument("--keep-days", type=float, default=30)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    try:
        rep = vacuum(args.path, args.keep_lines, args.keep_days, args.dry_run)
    except Exception as e:  # noqa: BLE001 -- CLI must report, never traceback-loop
        print(f"vacuum FAILED on {args.path}: {e}", file=sys.stderr)
        return 1

    s = rep["status"]
    if s == "no-file":
        print(f"vacuum: no file at {args.path}; nothing to do.")
    elif s == "empty":
        print(f"vacuum: {args.path} is empty; nothing to do.")
    elif s == "no-op":
        print(f"vacuum: {args.path}: {rep['before_lines']} lines all within "
              f"{args.keep_days:g}d / {args.keep_lines} cap; no vacuum needed.")
    else:
        tag = "DRY-RUN " if rep["dry_run"] else ""
        race = (" race_retries=%d" % rep["race_retries"]) if rep["race_retries"] else ""
        print("vacuum %s%s: %d -> %d lines (dropped %d by age, %d by cap%s)"
              % (tag, args.path, rep["before_lines"], rep["after_lines"],
                 rep["dropped_age"], rep["dropped_cap"], race))
    return 0


if __name__ == "__main__":
    sys.exit(main())
