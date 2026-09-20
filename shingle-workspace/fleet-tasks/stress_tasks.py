#!/usr/bin/env python3
"""Stress test for fleet_tasks.py atomic claim.

Spawns 20 separate processes (separate interpreters, like real fleet members),
barrier-synchronizes them, and has all 20 attempt to claim the same open task.
Exactly one must win. Then exercises the lifecycle: re-claim idempotency,
non-owner complete, owner complete, claim-after-done, release flow.
"""
import json
import multiprocessing as mp
import os
import sys

sys.path.insert(0, "/home/toxic/.shingle/chat")
import fleet_tasks as ft

ROOT = "/tmp/stress-tasks"
CHANNEL = "fleet"
N = 20


def _setup():
    import shutil
    shutil.rmtree(ROOT, ignore_errors=True)
    chan = os.path.join(ROOT, CHANNEL)
    os.makedirs(os.path.join(chan, "tasks"), exist_ok=True)
    with open(os.path.join(chan, "_meta.json"), "w") as f:
        json.dump({"channel": CHANNEL, "members": [], "topic": "stress"}, f)


_BARRIER = None


def _init_pool(barrier):
    global _BARRIER
    _BARRIER = barrier


def _claimer(args):
    i, task_id = args
    _BARRIER.wait()  # all 20 hit claim_task at the same instant
    try:
        won = ft.claim_task(ROOT, CHANNEL, task_id, f"agent-{i:02d}")
        return (i, won)
    except Exception as e:  # noqa: BLE001
        return (i, f"ERROR: {type(e).__name__}: {e}")


def main():
    _setup()
    task = ft.create_task(ROOT, CHANNEL, "stress target", "claim me", "coordinator")
    tid = task["id"]
    print(f"created {tid}")

    barrier = mp.Barrier(N)
    with mp.Pool(N, initializer=_init_pool, initargs=(barrier,)) as pool:
        results = pool.map(_claimer, [(i, tid) for i in range(N)])

    winners = [i for i, r in results if r is True]
    losers = [i for i, r in results if r is False]
    errors = [(i, r) for i, r in results if r not in (True, False)]
    print(f"winners={winners} losers={len(losers)} errors={errors}")
    assert len(winners) == 1, f"ATOMICITY BROKEN: {len(winners)} winners"
    assert len(losers) == N - 1 and not errors, "unexpected results"
    winner = f"agent-{winners[0]:02d}"

    final = ft.get_task(ROOT, CHANNEL, tid)
    assert final["status"] == "claimed" and final["owner"] == winner, final
    assert ft.task_holder(ROOT, CHANNEL, tid) == winner
    print(f"PASS: exactly one winner ({winner}), task={final['status']}/{final['owner']}")

    # idempotent re-claim by holder
    assert ft.claim_task(ROOT, CHANNEL, tid, winner) is True
    # non-owner cannot complete
    assert ft.complete_task(ROOT, CHANNEL, tid, "agent-99") is False
    # owner completes
    assert ft.complete_task(ROOT, CHANNEL, tid, winner) is True
    assert ft.get_task(ROOT, CHANNEL, tid)["status"] == "done"
    # claim after done fails
    assert ft.claim_task(ROOT, CHANNEL, tid, "agent-01") is False
    # claim ticket cleaned up
    assert not os.path.exists(os.path.join(ROOT, CHANNEL, "tasks", f"{tid}.claim"))
    print("PASS: lifecycle (re-claim, non-owner complete blocked, complete, claim-after-done)")

    # release flow
    t2 = ft.create_task(ROOT, CHANNEL, "release me", "", "coordinator")
    assert ft.claim_task(ROOT, CHANNEL, t2["id"], "agent-05") is True
    assert ft.claim_task(ROOT, CHANNEL, t2["id"], "agent-06") is False
    assert ft.release_task(ROOT, CHANNEL, t2["id"], "agent-06") is False  # not owner
    assert ft.release_task(ROOT, CHANNEL, t2["id"], "agent-05") is True
    g = ft.get_task(ROOT, CHANNEL, t2["id"])
    assert g["status"] == "open" and g["owner"] is None, g
    assert ft.claim_task(ROOT, CHANNEL, t2["id"], "agent-06") is True  # re-claimable
    print("PASS: release flow")

    # list_tasks
    all_tasks = ft.list_tasks(ROOT, CHANNEL)
    assert len(all_tasks) == 2, all_tasks
    assert len(ft.list_tasks(ROOT, CHANNEL, status="done")) == 1
    assert len(ft.list_tasks(ROOT, CHANNEL, status="claimed")) == 1
    print("PASS: list_tasks + status filter")

    # events outbox
    with open(os.path.join(ROOT, CHANNEL, "tasks", "_events.jsonl")) as f:
        kinds = [json.loads(line)["kind"] for line in f]
    assert kinds.count("task_created") == 2 and "task_claimed" in kinds
    assert "task_completed" in kinds and "task_released" in kinds, kinds
    print(f"PASS: events outbox ({len(kinds)} events)")

    # missing task / bad names
    try:
        ft.claim_task(ROOT, CHANNEL, "task-deadbeefcafe", "agent-00")
        raise AssertionError("expected TaskNotFound")
    except ft.TaskNotFound:
        pass
    try:
        ft.claim_task(ROOT, CHANNEL, "../evil", "agent-00")
        raise AssertionError("expected traversal block")
    except ft.FleetTaskError:
        pass
    print("PASS: error paths (TaskNotFound, traversal guard)")

    print("ALL STRESS TESTS PASSED")


if __name__ == "__main__":
    main()
