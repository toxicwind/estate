#!/usr/bin/env python3
"""Coordinator patch 1: HMAC identity wiring into chat.py.

Applies exact-string edits; asserts each anchor occurs exactly once.
Run: python3 patch_identity.py  (cwd = /home/toxic/.shingle/chat)
"""
import sys
from pathlib import Path

CHAT = Path("/home/toxic/.shingle/chat/chat.py")
src = CHAT.read_text(encoding="utf-8")

def rep(old: str, new: str) -> None:
    global src
    n = src.count(old)
    assert n == 1, f"anchor found {n}x (expected 1): {old[:70]!r}"
    src = src.replace(old, new, 1)
    print(f"ok: {old[:60]!r}...")

# 1. imports
rep(
    "from fleet_addr import addressed_wait_filter\n",
    "from fleet_addr import addressed_wait_filter\n\nimport fleet_identity\nimport fleet_roster\n",
)

# 2. docstring command list
rep(
    "Commands: init | channels | roster | post | read | wait | peek | claim | lock | check | unlock | recover | recover-pending | task | state | compact | event\n",
    "Commands: init | channels | roster | post | read | wait | peek | claim | lock | check | unlock | recover | recover-pending | task | state | compact | event | keygen\n",
)

# 3. roster revocation gate helper, placed just before cmd_read
rep(
    "def cmd_read(root: Path, a):\n",
    '''def _sender_cleared(meta: dict) -> None:
    """Roster revocation gate: call after HMAC verification on a read path.

    Rejects revoked senders outright. Unknown senders are rejected once the
    roster is enrolled (non-empty); an empty roster means bootstrap mode where
    HMAC alone is the gate.
    """
    sender = meta.get("from", "")
    rec = fleet_roster.lookup(sender)
    if rec is not None and rec.get("revoked"):
        die(f"identity check failed: sender '{sender}' is revoked")
    if rec is None and fleet_roster.list_all():
        die(f"identity check failed: sender '{sender}' is not enrolled in the fleet roster")


def cmd_read(root: Path, a):
''',
)

# 4. cmd_post: sign and append hmac field
rep(
    '''        fm += [
            f"channel: {channel}",
            f"ts: {timestamp}",
            f"status: {status}",
            f"title: {title}",
            "---",
            "",
        ]
        (d / fname).write_text("\\n".join(fm) + body.rstrip() + "\\n", encoding="utf-8")''',
    '''        # Fleet identity: HMAC-sign the canonical message bytes. sign() raises
        # FleetIdentityError when the sender has no key -> the post fails closed.
        sig = fleet_identity.sign(
            sender,
            fleet_identity.canonical_message(
                seq=seq,
                sender=sender,
                to=to,
                reply_to=reply,
                channel=channel,
                ts=timestamp,
                status=status,
                title=title,
                body=body,
            ),
        )
        fm += [
            f"channel: {channel}",
            f"ts: {timestamp}",
            f"status: {status}",
            f"title: {title}",
            f"hmac: {sig}",
            "---",
            "",
        ]
        (d / fname).write_text("\\n".join(fm) + body.rstrip() + "\\n", encoding="utf-8")''',
)

# 5. cmd_read loop: verify + roster gate
rep(
    '''    for seq, p in found:
        meta = parse_frontmatter(p)
        if not a.all and not is_relevant(meta, a.agent):
            continue
        _print_message(p)
        shown += 1''',
    '''    for seq, p in found:
        meta = parse_frontmatter(p)
        if not a.all and not is_relevant(meta, a.agent):
            continue
        try:
            meta = fleet_identity.verify_on_read(p)
        except fleet_identity.FleetIdentityError as e:
            die(f"identity check failed: {e}")
        _sender_cleared(meta)
        _print_message(p)
        shown += 1''',
)

# 6. cmd_peek loop: verify + roster gate
rep(
    '''    for p in files:
        _print_message(p)
    if not files:
        print(f"(channel '{a.channel}' is empty)")''',
    '''    for p in files:
        try:
            meta = fleet_identity.verify_on_read(p)
        except fleet_identity.FleetIdentityError as e:
            die(f"identity check failed: {e}")
        _sender_cleared(meta)
        _print_message(p)
    if not files:
        print(f"(channel '{a.channel}' is empty)")''',
)

# 7. cmd_keygen, placed just before cmd_channels
rep(
    "def cmd_channels(root: Path, a):\n",
    '''def cmd_keygen(root: Path, a):
    try:
        key_path = fleet_identity.keygen(a.agent_id, force=a.force)
    except fleet_identity.FleetIdentityError as e:
        die(str(e))
    print(f"key written for '{a.agent_id}' at {key_path}  (keep it secret; 0600)")


def cmd_channels(root: Path, a):
''',
)

# 8. argparse: keygen subcommand after init
rep(
    '''    s = sub.add_parser("init", help="create a channel")
    s.add_argument("channel", help="name of the channel to create")
    s.add_argument("--members", help="comma-separated agent names")
    s.add_argument("--topic", help="initial topic of the channel")
    s.set_defaults(func=cmd_init)
''',
    '''    s = sub.add_parser("init", help="create a channel")
    s.add_argument("channel", help="name of the channel to create")
    s.add_argument("--members", help="comma-separated agent names")
    s.add_argument("--topic", help="initial topic of the channel")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("keygen", help="mint an HMAC identity key for an agent")
    s.add_argument("agent_id", help="agent id (must match fleet identity rules)")
    s.add_argument("--force", action="store_true", help="rotate: replace existing key")
    s.set_defaults(func=cmd_keygen)
''',
)

CHAT.write_text(src, encoding="utf-8")
print("patch applied:", CHAT)
