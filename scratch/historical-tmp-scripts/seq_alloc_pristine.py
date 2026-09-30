#!/usr/bin/env python3
"""Monotonic per-channel sequence allocator for squawk.

Why this exists (2026-09-21): the old allocator derived next-seq from the
live directory listing (max "<seq>-*.md" filename + 1). Whenever message
files were deleted or archived, it REUSED dead sequence numbers -- and the
feed server's in-memory high-water mark then suppressed the "new" message
forever (seq <= high looks already-delivered to every long-poll client).
Observed: a completion notice allocated seq 12805 after 12816 already
existed; it never reached any live client.

This module keeps a durable, never-decreasing high-water mark per channel::

    <root>/.seqhigh-<channel>

``alloc_seq`` serializes the read-modify-write on its own internal flock
(``<root>/.seqalloc-<channel>.lock``), so every writer -- the feed server's
``_publish_message``, ``chat_core._next_seq``, the legacy
``hatch/agents/ember/chat`` ``_next_seq``, and the hatch ``squawk`` CLI --
gets a unique, strictly increasing seq even though they use different outer
locks. The outer per-writer locks are kept as defense-in-depth (they also
protect DAG-parent computation and the file write itself).

Allocation rule:  seq = max(disk_max, stored_high) + 1;  store seq.

The disk_max term means a fresh channel (or a deliberately wiped .seqhigh
file) still starts above every file on disk; the stored term means deleted
files can never pull the counter back.

Usage as a script (safe to call inside a writer's own outer lock --
alloc_seq only takes its own internal lock):
    seq_alloc.py <root> <channel>                -> print allocated seq
    seq_alloc.py --seed <root> <channel> <floor>  -> ensure stored >= floor
"""

from __future__ import annotations

import fcntl
import os
import re
import sys
import time
from pathlib import Path

_MSG_RE = re.compile(r"^(\d+)-.*\.md$")
_LOCK_TIMEOUT = 15.0


def high_path(root: Path | str, channel: str) -> Path:
    return Path(root) / f".seqhigh-{channel}"


def _alloc_lock_path(root: Path | str, channel: str) -> Path:
    return Path(root) / f".seqalloc-{channel}.lock"


def disk_high(chan_dir: Path | str) -> int:
    """Max seq among message files actually on disk (0 when empty)."""
    top = 0
    try:
        names = os.listdir(chan_dir)
    except OSError:
        return 0
    for name in names:
        m = _MSG_RE.match(name)
        if m:
            v = int(m.group(1))
            if v > top:
                top = v
    return top


def read_high(root: Path | str, channel: str) -> int:
    """Durable high-water mark (0 when never allocated)."""
    try:
        return int(high_path(root, channel).read_text(encoding="utf-8").strip() or "0")
    except (OSError, ValueError):
        return 0


def _write_high_atomic(path: Path, value: int) -> None:
    tmp = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    tmp.write_text(f"{value}\n", encoding="utf-8")
    os.replace(tmp, path)

def _locked(root: Path, channel: str):
    """Context manager: exclusive internal alloc lock for the channel."""
    from contextlib import contextmanager

    @contextmanager
    def _ctx():
        lock_path = _alloc_lock_path(root, channel)
        try:
            lock_path.touch(exist_ok=True)
        except OSError:
            pass
        deadline = time.time() + _LOCK_TIMEOUT
        with open(lock_path, "w") as lockf:
            while True:
                try:
                    fcntl.flock(lockf, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError:
                    if time.time() >= deadline:
                        raise TimeoutError(f"seq-alloc lock busy: {lock_path}")
                    time.sleep(0.02)
            try:
                yield
            finally:
                fcntl.flock(lockf, fcntl.LOCK_UN)

    return _ctx()


def alloc_seq(root: Path | str, channel: str) -> int:
    """Allocate the next monotonic seq for the channel and persist it.

    Safe to call from any writer process: the read-modify-write is
    serialized on the internal per-channel flock. Never return a  seq at
    or below any previously allocated one, even if message files were
    deleted in the meantime.
    """
    root = Path(root)
    chan_dir = root / channel
    try:
        chan_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    with _locked(root, channel):
        seq = max(disk_high(chan_dir), read_high(root, channel)) + 1
        _write_high_atomic(high_path(root, channel), seq)
        return seq


def seed_high(root: Path | str, channel: str, floor: int) -> int:
    """Ensure the durable mark is >= floor (and >= disk). Returns the mark."""
    root = Path(root)
    with _locked(root, channel):
        cur = max(read_high(root, channel), disk_high(root / channel), int(floor))
        _write_high_atomic(high_path(root, channel), cur)
        return cur


def main(argv: list[str]) -> int:
    if len(argv) == 5 and argv[1] == "--seed":
        print(seed_high(argv[2], argv[3], argv[4]))
        return 0
    if len(argv) == 3:
        print(alloc_seq(argv[1], argv[2]))
        return 0
    sys.stderr.write(
        "usage: seq_alloc.py <root> <channel>\n"
        "       seq_alloc.py --seed <root> <channel> <floor>\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
