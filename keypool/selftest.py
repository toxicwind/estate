"""Self-test: patterns in isolation, no network."""
import random
import sys
import time


def run() -> int:
    from . import (affinity, backoff, circuit, clock, errors, persist,
                   ratelimit, scoring, state)
    import tempfile, os, json
    fails = 0

    # Pattern 9: monotonic is monotonic
    a = clock.mono(); b = clock.mono()
    assert b >= a, "monotonic clock went backwards"
    print("  pattern 9  clock          OK")

    # Pattern 6: error taxonomy
    assert errors.classify(401, fail_status=frozenset({401})) == "switch"
    assert errors.classify(400, surface_codes=frozenset({400})) == "surface"
    assert errors.classify(0, exception=TimeoutError()) == "soft"
    assert errors.classify(503, fail_status=frozenset({503})) == "switch"
    print("  pattern 6  errors         OK")

    # Pattern 7: header parsing
    assert ratelimit.parse_retry_after("30") == 30.0
    assert ratelimit.parse_duration("6m0s") == 360.0
    assert ratelimit.parse_duration("500ms") == 0.5
    assert ratelimit.parse_epoch_or_iso("") is None
    print("  pattern 7  ratelimit      OK")

    # Pattern 1: preemption
    lim = ratelimit.Limit(remaining=1, reset_at=10.0)
    assert ratelimit.should_preempt(lim, floor=2, window=30) is True
    lim2 = ratelimit.Limit(remaining=50, reset_at=10.0)
    assert ratelimit.should_preempt(lim2, floor=2, window=30) is False
    print("  pattern 1  preempt        OK")

    # Pattern 2: circuit breaker
    cb = circuit.Circuit(failure_threshold=2, recovery_timeout=0.2)
    assert cb.state == "closed"
    cb.record_failure(); cb.record_failure()
    assert cb.state == "open"
    assert cb.allow_request() is False
    time.sleep(0.25)
    assert cb.allow_request() is True
    assert cb.state == "half_open"
    cb.record_success()
    assert cb.state == "closed"
    print("  pattern 2  circuit        OK")

    # Pattern 3: weighted pick is statistical
    r = random.Random(7)
    picks = [scoring.weighted_pick([("a", 1.0), ("b", 4.0)], rng=r) for _ in range(300)]
    assert picks.count("b") > picks.count("a") * 2
    print("  pattern 3  scoring        OK")

    # Pattern 5 + 11: affinity TTL and GC
    am = affinity.AffinityMap(ttl=0.05)
    am.bind("s1", "k1")
    assert am.get("s1") == "k1"
    time.sleep(0.1)
    assert am.get("s1") is None
    am.bind("s2", "k2"); am.gc()
    assert am.size() == 1, am.size()
    print("  pattern 5  affinity       OK")

    # Pattern 8: backoff bounds
    for n in range(6):
        v = backoff.backoff(n, initial=0.5, cap=30.0)
        assert 0 < v <= 30 * 1.3, f"backoff out of range: {v}"
    print("  pattern 8  backoff        OK")

    # Pattern 10: atomic write
    d = tempfile.mkdtemp()
    p = os.path.join(d, "x.json")
    persist.write_json(p, {"a": 1})
    assert persist.read_json(p) == {"a": 1}
    with open(p, "w") as f:
        f.write("not json")
    assert persist.read_json(p, default={}) == {}
    print("  pattern 10 persist        OK")

    # State: park / revive
    ks = state.KeyState("K", "fake", free_only=False)
    ks.park(1.0, "test")
    assert ks.is_parked()
    ks.revive()
    assert not ks.is_parked()
    print("  state      KeyState       OK")

    print(f"selftest: {'ALL PASS' if not fails else str(fails) + ' FAILURES'}")
    return fails


if __name__ == "__main__":
    sys.exit(run())
