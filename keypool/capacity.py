"""Pattern 4: per-key inflight counter for spread-then-stack.

optimal is a soft target, max is a hard ceiling. Balanced mode: prefer
keys under optimal; overflow stacks on healthy keys up to max.
Sticky mode (optimal=max=1): single concurrent request per key.
"""
import threading


class Capacity:
    def __init__(self, optimal: int = 2, maximum: int = 8):
        self.optimal = optimal
        self.maximum = maximum
        self._inflight: dict[str, int] = {}
        self._lock = threading.Lock()

    def inflight(self, name: str) -> int:
        with self._lock:
            return self._inflight.get(name, 0)

    def try_acquire(self, name: str) -> bool:
        with self._lock:
            cur = self._inflight.get(name, 0)
            if cur >= self.maximum:
                return False
            self._inflight[name] = cur + 1
            return True

    def release(self, name: str):
        with self._lock:
            cur = self._inflight.get(name, 0)
            if cur > 0:
                self._inflight[name] = cur - 1

    def utilization(self, name: str) -> float:
        return self.inflight(name) / max(1, self.maximum)
