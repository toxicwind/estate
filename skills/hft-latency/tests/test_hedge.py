#!/usr/bin/env python3
"""Deterministic tests for race.py --hedge-ms (hedged launch).

Exercises run_race() directly: strategies are tiny `sh -c` programs, events
are captured by swapping race.emit, WINNERS_LOG points at a tmp file.
Timing margins are generous (100s of ms) — these assert ordering and hedge
semantics, not microsecond precision.
"""
import asyncio
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))
import race


def make_strategies():
    return [
        {"name": "slow", "cmd": ["sh", "-c", "sleep 0.6; echo SLOW"],
         "match": "SLOW"},
        {"name": "fast", "cmd": ["sh", "-c", "echo FAST"], "match": "FAST"},
    ]


class Cap:
    def __init__(self):
        self.events = []

    def __call__(self, obj):
        self.events.append(obj)

    def of(self, event):
        return [e for e in self.events if e["event"] == event]


def run_race(strats, tag, log_path, **kw):
    race.WINNERS_LOG = log_path
    cap = Cap()
    old = race.emit
    race.emit = cap
    try:
        out = asyncio.run(race.run_race(
            strats, "test-1", tag, timeout=5, race_timeout=15, **kw))
    finally:
        race.emit = old
    return out, cap


def seed_winners(log_path, tag, winner, n=1):
    with open(log_path, "w") as f:
        for _ in range(n):
            f.write(json.dumps({"tag": tag, "winner": winner,
                                "latency": {}}) + "\n")


def test_hedge_off_launches_all_at_once():
    tmp = tempfile.mkdtemp()
    (winner, _o, _t, _r), cap = run_race(
        make_strategies(), "t-off", os.path.join(tmp, "w.jsonl"), hedge_ms=0)
    assert winner == "fast", winner
    starts = cap.of("attempt_start")
    assert sorted(e["name"] for e in starts) == ["fast", "slow"]
    assert all(e["t_launch_s"] < 0.2 for e in starts), starts
    assert cap.of("hedge_armed") == [] and cap.of("hedge_fired") == []
    print("PASS test_hedge_off_launches_all_at_once")


def test_hedge_fast_primary_backups_never_launch():
    tmp = tempfile.mkdtemp()
    log = os.path.join(tmp, "w.jsonl")
    seed_winners(log, "t-fast", "fast", n=3)  # fast proven -> launches alone
    (winner, _o, _t, _r), cap = run_race(
        make_strategies(), "t-fast", log, hedge_ms=500)
    assert winner == "fast", winner
    starts = cap.of("attempt_start")
    assert [e["name"] for e in starts] == ["fast"], starts
    assert len(cap.of("hedge_armed")) == 1
    assert len(cap.of("hedge_standdown")) == 1
    assert cap.of("hedge_fired") == []
    print("PASS test_hedge_fast_primary_backups_never_launch")


def test_hedge_slow_primary_fires_backups():
    tmp = tempfile.mkdtemp()  # no winners log -> config order: slow first
    (winner, _o, _t, _r), cap = run_race(
        make_strategies(), "t-slow", os.path.join(tmp, "w.jsonl"),
        hedge_ms=150)
    assert winner == "fast", winner
    starts = cap.of("attempt_start")
    assert [e["name"] for e in starts] == ["slow", "fast"], starts
    assert starts[0]["t_launch_s"] < 0.2, starts[0]
    assert 0.1 < starts[1]["t_launch_s"] < 0.5, starts[1]  # ~150ms deadline
    assert len(cap.of("hedge_fired")) == 1
    assert cap.of("hedge_standdown") == []
    print("PASS test_hedge_slow_primary_fires_backups")


def test_hedge_orders_by_winners_log():
    tmp = tempfile.mkdtemp()
    log = os.path.join(tmp, "w.jsonl")
    seed_winners(log, "t-ord", "fast", n=3)
    race.WINNERS_LOG = log
    ordered = race._hedge_order("t-ord", make_strategies())  # cfg: slow,fast
    assert [s["name"] for s in ordered] == ["fast", "slow"], ordered
    print("PASS test_hedge_orders_by_winners_log")


def test_hedge_single_strategy_no_hedge_events():
    tmp = tempfile.mkdtemp()
    strats = [{"name": "only", "cmd": ["sh", "-c", "echo ONLY"],
               "match": "ONLY"}]
    (winner, _o, _t, _r), cap = run_race(
        strats, "t-one", os.path.join(tmp, "w.jsonl"), hedge_ms=200)
    assert winner == "only", winner
    assert cap.of("hedge_armed") == [] and cap.of("hedge_fired") == []
    print("PASS test_hedge_single_strategy_no_hedge_events")


if __name__ == "__main__":
    test_hedge_off_launches_all_at_once()
    test_hedge_fast_primary_backups_never_launch()
    test_hedge_slow_primary_fires_backups()
    test_hedge_orders_by_winners_log()
    test_hedge_single_strategy_no_hedge_events()
    print("ALL HEDGE TESTS PASS")
