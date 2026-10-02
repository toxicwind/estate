"""P3 functional test (runs on awrawr-pc, no network): stub judge_fn that
always fails fast with a provider-class failure, so the retry cascade
would normally issue attempt-2 (alt provider) + fallback."""
import sys
import time

sys.path.insert(0, "/home/toxic/sovereign/agents/oracle-market/bin")
import oracle_ask as oa
import engine

TARGETS = {"a": ["p1/x"], "c": ["p2/z"], "oracle-judge-local": ["local/m"]}
seen = []


def fail_stub(alias, prompt, t, attempt_no=1, provider_requested=None,
              correlation_id=None):
    seen.append((alias, attempt_no))
    jp = engine.JudgePosterior(
        judge_id=alias, posterior=0.5, refused=False, valid=False,
        failure_category=engine.FAILURE_TIMEOUT, provider=provider_requested)
    att = engine.JudgeAttempt(
        attempt_no=attempt_no, slot_alias=alias,
        provider_requested=provider_requested,
        failure_category=engine.FAILURE_TIMEOUT, correlation_id=correlation_id)
    return jp, att


def run(deadline):
    seen.clear()
    return oa._resilient_judge(
        "a", "p", 10, judge_fn=fail_stub,
        panel_aliases=["a", "c"], targets=TARGETS,
        correlation_id="p3t", deadline=deadline)


# 1. deadline already past: attempt-1 fires, attempt-2 + fallback skipped
jp, slot, attempts = run(time.time() - 1.0)
assert seen == [("a", 1)], seen
assert len(attempts) == 1, [a.attempt_no for a in attempts]
assert len(slot["budget_skips"]) == 2, slot["budget_skips"]
assert {s["alias"] for s in slot["budget_skips"]} == {"c", "oracle-judge-local"}
assert all(s["remaining_budget_s"] <= 0.0 for s in slot["budget_skips"])
print("P3 past-deadline: OK — skipped alt+fallback, kept attempt-1 evidence")

# 2. deadline=None (old signature path): unchanged behavior, no skips
jp, slot, attempts = run(None)
assert seen == [("a", 1), ("c", 2), ("oracle-judge-local", 3)], seen
assert slot["budget_skips"] == [], slot["budget_skips"]
assert len(attempts) == 3
print("P3 deadline=None: OK — old path preserved, zero skips")

# 3. generous deadline: everything issued, no skips
jp, slot, attempts = run(time.time() + 1000.0)
assert seen == [("a", 1), ("c", 2), ("oracle-judge-local", 3)], seen
assert slot["budget_skips"] == [], slot["budget_skips"]
print("P3 generous deadline: OK — all attempts issued")

# 4. tight-but-nonzero budget: attempt-2 fits (10s < 30s), fallback skipped
jp, slot, attempts = run(time.time() + 30.0)
assert seen == [("a", 1), ("c", 2)], seen
assert len(slot["budget_skips"]) == 1, slot["budget_skips"]
assert slot["budget_skips"][0]["alias"] == "oracle-judge-local"
assert slot["budget_skips"][0]["planned_timeout_s"] == 120.0
print("P3 partial budget: OK — attempt-2 issued, 120s fallback skipped")

# 5. slot_info stays JSON-serializable (main() dumps the verdict on stdout)
import json
json.dumps(slot)
print("P3 slot_info JSON-safe: OK")
print("ALL P3 FUNCTIONAL TESTS PASSED")
