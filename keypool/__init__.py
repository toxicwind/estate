"""keypool — modular API-key rotation proxy for LLM providers.

Thirteen patterns; each its own module:

  1  ratelimit.py   proactive guard: preempt before 429
  2  circuit.py     CLOSED / OPEN / HALF_OPEN per pool
  3  scoring.py     weighted score, weighted-random selection
  4  capacity.py    inflight tracking; spread-then-stack
  5  affinity.py    session -> key stickiness (prompt cache)
  6  errors.py      SWITCH / SURFACE / SOFT taxonomy
  7  ratelimit.py   Retry-After + x-ratelimit-reset parsing
  8  backoff.py     abort-aware exponential backoff with jitter
  9  clock.py       monotonic time for all intervals
 10  persist.py     atomic JSON (temp + os.replace)
 11  affinity.py    session GC + orphan sweep
 12  proxy.py       cross-provider cascade
 13  alerts.py      non-blocking webhook queue

See README.md next to this file.
"""
__version__ = "3.0.0"
