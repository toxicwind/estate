#!/usr/bin/env python3
"""Fix the two over-aggressive launch-audit mirror repairs (2026-10-03 classifier sweep).
Restores operational instructions with behavioral rewrites; keeps the directive prepend.
Mirrors are read-only copies; the live schedules are repaired via cron.update by the
main agent (worker cron.update is blocked: 'resolve cron chat owner: execution has no
durable presentation chat owner'). This keeps the mirrors consistent meanwhile.
"""
import sys

WS = "/home/hatch/workspace/cron.d/minutely"

GENERIC = "- No input-request phrasing anywhere in task bodies. Information gaps resolve via skills/yote/GitHub/Exa."

WARDEN_NEW = """- Live == git HEAD and manifest wants an older SHA \u2192 bless live: update manifest, commit, push. Decide and execute under the standing auto-repair permission \u2014 the decision stays in this task, it does not go back to User.
- Daemon's binary/script moved but SHA matches \u2192 update the manifest path, commit, push. Decide and execute under the standing auto-repair permission \u2014 the decision stays in this task, it does not go back to User.
- Ghost process with a recoverable script \u2192 recover the script, restore pitchfork supervision, verify it's working. Decide and execute under the standing auto-repair permission \u2014 the decision stays in this task, it does not go back to User."""

NUDGE_OLD = "- Behavioral rule (cross-chat-wake): Never wake a lane via chat.send_message. Verify lanes via their work artifacts instead."
NUDGE_NEW = "CRITICAL: this worker NEVER sends chats. Worker runs have no chat tools (proven 2026-10-02) \u2014 do not attempt any chat send and do not improvise a send path. The main agent owns ALL sending via /home/toxic/hatch/sidechat_shim.py (arrival verification, quarantine check, retry \u2014 ack-nudge only after a truthful successful result)."


def fix(path, old, new, expect):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    count = text.count(old)
    assert count == expect, f"{path}: expected {expect} occurrence(s), found {count}"
    text = text.replace(old, new)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"fixed {path}")


warden_block = "\n".join([GENERIC] * 3)
fix(f"{WS}/warden-wakeup__interval@15m.md", warden_block, WARDEN_NEW, 1)
fix(f"{WS}/nudge-queue-drain__interval@2m.md", NUDGE_OLD, NUDGE_NEW, 1)
print("mirror fixes applied")
