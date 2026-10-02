#!/usr/bin/env python3
"""Coordinator patch 3: log.jsonl append in cmd_post. Never fails the post."""
from pathlib import Path

CHAT = Path("/home/toxic/.shingle/chat/chat.py")
src = CHAT.read_text(encoding="utf-8")

def rep(old: str, new: str) -> None:
    global src
    n = src.count(old)
    assert n == 1, f"anchor found {n}x (expected 1): {old[:70]!r}"
    src = src.replace(old, new, 1)
    print(f"ok: {old[:60]!r}...")

rep(
    "import fleet_identity\nimport fleet_roster\nimport fleet_wait\n",
    "import fleet_identity\nimport fleet_log\nimport fleet_roster\nimport fleet_wait\n",
)

rep(
    '''        (d / fname).write_text("\\n".join(fm) + body.rstrip() + "\\n", encoding="utf-8")
    finally:
        _release_lock(lock)''',
    '''        (d / fname).write_text("\\n".join(fm) + body.rstrip() + "\\n", encoding="utf-8")
        # Fleet log: parallel append-only JSONL index (one os.write per record,
        # seq assigned by the caller under the existing seq lock). Never fails
        # the post: the .md file is the source of truth; a lost/corrupt
        # log.jsonl is always rebuildable from message files.
        try:
            fleet_log.append(
                root,
                channel,
                seq=seq,
                agent=sender,
                type="message",
                body=body,
                ts=timestamp,
                hmac=sig,
            )
        except Exception as e:  # noqa: BLE001 -- the index must not break posts
            print(f"(warning: log.jsonl append failed: {e})", file=sys.stderr)
    finally:
        _release_lock(lock)''',
)

CHAT.write_text(src, encoding="utf-8")
print("patch applied:", CHAT)
