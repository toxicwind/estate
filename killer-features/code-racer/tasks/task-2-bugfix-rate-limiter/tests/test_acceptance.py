"""Hidden acceptance tests for task-2-bugfix-rate-limiter.

HIDDEN from candidate strategies. Conforms to code-racer INTERFACE.md v1:
the candidate's fixed module is collected as solution.py and sits flat next
to this file in the harness testbed.

Time is faked by monkeypatching time.monotonic, so tests are deterministic.
"""
import time

import pytest

import solution
from solution import TokenBucket


class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


@pytest.fixture()
def clock(monkeypatch):
    c = FakeClock()
    monkeypatch.setattr(time, "monotonic", c)
    monkeypatch.setattr(solution.time, "monotonic", c)
    return c


def test_starts_full(clock):
    b = TokenBucket(rate=10, capacity=5)
    assert b.available == 5.0


def test_burst_then_empty(clock):
    b = TokenBucket(rate=10, capacity=5)
    for _ in range(5):
        assert b.take() is True
    assert b.take() is False


def test_subsecond_refill(clock):
    # THE planted-bug test: int() truncation kills sub-second refill.
    b = TokenBucket(rate=10, capacity=10)
    for _ in range(10):
        assert b.take() is True
    assert b.take() is False
    clock.advance(0.25)          # 2.5 tokens should accrue
    assert b.take() is True
    assert b.take() is True
    assert b.take() is False     # only 0.5 token left


def test_fractional_tokens_accumulate(clock):
    b = TokenBucket(rate=4, capacity=10)
    assert b.take(10) is True
    clock.advance(0.5)           # 2.0 tokens
    assert b.take(2) is True
    assert b.take() is False


def test_refill_caps_at_capacity(clock):
    b = TokenBucket(rate=10, capacity=5)
    assert b.take(5) is True
    clock.advance(100.0)
    assert b.available == 5.0
    for _ in range(5):
        assert b.take() is True
    assert b.take() is False


def test_take_n_bulk(clock):
    b = TokenBucket(rate=10, capacity=10)
    assert b.take(4) is True
    assert b.take(7) is False    # only 6 left; consumes nothing
    assert b.take(6) is True
    assert b.take() is False


def test_take_more_than_capacity_never_succeeds(clock):
    b = TokenBucket(rate=10, capacity=5)
    assert b.take(6) is False
    clock.advance(60.0)
    assert b.take(6) is False
    assert b.available == 5.0


def test_take_zero_always_true(clock):
    b = TokenBucket(rate=10, capacity=5)
    assert b.take(5) is True
    assert b.take(0) is True
    assert b.take(0) is True
    assert b.available == 0.0


def test_take_negative_raises(clock):
    b = TokenBucket(rate=10, capacity=5)
    with pytest.raises(ValueError):
        b.take(-1)


def test_constructor_validation():
    with pytest.raises(ValueError):
        TokenBucket(rate=0, capacity=5)
    with pytest.raises(ValueError):
        TokenBucket(rate=-1, capacity=5)
    with pytest.raises(ValueError):
        TokenBucket(rate=10, capacity=0)


def test_last_refill_timestamp_advances(clock):
    b = TokenBucket(rate=10, capacity=5)
    t0 = b._last
    clock.advance(0.1)
    b.take()
    assert b._last > t0


def test_available_triggers_refill(clock):
    b = TokenBucket(rate=10, capacity=5)
    assert b.take(5) is True
    clock.advance(0.3)
    assert b.available == pytest.approx(3.0)
