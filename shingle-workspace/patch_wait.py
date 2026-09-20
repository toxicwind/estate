#!/usr/bin/env python3
"""Coordinator patch 2: inotify fast-path wait via fleet_wait.

Replaces cmd_wait's sleep-poll loop. Run: python3 patch_wait.py
(cwd = /home/toxic/.shingle/chat)
"""
from pathlib import Path

CHAT = Path("/home/toxic/.shingle/chat/chat.py")
src = CHAT.read_text(encoding="utf-8")

def rep(old: str, new: str) -> None:
    global src
    n = src.count(old)
    assert n == 1, f"anchor found {n}x (expected 1): {old[:70]!r}"
    src = src.replace(old, new, 1)
    print(f"ok: {old[:60]!r}...")

# 1. import fleet_wait alongside the other fleet imports
rep(
    "import fleet_identity\nimport fleet_roster\n",
    "import fleet_identity\nimport fleet_roster\nimport fleet_wait\n",
)

# 2. replace the whole cmd_wait body
old_wait = '''def cmd_wait(root: Path, a):
    d = require_channel(root, a.channel)
    cur = read_cursor(d, a.agent)
    deadline = time.time() + a.timeout
    last_mtime = 0
    while True:
        try:
            mtime = d.stat().st_mtime
        except OSError:
            mtime = 0

        found = []
        if mtime == 0 or mtime != last_mtime:
            last_mtime = mtime
            # Optimization: use os.scandir to avoid Path instantiation overhead for
            # thousands of old messages per tick.
            try:
                with os.scandir(d) as it:
                    for entry in it:
                        if not entry.name.endswith(".md"):
                            continue
                        seq = _seq_from_name(entry.name)
                        if seq is None or seq <= cur:
                            continue
                        p = Path(entry.path)
                        meta = parse_frontmatter(p)
                        if a.all or is_relevant(meta, a.agent):
                            found.append(p)
            except OSError:
                pass
        if found:
            # Sort only the newly found messages
            found.sort(key=lambda p: _seq_from_name(p.name))
            for p in found:
                _print_message(p)
            write_cursor(d, a.agent, max_seq(d))
            return
        if time.time() >= deadline:
            print(
                f"(timeout after {a.timeout}s: no new messages for {a.agent} in '{a.channel}')",
                file=sys.stderr,
            )
            raise SystemExit(2)
        time.sleep(a.interval)
'''

new_wait = '''def cmd_wait(root: Path, a):
    # Fleet fast path: fleet_wait arms inotify BEFORE the initial scan (race-free),
    # falling back to scandir polling on non-Linux or inotify failure. Zero-token:
    # blocks in-process, no subprocess, no network. --interval survives as the
    # poll-fallback quantum.
    import fleet_wait as _fw

    _fw._POLL_TICK = max(0.05, a.interval)  # --interval survives as the poll-fallback quantum

    d = require_channel(root, a.channel)
    cur = read_cursor(d, a.agent)
    deadline = time.time() + a.timeout
    while True:
        remaining = max(0.0, deadline - time.time())
        found = _fw.wait_for_new_messages(d, cur, remaining)
        if found:
            for p in found:
                meta = parse_frontmatter(p)
                if not a.all and not is_relevant(meta, a.agent):
                    continue
                try:
                    meta = fleet_identity.verify_on_read(p)
                except fleet_identity.FleetIdentityError as e:
                    die(f"identity check failed: {e}")
                _sender_cleared(meta)
                _print_message(p)
            write_cursor(d, a.agent, max_seq(d))
            return
        # found == [] means the timeout expired with no new relevant messages.
        print(
            f"(timeout after {a.timeout}s: no new messages for {a.agent} in '{a.channel}')",
            file=sys.stderr,
        )
        raise SystemExit(2)
'''

rep(old_wait, new_wait)

CHAT.write_text(src, encoding="utf-8")
print("patch applied:", CHAT)
