#!/usr/bin/env python3
"""Nightjar cycle 4: integration verification of P2 (hedged attempt-2) in
the REAL bin/oracle_ask.py::_resilient_judge.

HEDGE_DELAY_S is monkeypatched down (40s -> 0.25s); everything else is the
production code path. Breaker state is isolated to a temp file (same
convention as bin/test_oracle_reliability.py).

Run on awrawr-pc:
  cd /home/toxic/sovereign/agents/oracle-market && python3 /tmp/hedge_integration.py
Exit 0 = all pass.
"""
import importlib.util
import os
import shutil
import sys
import tempfile
import time

BIN = "/home/toxic/sovereign/agents/oracle-market/bin"
sys.path.insert(0, BIN)
import engine  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "oracle_ask_under_test", os.path.join(BIN, "oracle_ask.py"))
_oa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_oa)

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print("ok   %s" % name)
    else:
        print("FAIL %s %s" % (name, detail))
        FAILURES.append(name)


_TARGETS = {"a": ["p1/x"], "b": ["p1/y"], "c": ["p2/z"],
            "oracle-judge-local": ["local/m"]}


def _mk_att(attempt_no, slot_alias, category, correlation_id=None):
    return engine.JudgeAttempt(
        attempt_no=attempt_no, slot_alias=slot_alias,
        failure_category=category, correlation_id=correlation_id)


def mk_plan_stub(plan, seen):
    """plan: {alias: (delay_s, outcome)}; outcome ok/timeout/http5xx."""
    def fn(alias, prompt, t, attempt_no=1, provider_requested=None,
           correlation_id=None):
        seen.append(alias)
        delay, outcome = plan[alias]
        time.sleep(delay)
        ok = outcome == "ok"
        cat = {"ok": engine.FAILURE_OK,
               "timeout": engine.FAILURE_TIMEOUT,
               "http5xx": engine.FAILURE_HTTP_5XX}[outcome]
        jp = engine.JudgePosterior(
            judge_id=alias, posterior=0.7 if ok else 0.5, valid=ok,
            failure_category=cat, provider=provider_requested)
        return jp, _mk_att(attempt_no, alias, cat, correlation_id)
    return fn


def resilient(model, plan, seen, panel=("a", "b", "c"), deadline=None,
              timeout_s=2):
    return _oa._resilient_judge(
        model, "p", timeout_s, judge_fn=mk_plan_stub(plan, seen),
        panel_aliases=list(panel), targets=_TARGETS,
        correlation_id="corr-int", deadline=deadline)


def test_hedge_fires_alternate_wins():
    seen = []
    t0 = time.time()
    jp, slot, attempts = resilient(
        "a", {"a": (0.6, "ok"), "c": (0.1, "ok")}, seen)
    wall = time.time() - t0
    check("int: hedge fired", slot["hedged"] is True, slot)
    check("int: alternate won", slot["served_by"] == "c", slot["served_by"])
    check("int: jp live", jp.live)
    check("int: both attempts ledgered", len(attempts) == 2, len(attempts))
    check("int: ledger attempt order",
          [a.attempt_no for a in attempts] == [1, 2])
    check("int: loser real outcome",
          attempts[0].slot_alias == "a"
          and attempts[0].failure_category == engine.FAILURE_OK)
    check("int: faster than sequential tail", wall < 1.5, round(wall, 3))
    check("int: json-safe slot", bool(__import__("json").dumps(slot)))


def test_no_hedge_fast_success():
    seen = []
    jp, slot, attempts = resilient("a", {"a": (0.05, "ok")}, seen)
    check("int: no hedge on fast success", slot["hedged"] is False)
    check("int: single attempt", len(attempts) == 1)
    check("int: served by a", slot["served_by"] == "a" and jp.live)
    check("int: stub saw only a", seen == ["a"], seen)


def test_no_hedge_fast_failure_sequential():
    seen = []
    jp, slot, attempts = resilient(
        "a", {"a": (0.05, "http5xx"), "c": (0.05, "ok")}, seen)
    check("int: no hedge on fast failure", slot["hedged"] is False)
    check("int: sequential cascade a->c", seen == ["a", "c"], seen)
    check("int: served by c", slot["served_by"] == "c" and jp.live)
    check("int: two attempts", len(attempts) == 2)


