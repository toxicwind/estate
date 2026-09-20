#!/usr/bin/env python3
"""Coordinator patch 13: cmd_wait must not return on irrelevant messages.

Bug: when wait_for_new_messages returned files but every one was
irrelevant to the waiting agent, cmd_wait advanced the cursor to max_seq
and returned anyway -- the wait ended with nothing delivered.

Fix: track whether anything relevant was delivered. If not, advance the
in-memory scan cursor past the irrelevant messages (so we don't
busy-loop) and keep waiting until a relevant message arrives or the
deadline hits. The on-disk cursor only advances when something is
actually delivered, so a timed-out wait doesn't silently consume
messages the agent never saw.
"""
from pathlib import Path

CHAT = Path("/home/toxic/.shingle/chat/chat.py")
src = CHAT.read_text(encoding="utf-8")

old = """        found = _fw.wait_for_new_messages(d, cur, remaining)
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
                # Fleet Lamport: fold the sender's clock into ours.
                fleet_time.observe(root, a.agent, fleet_time.message_lamport(meta))
                _print_message(p)
            write_cursor(d, a.agent, max_seq(d))
            return"""
new = """        found = _fw.wait_for_new_messages(d, cur, remaining)
        if found:
            delivered = False
            for p in found:
                meta = parse_frontmatter(p)
                if not a.all and not is_relevant(meta, a.agent):
                    continue
                try:
                    meta = fleet_identity.verify_on_read(p)
                except fleet_identity.FleetIdentityError as e:
                    die(f"identity check failed: {e}")
                _sender_cleared(meta)
                # Fleet Lamport: fold the sender's clock into ours.
                fleet_time.observe(root, a.agent, fleet_time.message_lamport(meta))
                _print_message(p)
                delivered = True
            if delivered:
                write_cursor(d, a.agent, max_seq(d))
                return
            # Only irrelevant messages arrived: advance the in-memory scan
            # cursor past them and keep waiting for something relevant.
            # The on-disk cursor is untouched -- a timed-out wait must not
            # silently consume messages the agent never saw.
            cur = max_seq(d)
            continue"""
assert src.count(old) == 1
src = src.replace(old, new, 1)
CHAT.write_text(src, encoding="utf-8")
print("patched")
