"""Hidden acceptance tests for task-4-lru-cache.

HIDDEN from candidate strategies. Conforms to code-racer INTERFACE.md v1:
`from solution import LRUCache` works in the harness testbed (solution.py
sits flat next to this file).
"""
import random
import time

import pytest

from solution import LRUCache


def test_constructor_validation():
    with pytest.raises(ValueError):
        LRUCache(0)
    with pytest.raises(ValueError):
        LRUCache(-3)


def test_basic_put_get():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") == 1
    assert c.get("b") == 2
    assert len(c) == 2


def test_eviction_order():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")            # a now MRU; b is LRU
    c.put("c", 3)         # evicts b
    assert c.get("b") is None
    assert "b" not in c
    assert c.get("a") == 1
    assert c.get("c") == 3
    assert c.keys() == ["c", "a"]


def test_put_existing_key_updates_and_refreshes():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)         # MRU-first: [b, a]
    c.put("a", 10)        # update: a becomes MRU -> [a, b]
    assert c.keys() == ["a", "b"]
    c.put("c", 3)         # evicts b (LRU), not a -> [c, a]
    assert "b" not in c
    assert c.get("a") == 10   # get refreshes a -> [a, c]
    assert c.keys() == ["a", "c"]


def test_get_miss_returns_default_and_inserts_nothing():
    c = LRUCache(2)
    assert c.get("nope") is None
    assert c.get("nope", "dflt") == "dflt"
    assert len(c) == 0
    assert c.keys() == []


def test_contains_does_not_affect_recency():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)         # MRU-first: [b, a]
    c.get("a")            # refresh a -> [a, b]; b is now LRU
    assert ("b" in c) is True    # must NOT refresh b ...
    assert ("zzz" in c) is False
    c.put("c", 3)         # ... so b (still LRU) is evicted, not a
    assert "b" not in c
    assert c.get("a") == 1
    assert c.get("c") == 3


def test_capacity_one():
    c = LRUCache(1)
    c.put("a", 1)
    assert c.keys() == ["a"]
    c.put("b", 2)         # evicts a
    assert "a" not in c
    assert c.get("b") == 2
    c.put("b", 20)        # update, no eviction
    assert len(c) == 1
    assert c.get("b") == 20


def test_none_value_distinguishable_from_miss():
    c = LRUCache(2)
    c.put("a", None)
    assert "a" in c
    assert c.get("a") is None
    assert c.get("missing", "dflt") == "dflt"
    assert c.keys() == ["a"]


def test_keys_mru_first_after_mixed_ops():
    c = LRUCache(3)
    c.put(1, "x")
    c.put(2, "y")
    c.put(3, "z")
    c.get(1)              # order: 1, 3, 2
    c.get(2)              # order: 2, 1, 3
    assert c.keys() == [2, 1, 3]
    c.put(4, "w")         # evicts 3
    assert c.keys() == [4, 2, 1]


def test_various_key_types():
    c = LRUCache(3)
    c.put((1, 2), "tuple")
    c.put(42, "int")
    c.put(None, "none-key")
    assert c.get((1, 2)) == "tuple"
    assert c.get(42) == "int"
    assert c.get(None) == "none-key"
    assert len(c) == 3


def test_len_tracks_evictions():
    c = LRUCache(2)
    assert len(c) == 0
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)
    assert len(c) == 2


def test_correctness_against_reference_model():
    # Randomized differential test vs a simple OrderedDict-style model.
    from collections import OrderedDict
    rng = random.Random(1234)
    for capacity in (1, 2, 5):
        c = LRUCache(capacity)
        model = OrderedDict()
        for i in range(2000):
            op = rng.random()
            k = rng.randrange(8)
            if op < 0.5:
                v = rng.randrange(1000)
                c.put(k, v)
                if k in model:
                    del model[k]
                model[k] = v
                while len(model) > capacity:
                    model.popitem(last=False)
            elif op < 0.8:
                assert c.get(k, "MISS") == model.get(k, "MISS")
                if k in model:
                    model.move_to_end(k)
            else:
                assert (k in c) == (k in model)
            assert len(c) == len(model)
            assert c.keys() == list(reversed(model.keys()))


def test_performance_50k_ops():
    c = LRUCache(1000)
    start = time.monotonic()
    for i in range(50000):
        c.put(i % 1500, i)
        c.get(i % 1500)
    elapsed = time.monotonic() - start
    assert elapsed < 5.0, f"50k ops took {elapsed:.2f}s — likely not O(1)"
