"""Bidder profiles for the e2e batch.

Each profile models a distinct bidder "species" in the pool:
  caps      - which task kinds the bidder can execute
  delay_s   - real seconds of simulated bidder latency added around real
              execution (models speed: fast bidders finish sooner)
  fail_rate - real injected failure probability (models unreliability)

The ORACLE (ground truth for allocation quality): for a task, the
best-suited bidder is the eligible bidder (requires ⊆ caps) with the
smallest delay_s. With this pool the oracle is unambiguous:
  python tasks -> py-nitro,  shell tasks -> sh-nitro.
py-steady is the "slow generalist" trap: eligible for everything, best
at nothing. flaky-py tests failure/re-auction handling. sh-slow tests
whether the market avoids a slow specialist.
"""

PROFILES = {
    "py-nitro":  {"caps": {"python"},         "delay_s": 0.3, "fail_rate": 0.0},
    "sh-nitro":  {"caps": {"shell"},          "delay_s": 0.3, "fail_rate": 0.0},
    "py-steady": {"caps": {"python", "shell"}, "delay_s": 1.5, "fail_rate": 0.0},
    "sh-slow":   {"caps": {"shell"},          "delay_s": 4.0, "fail_rate": 0.0},
    "flaky-py":  {"caps": {"python"},         "delay_s": 0.6, "fail_rate": 0.25},
}

POOL = ["py-nitro", "sh-nitro", "py-steady", "sh-slow", "flaky-py"]


def eligible(task):
    req = set(task["requires"])
    return [n for n in POOL if req <= PROFILES[n]["caps"]]


def oracle_best(task):
    """Ground-truth best-suited bidder for allocation-quality scoring."""
    return min(eligible(task), key=lambda n: PROFILES[n]["delay_s"])
