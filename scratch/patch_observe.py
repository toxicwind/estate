#!/usr/bin/env python3
"""Coordinator patch 6: Lamport observe() on the read/wait paths."""
from pathlib import Path

CHAT = Path("/home/toxic/.shingle/chat/chat.py")
src = CHAT.read_text(encoding="utf-8")

def rep(old: str, new: str) -> None:
    global src
    n = src.count(old)
    assert n == 1, f"anchor found {n}x (expected 1): {old[:70]!r}"
    src = src.replace(old, new, 1)
    print(f"ok: {old[:60]!r}...")

# cmd_read loop
rep(
    """        try:
            meta = fleet_identity.verify_on_read(p)
        except fleet_identity.FleetIdentityError as e:
            die(f"identity check failed: {e}")
        _sender_cleared(meta)
        _print_message(p)
        shown += 1""",
    """        try:
            meta = fleet_identity.verify_on_read(p)
        except fleet_identity.FleetIdentityError as e:
            die(f"identity check failed: {e}")
        _sender_cleared(meta)
        # Fleet Lamport: fold the sender's clock into ours (max, no tick).
        fleet_time.observe(root, a.agent, fleet_time.message_lamport(meta))
        _print_message(p)
        shown += 1""",
)

# cmd_wait loop
rep(
    """                try:
                    meta = fleet_identity.verify_on_read(p)
                except fleet_identity.FleetIdentityError as e:
                    die(f"identity check failed: {e}")
                _sender_cleared(meta)
                _print_message(p)""",
    """                try:
                    meta = fleet_identity.verify_on_read(p)
                except fleet_identity.FleetIdentityError as e:
                    die(f"identity check failed: {e}")
                _sender_cleared(meta)
                # Fleet Lamport: fold the sender's clock into ours.
                fleet_time.observe(root, a.agent, fleet_time.message_lamport(meta))
                _print_message(p)""",
)

CHAT.write_text(src, encoding="utf-8")
print("patch applied:", CHAT)
