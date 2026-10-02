#!/usr/bin/env python3
"""Coordinator patch 8: presence commands (heartbeat/presence/suspect).

Design note: heartbeat() bumps incarnation on EVERY call, so it is wired as
an explicit per-turn command, NOT auto-called on every chat.py invocation.
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

# 1. import
rep(
    "import fleet_roster\nimport fleet_time\n",
    "import fleet_presence\nimport fleet_roster\nimport fleet_time\n",
)

# 2. commands, placed just before cmd_channels
rep(
    "def cmd_channels(root: Path, a):\n",
    '''def cmd_heartbeat(root: Path, a):
    """Explicit per-turn liveness ping. Call at the top of every agent turn.

    Incarnation bumps on every call, so this is NOT auto-wired into other
    commands -- one heartbeat per agent turn is the contract.
    """
    hb = fleet_presence.heartbeat(root, a.agent)
    print(f"heartbeat for '{a.agent}': incarnation={hb['incarnation']}")


def cmd_presence(root: Path, a):
    """SWIM-style liveness hints. NEVER authorization: fleet_roster.py is the
    trust registry; this is gossip-targeting only."""
    states = fleet_presence.alive_agents(root)
    names = sorted([a.agent] if a.agent else states)
    if not names:
        print("(no heartbeats recorded yet)")
        return
    print(f"{'AGENT':<28}{'STATE':<10}LAST-SEEN")
    for name in names:
        state = states.get(name, "dead")  # never heartbeated
        age = fleet_presence.heartbeat_age(root, name)
        age_s = "never" if age == float("inf") else f"{age:.0f}s ago"
        print(f"{name:<28}{state:<10}{age_s}")
    print()
    print("liveness hints, NOT credentials: never use presence for authorization.")
    print("suspect/dead = no heartbeat within 60s/300s; idle and crashed are")
    print("indistinguishable. A fresh heartbeat always refutes suspicion marks.")


def cmd_suspect(root: Path, a):
    """Record a SWIM suspicion mark (gossip hint with attribution, not a verdict)."""
    ok = fleet_presence.suspect(root, a.by, a.peer, a.reason or "")
    if ok:
        print(f"suspicion mark recorded: {a.by} suspects {a.peer}")
    else:
        print(f"(no mark: {a.peer} heartbeat is fresh or never seen)")


def cmd_channels(root: Path, a):
''',
)

# 3. argparse: three subcommands after the gc block
rep(
    '''    s = sub.add_parser("gc", help="archive then reap expired ephemeral channels")
    s.add_argument("--dry-run", action="store_true", help="list what would be reaped")
    s.set_defaults(func=cmd_gc)
''',
    '''    s = sub.add_parser("gc", help="archive then reap expired ephemeral channels")
    s.add_argument("--dry-run", action="store_true", help="list what would be reaped")
    s.set_defaults(func=cmd_gc)

    s = sub.add_parser("heartbeat", help="per-turn liveness ping (call at the top of every agent turn)")
    s.add_argument("--as", dest="agent", required=True, help="agent sending the heartbeat")
    s.set_defaults(func=cmd_heartbeat)

    s = sub.add_parser(
        "presence",
        help="SWIM-style liveness hints (NOT credentials -- never use for authorization)",
    )
    s.add_argument("agent", nargs="?", default=None, help="single agent to inspect (default: all)")
    s.set_defaults(func=cmd_presence)

    s = sub.add_parser("suspect", help="record a SWIM suspicion mark (gossip hint, not a verdict)")
    s.add_argument("peer", help="agent suspected of being down")
    s.add_argument("--by", required=True, help="agent recording the suspicion")
    s.add_argument("--reason", default="", help="why the peer is suspected")
    s.set_defaults(func=cmd_suspect)
''',
)

CHAT.write_text(src, encoding="utf-8")
print("patch applied:", CHAT)
