"""Pattern 3: weighted score + weighted-random pick.

Factors (defaults): health 0.30, latency 0.25, quota 0.20,
cost_inv 0.15, stability 0.10. Selection is weighted-random over the
eligible set — avoids thundering herd on momentary-best.
"""
import random
import threading
from collections import deque

WEIGHTS = {"health": 0.30, "latency": 0.25, "quota": 0.20,
           "cost_inv": 0.15, "stability": 0.10}


class LatencyTracker:
    def __init__(self, window: int = 64):
        self._s = deque(maxlen=window)
        self._lock = threading.Lock()

    def record(self, ms: float):
        with self._lock:
            self._s.append(ms)

    def p95(self) -> float:
        with self._lock:
            if not self._s:
                return 9999.0
            v = sorted(self._s)
        return v[min(int(len(v) * 0.95), len(v) - 1)]

    def variance(self) -> float:
        with self._lock:
            if len(self._s) < 2:
                return 0.0
            v = list(self._s)
        m = sum(v) / len(v)
        return sum((x - m) ** 2 for x in v) / len(v)


def _norm(x: float, lo: float, hi: float) -> float:
    return max(0.0, min(1.0, (x - lo) / (hi - lo))) if hi > lo else 0.5


def score(*, health: float, p95_ms: float, variance: float,
          quota: float | None, is_free: bool) -> float:
    w = WEIGHTS
    q = quota if quota is not None else 1.0
    lat = 1.0 - _norm(p95_ms, 0, 3000)
    stab = 1.0 - _norm(variance, 0, 500_000)
    cost = 1.0 if is_free else 0.5
    return (w["health"] * health + w["latency"] * lat + w["quota"] * q
            + w["cost_inv"] * cost + w["stability"] * stab) / sum(w.values())


def weighted_pick(pairs: list[tuple[str, float]], *,
                  rng: random.Random | None = None) -> str | None:
    if not pairs:
        return None
    r = rng or random
    total = sum(max(0.0, w) for _, w in pairs)
    if total <= 0:
        return r.choice([n for n, _ in pairs])
    t = r.uniform(0, total)
    acc = 0.0
    for n, w in pairs:
        acc += max(0.0, w)
        if t <= acc:
            return n
    return pairs[-1][0]
