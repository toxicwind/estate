"""Token-bucket rate limiter.

There is a single planted bug in the refill path. Fix it so that the
acceptance tests pass. Do not change the public API.
"""
import time


class TokenBucket:
    def __init__(self, rate, capacity):
        if rate <= 0:
            raise ValueError("rate must be > 0")
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.rate = rate
        self.capacity = capacity
        self.tokens = float(capacity)
        self._last = time.monotonic()

    def _refill(self):
        now = time.monotonic()
        elapsed = int(now - self._last)
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self._last = now

    def take(self, n=1):
        if n < 0:
            raise ValueError("n must be >= 0")
        self._refill()
        if self.tokens >= n:
            self.tokens -= n
            return True
        return False

    @property
    def available(self):
        self._refill()
        return self.tokens
