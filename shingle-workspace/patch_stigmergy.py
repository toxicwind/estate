#!/usr/bin/env python3
"""Coordinator patch 9: stigmergy commands (react / suggest-role)."""
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
    "import fleet_presence\nimport fleet_roster\n",
    "import fleet_presence\nimport fleet_roster\nimport fleet_stigmergy\n",
)

# 2. commands, placed just before cmd_suspect
rep(
    "def cmd_suspect(root: Path, a):\n",
    '''def cmd_react(root: Path, a):
    """Deposit a pheromone trace pointing at a message (stigmergic signal).

    Reactions are signals, NOT notifications: nobody is paged; agents that
    read the field notice. Traces decay with their TTL and are invisible
    past it.
    """
    d = require_channel(root, a.channel)
    fleet_stigmergy.react(
        root, a.channel, a.agent, target_seq=a.seq, kind=a.kind,
        strength=a.strength, ttl_s=a.ttl, note=a.note or "",
    )
    print(f"trace deposited on #{a.seq} in '{a.channel}' (kind={a.kind})")


def cmd_suggest_role(root: Path, a):
    """ADVISORY ONLY role suggestion from local claim traces.

    Emergent specialization (Ferrante et al. 2015): the fleet self-balances
    because agents follow such local readings, not because anyone assigns.
    This command never enforces, never writes, never orders -- there is no
    --enforce flag and there never will be.
    """
    require_channel(root, a.channel)
    s = fleet_stigmergy.suggest_role(root, a.channel, a.agent)
    if s is None:
        print("(no traces yet -- nothing to suggest; the field is empty)")
        return
    print(json.dumps(s, indent=2))


def cmd_suspect(root: Path, a):
''',
)

# 3. argparse after the suspect block
rep(
    '''    s = sub.add_parser("suspect", help="record a SWIM suspicion mark (gossip hint, not a verdict)")
    s.add_argument("peer", help="agent suspected of being down")
    s.add_argument("--by", required=True, help="agent recording the suspicion")
    s.add_argument("--reason", default="", help="why the peer is suspected")
    s.set_defaults(func=cmd_suspect)
''',
    '''    s = sub.add_parser("suspect", help="record a SWIM suspicion mark (gossip hint, not a verdict)")
    s.add_argument("peer", help="agent suspected of being down")
    s.add_argument("--by", required=True, help="agent recording the suspicion")
    s.add_argument("--reason", default="", help="why the peer is suspected")
    s.set_defaults(func=cmd_suspect)

    s = sub.add_parser(
        "react",
        help="deposit a pheromone trace on a message (stigmergic signal, not a notification)",
    )
    s.add_argument("channel", help="channel holding the message")
    s.add_argument("--as", dest="agent", required=True, help="reacting agent")
    s.add_argument("--seq", type=int, required=True, help="target message seq")
    s.add_argument("--kind", default="signal", help="trace kind (default: signal)")
    s.add_argument("--strength", type=float, default=1.0, help="pheromone strength")
    s.add_argument("--ttl", type=float, default=None, help="trace TTL in seconds")
    s.add_argument("--note", default="", help="free-form label (task types are emergent, not an enum)")
    s.set_defaults(func=cmd_react)

    s = sub.add_parser(
        "suggest-role",
        help="ADVISORY ONLY: suggest a specialization from local claim traces (never enforced)",
    )
    s.add_argument("channel", help="channel to read traces from")
    s.add_argument("--as", dest="agent", required=True, help="agent asking for a suggestion")
    s.set_defaults(func=cmd_suggest_role)
''',
)

CHAT.write_text(src, encoding="utf-8")
print("patch applied:", CHAT)
