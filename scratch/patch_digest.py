#!/usr/bin/env python3
"""Coordinator patch 7: `digest` command (fleet_delta slow-path)."""
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
    "import fleet_dag\nimport fleet_ephemeral\n",
    "import fleet_dag\nimport fleet_delta\nimport fleet_ephemeral\n",
)

# 2. cmd_digest, placed just before cmd_read
rep(
    "def cmd_read(root: Path, a):\n",
    '''def cmd_digest(root: Path, a):
    """Slow-path what's-new digest across ALL channels (delta-state sync).

    One line per unread message: "<channel> #<seq> <from>-><to> <lamport>
    <body, 80 chars>". The per-agent vector (.vectors/<agent>.json) advances
    unless --peek. First use migrates the base's .cursors into the vector so
    the digest starts from "what I've read".

    NOTE: digest lines are addressing-filtered hints for slow-path agents;
    the HMAC/roster trust boundary is enforced on the full read path.
    """
    vec = fleet_delta.load_vector(root, a.agent)
    if not vec:
        vec = fleet_delta.migrate_from_cursors(root, a.agent)
    deltas = fleet_delta.delta(root, a.agent)
    for line in fleet_delta.delta_digest(root, a.agent, relevant_only=not a.all):
        print(line)
    if not deltas:
        print(f"(no new messages for {a.agent}; vector unchanged)")
        return
    if not a.peek:
        adv = dict(vec)
        for ch, paths in deltas.items():
            top = max((_seq_from_name(p.name) or 0) for p in paths)
            adv[ch] = max(adv.get(ch, 0), top)
        fleet_delta.advance(root, a.agent, adv)


def cmd_read(root: Path, a):
''',
)

# 3. argparse: digest subcommand (place after the read parser block).
# Find the read parser block first -- read it dynamically is overkill;
# anchor on the peek parser which follows read.
rep(
    '''    s = sub.add_parser("peek", help="show last N messages without touching the cursor")''',
    '''    s = sub.add_parser("digest", help="slow-path what's-new digest across all channels")
    s.add_argument("--as", dest="agent", required=True, help="agent reading the digest")
    s.add_argument("--peek", action="store_true", help="print digest but do not advance the vector")
    s.add_argument("--all", action="store_true", help="include messages not addressed to the agent")
    s.set_defaults(func=cmd_digest)

    s = sub.add_parser("peek", help="show last N messages without touching the cursor")''',
)

CHAT.write_text(src, encoding="utf-8")
print("patch applied:", CHAT)
