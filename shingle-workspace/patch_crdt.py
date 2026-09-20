#!/usr/bin/env python3
"""Coordinator patch 17: wire fleet_crdt op appends + ops command.

Appends (never break the action; warn to stderr on failure):
- cmd_post  -> post op {seq}
- cmd_react -> react op {target_seq, kind, strength}
- cmd_init  -> channel-create op on the ROOT op log
- cmd_task_bid -> bid op {task_id, score, ts}
- cmd_task_claim -> claim op {task_id, agent} on success
New: `chat.py ops [channel] [--json] [--materialize]`.
"""
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
    "import fleet_bids\nimport fleet_e2ee\n",
    "import fleet_bids\nimport fleet_crdt\nimport fleet_e2ee\n",
)

# Helper: op appends never break actions.
rep(
    '''def _print_message(path: Path, meta: dict | None = None):''',
    '''def _record_op(root: Path, channel: str | None, kind: str, actor: str,
               lamport: int, payload: dict) -> None:
    """Append one CRDT op. Fail soft (stderr warning): the op log is a
    derived index, and it must never break the action it records."""
    try:
        fleet_crdt.append_op(
            root, channel,
            fleet_crdt.make_op(kind, channel or "root", actor, lamport,
                               payload=payload),
        )
    except Exception as e:  # noqa: BLE001 -- op log never breaks actions
        print(f"(warning: op log append failed: {e})", file=sys.stderr)


def _print_message(path: Path, meta: dict | None = None):''',
)

# 1. cmd_post -> post op (after the lock is released, lamport in scope).
rep(
    '''    finally:
        _release_lock(lock)
    print(f"posted #{seq} -> {a.channel}/{fname}")''',
    '''    finally:
        _release_lock(lock)
    # Fleet CRDT: the post is a commutative operation; the op log lets any
    # replica converge on the same action set regardless of order.
    _record_op(root, channel, fleet_crdt.POST, sender, lamport, {"seq": seq})
    print(f"posted #{seq} -> {a.channel}/{fname}")''',
)

# 2. cmd_init -> channel-create op on the root log.
rep(
    '''    # Fleet discovery: index the channel AFTER _meta.json is durably written,
    # so a crashed init never indexes a half-made channel.
    fleet_watch.note_channel(root, a.channel)''',
    '''    # Fleet discovery: index the channel AFTER _meta.json is durably written,
    # so a crashed init never indexes a half-made channel.
    fleet_watch.note_channel(root, a.channel)
    # Fleet CRDT: channel creation is a commutative op on the root log.
    _record_op(
        root, None, fleet_crdt.CHANNEL_CREATE, "system", 0,
        {"channel": a.channel},
    )''',
)

# 3. cmd_react -> react op (a reaction is a send event: tick the clock).
rep(
    '''    print(f"trace deposited on #{a.seq} in '{a.channel}' (kind={a.kind})")''',
    '''    print(f"trace deposited on #{a.seq} in '{a.channel}' (kind={a.kind})")
    # Fleet CRDT: the reaction is a commutative operation.
    _record_op(
        root, a.channel, fleet_crdt.REACT, a.agent,
        fleet_time.tick(root, a.agent),
        {"target_seq": a.seq, "react_kind": a.kind, "strength": a.strength},
    )''',
)

# 4. cmd_task_bid -> bid op.
rep(
    '''    if res["winner"]:
        ranked = ", ".join(f"{b['agent']}={b['score']}" for b in res["ranked"])
        print(f"current consensus winner: '{res['winner']}' (ranked: {ranked})")''',
    '''    if res["winner"]:
        ranked = ", ".join(f"{b['agent']}={b['score']}" for b in res["ranked"])
        print(f"current consensus winner: '{res['winner']}' (ranked: {ranked})")
    # Fleet CRDT: the bid is a commutative operation (latest-wins per agent).
    _record_op(
        root, a.channel, fleet_crdt.BID, _task_actor(a),
        fleet_time.tick(root, _task_actor(a)),
        {"task_id": a.task_id, "score": bid["score"], "ts": bid["ts"]},
    )''',
)

# 5. cmd_task_claim -> claim op on success (next to the stigmergy trace).
rep(
    '''    # Stigmergy: every successful claim leaves a trace for suggest-role.
    # Traces must never break claims.
    try:''',
    '''    # Fleet CRDT: the claim is a commutative operation (LWW by lamport).
    _record_op(
        root, a.channel, fleet_crdt.CLAIM, actor,
        fleet_time.tick(root, actor),
        {"task_id": a.task_id, "agent": actor},
    )
    # Stigmergy: every successful claim leaves a trace for suggest-role.
    # Traces must never break claims.
    try:''',
)

# 6. ops command.
rep(
    '''def cmd_task_renew(root: Path, a):''',
    '''def cmd_ops(root: Path, a):
    """Show the commutative op log (Shapiro et al. 2011).

    The op log records every fleet action kind -- posts, reactions,
    channel creates, bids, claims -- as commutative operations. Any two
    replicas that have seen the same ops materialize the same state,
    regardless of the order they observed them in. The .md files remain
    the canonical human-readable data; this is the convergence substrate.
    """
    ops = fleet_crdt.read_ops(root, a.channel)
    if a.json:
        print(json.dumps(ops, indent=2))
        return
    where = f"channel '{a.channel}'" if a.channel else "root"
    if not ops:
        print(f"(no ops for {where})")
        return
    if a.materialize:
        state = fleet_crdt.materialize(ops)
        print(f"{where}: {len(ops)} op(s) materialized")
        print(f"  messages: {sorted(state['messages'])}")
        print(f"  reactions: {len(state['reactions'])}")
        print(f"  channels: {state['channels']}")
        bids = {
            t: {ag: b["score"] for ag, b in agents.items()}
            for t, agents in state["bids"].items()
        }
        print(f"  bids: {bids}")
        claims = {t: c["agent"] for t, c in state["claims"].items()}
        print(f"  claims: {claims}")
        return
    for o in ops:
        print(f"{o['lamport']:>4} {o['kind']:<14} {o['actor']:<12} {o['op_id']}")


def cmd_task_renew(root: Path, a):''',
)

# Argparse for ops (next to gossip).
rep(
    '''    s = sub.add_parser(
        "gossip",
        help="anti-entropy pass: scan seq gaps, backfill from log, compare digests",
    )''',
    '''    s = sub.add_parser(
        "ops",
        help="show the commutative op log (posts, reactions, bids, claims...)",
    )
    s.add_argument(
        "channel", nargs="?", default=None,
        help="channel to inspect (omit for the root channel-create log)",
    )
    s.add_argument("--json", action="store_true", help="raw ops as JSON")
    s.add_argument(
        "--materialize", action="store_true",
        help="fold the ops into replica state",
    )
    s.set_defaults(func=cmd_ops)

    s = sub.add_parser(
        "gossip",
        help="anti-entropy pass: scan seq gaps, backfill from log, compare digests",
    )''',
)

p.write_text(src, encoding="utf-8")
print("patch applied:", p)
