"""Pattern 8: abort-aware backoff.

Exponential with ±25% jitter to de-correlate storms. Sleep uses
threading.Event.wait so it wakes early when the client disconnects
(event is set by the caller).
"""
import random
import threading


def sleep_abortable(seconds: float, abort: threading.Event,
                    granularity: float = 0.25) -> bool:
    end = __import__("time").monotonic() + seconds
    while True:
        rem = end - __import__("time").monotonic()
        if rem <= 0:
            return True
        if abort.wait(min(granularity, rem)):
            return False


def backoff(attempt: int, *, initial: float = 0.5, cap: float = 30.0,
            jitter: float = 0.25, rng: random.Random | None = None) -> float:
    r = rng or random
    base = min(initial * (2 ** attempt), cap)
    return base * r.uniform(1.0 - jitter, 1.0 + jitter)
