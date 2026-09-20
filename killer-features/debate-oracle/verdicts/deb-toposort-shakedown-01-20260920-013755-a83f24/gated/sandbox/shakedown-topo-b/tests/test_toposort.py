"""Hidden acceptance tests for toposort-shakedown-01 (debate-oracle e2e gate).
Debaters never saw these. Derived from tasks/shakedown-toposort/task.json spec.
"""
import itertools
import random

import pytest

from toposort import CycleError, topological_order


def test_basic_order():
    order = topological_order(["a", "b", "c"], [("a", "b"), ("b", "c")])
    assert order == ["a", "b", "c"]


def test_empty():
    assert topological_order([], []) == []


def test_disconnected():
    order = topological_order(["b", "a"], [])
    assert order == ["a", "b"]  # lex smallest by repr


def test_lex_smallest_tiebreak():
    # diamond: a->b, a->c, b->d, c->d ; valid orders: abcd, acbd -> abcd wins
    order = topological_order(["a", "b", "c", "d"],
                              [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")])
    assert order == ["a", "b", "c", "d"]


def test_duplicate_edges_ignored():
    order = topological_order(["a", "b"], [("a", "b"), ("a", "b")])
    assert order == ["a", "b"]


def test_unknown_node_raises():
    with pytest.raises(ValueError):
        topological_order(["a"], [("a", "zzz")])
    with pytest.raises(ValueError):
        topological_order(["a"], [("zzz", "a")])


def test_self_loop_cycle_shape():
    with pytest.raises(CycleError) as ei:
        topological_order(["a"], [("a", "a")])
    assert ei.value.cycle == ["a", "a"]


def _assert_real_cycle(cycle, edges):
    edge_set = set(edges)
    assert len(cycle) >= 2, "cycle too short: %r" % (cycle,)
    assert cycle[0] == cycle[-1], "first node not repeated at end: %r" % (cycle,)
    for u, v in zip(cycle, cycle[1:]):
        assert (u, v) in edge_set, "pair (%r, %r) is not an actual edge" % (u, v)


def test_real_cycle_reporting():
    edges = [("a", "b"), ("b", "c"), ("c", "a"), ("c", "d")]
    with pytest.raises(CycleError) as ei:
        topological_order(["a", "b", "c", "d"], edges)
    _assert_real_cycle(ei.value.cycle, edges)


def test_real_cycle_reporting_2():
    edges = [("x", "y"), ("y", "z"), ("z", "y")]
    with pytest.raises(CycleError) as ei:
        topological_order(["x", "y", "z"], edges)
    _assert_real_cycle(ei.value.cycle, edges)


def test_bruteforce_lex_minimal():
    rng = random.Random(42)
    for trial in range(30):
        n = rng.randint(2, 6)
        nodes = list(range(n))
        edges = [(u, v) for u in nodes for v in nodes
                 if u != v and rng.random() < 0.3]
        # skip cyclic graphs for the ordering check
        try:
            got = topological_order(nodes, edges)
        except CycleError:
            continue
        # brute force the lex-smallest valid order
        best = None
        for perm in itertools.permutations(nodes):
            pos = {x: i for i, x in enumerate(perm)}
            if all(pos[u] < pos[v] for u, v in edges):
                if best is None or perm < best:
                    best = perm
        assert best is not None
        assert list(got) == list(best), "trial %d: got %r want %r" % (trial, got, best)
