# Task 2 — Fix the Rate Limiter

A token-bucket rate limiter in `rate_limiter.py` has a **single planted bug**.
Your job: find it and fix it.

**Deliverable:** write the corrected module to `solution.py` (this is the file
the harness collects and tests — `from solution import TokenBucket` must work).

## Expected behavior (the spec)

`TokenBucket(rate, capacity)`:

- `rate`: tokens added per second (float, must be > 0).
- `capacity`: maximum tokens the bucket can hold (int, must be >= 1).
- The bucket starts full (`tokens == capacity`).
- `take(n=1)`:
  - First refills the bucket based on time elapsed since the last refill.
  - If at least `n` tokens are available, consumes `n` and returns `True`.
  - Otherwise consumes nothing and returns `False`.
  - `take(0)` always returns `True` (consumes nothing).
  - Raises `ValueError` if `n < 0`.
- Refill is **continuous**: after `t` seconds, `t * rate` tokens are added (fractional tokens are fine — the bucket tracks a float internally), capped at `capacity`.
- `available` property returns the current token count (after refilling).

## The bug

Something in the refill path is wrong. The existing code passes a quick smoke test
(full bucket allows a burst), but the hidden acceptance tests exercise sub-second
refill timing and will fail until the bug is fixed.

## Rules

- Fix the bug with a minimal change; do not rewrite the class.
- Only the standard library may be used.
- Do not change the public API (`__init__`, `take`, `available`).
- Resource limits: `limits.json` in this directory.
