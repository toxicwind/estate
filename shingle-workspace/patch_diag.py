#!/usr/bin/env python3
"""Coordinator patch 18: diagnostic CLI -- dag verify, thread view, clocks."""
from pathlib import Path

BASE = Path("/home/toxic/.shingle/chat")

p = BASE / "chat.py"
src = p.read_text(encoding="utf-8")

def rep(old: str, new: str) -> None:
    global src
    n = src.count(old)
    assert n == 1, f"anchor found {n}x (expected 1): {old[:70]!r}"
    src = src.replace(old, new, 1)
    print(f"ok: {old[:60]!r}...")

rep(
    '''def cmd_ops(root: Path, a):''',
    '''def cmd_dag(root: Path, a):
    """Verify the hash-linked message DAG of a channel.

    Checks parent links, seq integrity, duplicate seqs, cycles, and
    unparseable files. Empty problem list == clean chain.
    """
    d = require_channel(root, a.channel)
    problems = fleet_dag.verify_chain(d)
    if a.json:
        print(json.dumps(problems, indent=2))
        return
    if not problems:
        n = len(fleet_dag.read_channel(d))
        print(f"DAG for '{a.channel}': clean ({n} message(s) verified)")
        return
    print(f"DAG for '{a.channel}': {len(problems)} problem(s)")
    for prob in problems:
        print(f"  [{prob['type']}] {prob['file']}: {prob['detail']}")


def cmd_thread(root: Path, a):
    """Show the reply thread from the root message to a target.

    Target may be a full message id, an unambiguous id prefix, or a seq
    number. Follows parents[0] (the reply thread) up to genesis.
    """
    d = require_channel(root, a.channel)
    target = a.target
    if target.isdigit():
        chan = fleet_dag.read_channel(d)
        seq = int(target)
        mids = [m for m, e in chan.items() if e["seq"] == seq]
        if not mids:
            die(f"no message with seq {seq} in '{a.channel}'")
        target = mids[0]
    try:
        chain = fleet_dag.thread_view(d, target)
    except fleet_dag.FleetDagError as e:
        die(str(e))
    for path in chain:
        meta, body = fleet_dag.parse_message(path)
        first = body.strip().splitlines()[0] if body.strip() else "(empty)"
        print(f"#{meta.get('seq')} {meta.get('from', '?')}: {first[:80]}")


def cmd_clocks(root: Path, a):
    """Show per-agent Lamport clocks (causal-time diagnostics).

    Clocks advance on local sends and on observed remote timestamps.
    Large gaps flag an agent that posts but never reads.
    """
    report = fleet_time.clock_drift_report(root)
    if a.json:
        print(json.dumps(report, indent=2))
        return
    if not report:
        print("(no agent clocks recorded)")
        return
    for agent in sorted(report):
        print(f"{agent}: {report[agent]}")


def cmd_ops(root: Path, a):''',
)

rep(
    '''    s = sub.add_parser(
        "ops",
        help="show the commutative op log (posts, reactions, bids, claims...)",
    )''',
    '''    s = sub.add_parser(
        "dag",
        help="verify the hash-linked message DAG of a channel",
    )
    s.add_argument("channel", help="channel to verify")
    s.add_argument("--json", action="store_true", help="problems as JSON")
    s.set_defaults(func=cmd_dag)

    s = sub.add_parser(
        "thread",
        help="show the reply thread from root to a message",
    )
    s.add_argument("channel", help="channel containing the message")
    s.add_argument("target", help="message id, id prefix, or seq number")
    s.set_defaults(func=cmd_thread)

    s = sub.add_parser(
        "clocks",
        help="show per-agent Lamport clocks (causal-time diagnostics)",
    )
    s.add_argument("--json", action="store_true", help="clocks as JSON")
    s.set_defaults(func=cmd_clocks)

    s = sub.add_parser(
        "ops",
        help="show the commutative op log (posts, reactions, bids, claims...)",
    )''',
)

p.write_text(src, encoding="utf-8")
print("patch applied:", p)
