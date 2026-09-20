#!/usr/bin/env python3
"""Coordinator patch 4: ephemeral channels + .channels-index discovery."""
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
    "import fleet_identity\nimport fleet_log\nimport fleet_roster\nimport fleet_wait\n",
    "import fleet_ephemeral\nimport fleet_identity\nimport fleet_log\nimport fleet_roster\nimport fleet_wait\nimport fleet_watch\n",
)

# 2. cmd_init: honor --ephemeral, then note the channel in .channels-index
rep(
    '''    m_str = ", ".join(members) if members else "(open)"
    print(f"created channel '{a.channel}' at {d}  members={m_str}")''',
    '''    if a.ephemeral is not None:
        fleet_ephemeral.mark_ephemeral(d, float(a.ephemeral))
    # Fleet discovery: index the channel AFTER _meta.json is durably written,
    # so a crashed init never indexes a half-made channel.
    fleet_watch.note_channel(root, a.channel)
    m_str = ", ".join(members) if members else "(open)"
    eph = f" ephemeral(ttl={a.ephemeral}s)" if a.ephemeral is not None else ""
    print(f"created channel '{a.channel}' at {d}  members={m_str}{eph}")''',
)

# 3. new commands, placed just before cmd_channels
rep(
    "def cmd_channels(root: Path, a):\n",
    '''def cmd_mark_ephemeral(root: Path, a):
    d = require_channel(root, a.channel)
    fleet_ephemeral.mark_ephemeral(d, float(a.ttl))
    print(f"channel '{a.channel}' marked ephemeral (ttl={a.ttl}s)")


def cmd_gc(root: Path, a):
    if a.dry_run:
        expired = []
        try:
            with os.scandir(root) as it:
                for entry in it:
                    if not entry.is_dir() or entry.name.startswith("."):
                        continue
                    try:
                        if fleet_ephemeral.is_expired(Path(entry.path)):
                            expired.append(entry.name)
                    except OSError:
                        pass
        except OSError as e:
            die(f"cannot scan chat root: {e}")
        if expired:
            print("would reap (expired ephemeral channels):")
            for name in sorted(expired):
                print(f"  {name}")
        else:
            print("(no expired ephemeral channels)")
        return
    reaped = fleet_ephemeral.gc(root)
    if reaped:
        print("reaped (archived to .archive/ first):")
        for name in reaped:
            print(f"  {name}")
    else:
        print("(no expired ephemeral channels)")


def cmd_channels(root: Path, a):
''',
)

# 4. argparse: --ephemeral on init; mark-ephemeral and gc subcommands
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
    s.add_argument(
        "--ephemeral",
        type=float,
        default=None,
        help="create as an ephemeral channel with this TTL in seconds",
    )
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("mark-ephemeral", help="mark a channel ephemeral with a TTL")
    s.add_argument("channel", help="channel to mark")
    s.add_argument("ttl", type=float, help="time-to-live in seconds")
    s.set_defaults(func=cmd_mark_ephemeral)

    s = sub.add_parser("gc", help="archive then reap expired ephemeral channels")
    s.add_argument("--dry-run", action="store_true", help="list what would be reaped")
    s.set_defaults(func=cmd_gc)
''',
)

CHAT.write_text(src, encoding="utf-8")
print("patch applied:", CHAT)
