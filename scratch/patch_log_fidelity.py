#!/usr/bin/env python3
"""Coordinator patch 11: pass fidelity fields to fleet_log.append in cmd_post."""
from pathlib import Path

CHAT = Path("/home/toxic/.shingle/chat/chat.py")
src = CHAT.read_text(encoding="utf-8")

old = """            fleet_log.append(
                root,
                channel,
                seq=seq,
                agent=sender,
                type="message",
                body=body,
                ts=timestamp,
            )"""
new = """            fleet_log.append(
                root,
                channel,
                seq=seq,
                agent=sender,
                type="message",
                body=body,
                ts=timestamp,
                # Fidelity fields: let anti-entropy backfill reconstruct a
                # byte-identical, HMAC-verifiable message file.
                msg_hmac=sig,
                to=to,
                title=title,
                reply_to=reply,
                status=status,
                lamport=lamport,
                parents=parents,
            )"""
assert src.count(old) == 1
src = src.replace(old, new, 1)
CHAT.write_text(src, encoding="utf-8")
print("patched")
