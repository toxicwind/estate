#!/usr/bin/env python3
"""Coordinator patch 16: wire fleet_bids into chat.py.

- task bid / task bids commands.
- cmd_task_claim: bid gate (only the consensus winner may claim while
  live bids exist), archive the round on success, stigmergy claim trace.
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
    "import fleet_e2ee\nimport fleet_ephemeral\n",
    "import fleet_bids\nimport fleet_e2ee\nimport fleet_ephemeral\n",
)

# cmd_task_claim: gate + archive + trace.
rep(
    '''def cmd_task_claim(root: Path, a):
    store = _lease_store(root, a.channel)
    with contextlib.redirect_stdout(io.StringIO()):
        task = store.claim(
            a.task_id,
            _task_actor(a),
            lease_seconds=a.lease_seconds,
        )
    _print_task_result("claimed", task)''',
    '''def cmd_task_claim(root: Path, a):
    # Fleet bid-then-consensus (Wang et al. 2022): while a live bid round
    # exists for the task, only the consensus winner may claim. No live
    # bids -> legacy first-come behavior. The lease itself still comes
    # from the base LeaseStore; this is a pre-check, not a new task board.
    actor = _task_actor(a)
    bid_res = None
    try:
        bid_res = fleet_bids.check_claim(root, a.channel, a.task_id, actor)
    except fleet_bids.BidError as e:
        die(str(e))
    store = _lease_store(root, a.channel)
    with contextlib.redirect_stdout(io.StringIO()):
        task = store.claim(
            a.task_id,
            actor,
            lease_seconds=a.lease_seconds,
        )
    # The round is decided: archive its bids so a later release starts fresh.
    if bid_res is not None:
        fleet_bids.archive_round(root, a.channel, a.task_id)
    # Stigmergy: every successful claim leaves a trace for suggest-role.
    # Traces must never break claims.
    try:
        note = f"claimed {a.task_id}"
        if bid_res is not None:
            wb = next(
                (b for b in bid_res["ranked"] if b["agent"] == actor), None
            )
            if wb is not None:
                note += f" as bid-winner (score={wb['score']})"
        fleet_stigmergy.record_claim(root, a.channel, actor, "task", note=note)
    except Exception:
        pass
    _print_task_result("claimed", task)''',
)

# New commands, next to the other task_* handlers.
rep(
    '''def cmd_task_renew(root: Path, a):''',
    '''def cmd_task_bid(root: Path, a):
    """Record a suitability bid for bid-then-consensus allocation."""
    try:
        bid = fleet_bids.record_bid(
            root, a.channel, a.task_id, _task_actor(a), a.score, note=a.note or ""
        )
    except fleet_bids.BidError as e:
        die(str(e))
    res = fleet_bids.resolve(root, a.channel, a.task_id)
    print(
        f"bid recorded for task '{a.task_id}' by '{bid['agent']}' "
        f"(score={bid['score']})"
    )
    if res["winner"]:
        ranked = ", ".join(f"{b['agent']}={b['score']}" for b in res["ranked"])
        print(f"current consensus winner: '{res['winner']}' (ranked: {ranked})")


def cmd_task_bids(root: Path, a):
    """Show (or clear) a task's current bid round."""
    if a.clear:
        n = fleet_bids.clear_bids(root, a.channel, a.task_id)
        print(f"cleared {n} bid(s) for task '{a.task_id}'")
        return
    res = fleet_bids.resolve(root, a.channel, a.task_id)
    if a.json:
        print(json.dumps(res, indent=2))
        return
    if not res["ranked"]:
        print(f"(no live bids for task '{a.task_id}')")
        return
    for i, b in enumerate(res["ranked"], 1):
        mark = " <-- consensus winner" if b["agent"] == res["winner"] else ""
        note = f" -- {b['note']}" if b.get("note") else ""
        print(f"{i}. {b['agent']}: score={b['score']}{mark}{note}")


def cmd_task_renew(root: Path, a):''',
)

# Argparse: add bid/bids under task_sub, right after claim.
rep(
    '''    s = task_sub.add_parser("claim", help="claim a ready task with a lease")
    s.add_argument("channel", help="channel containing the task")
    s.add_argument("task_id", help="task to claim")
    s.add_argument(
        "--as", "--from", dest="actor", required=True, help="agent claiming the task"
    )
    s.add_argument(
        "--lease-seconds",
        "--lease",
        "--ttl",
        type=float,
        default=300.0,
        help="duration of the lease in seconds",
    )
    s.set_defaults(func=cmd_task_claim)''',
    '''    s = task_sub.add_parser("claim", help="claim a ready task with a lease")
    s.add_argument("channel", help="channel containing the task")
    s.add_argument("task_id", help="task to claim")
    s.add_argument(
        "--as", "--from", dest="actor", required=True, help="agent claiming the task"
    )
    s.add_argument(
        "--lease-seconds",
        "--lease",
        "--ttl",
        type=float,
        default=300.0,
        help="duration of the lease in seconds",
    )
    s.set_defaults(func=cmd_task_claim)

    s = task_sub.add_parser(
        "bid", help="bid for a task (bid-then-consensus allocation)"
    )
    s.add_argument("channel", help="channel containing the task")
    s.add_argument("task_id", help="task to bid on")
    s.add_argument(
        "--as", "--from", dest="actor", required=True, help="bidding agent"
    )
    s.add_argument(
        "--score", type=float, required=True,
        help="self-assessed suitability in [0, 1]; highest wins",
    )
    s.add_argument("--note", default="", help="why suited (free-form)")
    s.set_defaults(func=cmd_task_bid)

    s = task_sub.add_parser("bids", help="show or clear a task's bid round")
    s.add_argument("channel", help="channel containing the task")
    s.add_argument("task_id", help="task to inspect")
    s.add_argument(
        "--clear", action="store_true",
        help="leader intervention: discard the round's bids",
    )
    s.add_argument("--json", action="store_true", help="raw resolution as JSON")
    s.set_defaults(func=cmd_task_bids)''',
)

p.write_text(src, encoding="utf-8")
print("patch applied:", p)