def test_hedge_fits_gated():
    seen = []
    jp, slot, attempts = resilient(
        "a", {"a": (0.6, "ok"), "c": (0.1, "ok")}, seen,
        deadline=time.time() - 1.0)  # P3: nothing fits
    check("int: no hedge when it can't fit", slot["hedged"] is False)
    check("int: primary result kept", jp.live and slot["served_by"] == "a")
    check("int: single attempt", len(attempts) == 1)
    check("int: stub saw only a", seen == ["a"], seen)


def test_hedge_double_failure_falls_to_fallback():
    seen = []
    jp, slot, attempts = resilient(
        "a", {"a": (0.6, "timeout"), "c": (0.1, "http5xx"),
              "oracle-judge-local": (0.05, "ok")}, seen)
    check("int: hedge fired", slot["hedged"] is True)
    check("int: fallback served", slot["served_by"] == "oracle-judge-local"
          and jp.live, slot["served_by"])
    check("int: three attempts, numbered",
          [a.attempt_no for a in attempts] == [1, 2, 3],
          [a.attempt_no for a in attempts])
    check("int: real categories",
          [a.failure_category for a in attempts] ==
          [engine.FAILURE_TIMEOUT, engine.FAILURE_HTTP_5XX,
           engine.FAILURE_OK])


def test_hedge_off_is_old_behavior():
    seen = []
    old_enabled, old_delay = _oa.HEDGE_ENABLED, _oa.HEDGE_DELAY_S
    _oa.HEDGE_ENABLED = False
    try:
        t0 = time.time()
        jp, slot, attempts = resilient("a", {"a": (0.6, "ok")}, seen)
        wall = time.time() - t0
    finally:
        _oa.HEDGE_ENABLED = old_enabled
    check("int: OFF -> hedged False", slot["hedged"] is False)
    check("int: OFF -> single attempt", len(attempts) == 1)
    check("int: OFF -> synchronous wait", wall >= 0.55, round(wall, 3))
    check("int: OFF -> jp live", jp.live and slot["served_by"] == "a")


def test_hedge_respects_open_breaker():
    # Trip p2's breaker (3 consecutive provider-class failures), then run
    # the hedge scenario: the hedge must NOT issue a call to c.
    bad = engine.JudgePosterior(judge_id="c", posterior=0.5, valid=False,
                                failure_category=engine.FAILURE_TIMEOUT,
                                provider="p2")
    for _ in range(3):
        _oa._breaker_record("p2", bad)
    check("int: p2 breaker open", not _oa._breaker_allows("p2"))
    seen = []
    jp, slot, attempts = resilient(
        "a", {"a": (0.6, "ok"), "c": (0.1, "ok")}, seen)
    check("int: hedge submitted but breaker-skipped",
          slot["hedged"] is True and "c" not in seen, seen)
    check("int: breaker skip ledgered",
          len(slot["breaker_skips"]) == 1, slot["breaker_skips"])
    check("int: primary won", jp.live and slot["served_by"] == "a")
    check("int: only attempt-1 in ledger", len(attempts) == 1,
          len(attempts))


def main():
    iso = tempfile.mkdtemp(prefix="oracle-hedge-int-")
    os.environ["JUDGE_BREAKER_PATH"] = os.path.join(
        iso, "judge-breaker-state.json")
    old_delay = _oa.HEDGE_DELAY_S
    _oa.HEDGE_DELAY_S = 0.25
    try:
        for fn in [test_hedge_fires_alternate_wins,
                   test_no_hedge_fast_success,
                   test_no_hedge_fast_failure_sequential,
                   test_hedge_fits_gated,
                   test_hedge_double_failure_falls_to_fallback,
                   test_hedge_off_is_old_behavior,
                   test_hedge_respects_open_breaker]:
            try:
                fn()
            except Exception as e:
                import traceback
                traceback.print_exc()
                print("FAIL %s raised %r" % (fn.__name__, e))
                FAILURES.append(fn.__name__)
    finally:
        _oa.HEDGE_DELAY_S = old_delay
        shutil.rmtree(iso, ignore_errors=True)
    print("---")
    if FAILURES:
        print("%d FAILURES: %s" % (len(FAILURES), ", ".join(FAILURES)))
        return 1
    print("integration clean: hedge works in the real _resilient_judge")
    return 0


if __name__ == "__main__":
    sys.exit(main())
