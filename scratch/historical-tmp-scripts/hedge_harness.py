#!/usr/bin/env python3
"""Standalone race harness for nightjar P2 (hedged attempt-2) — cycle 4.

Proves the hedge algorithm BEFORE it touches bin/oracle_ask.py:
  1. slow-primary + fast-alternate  -> hedge fires, first success wins
  2. alternate-fails               -> loser ledgered with its real outcome
  3. both-timeout                  -> bounded termination (no hang)
  4. primary fast success          -> NO hedge (tail-only gate)
  5. primary fast failure          -> NO hedge (sequential cascade owns it)
  6. no alternate provider         -> NO hedge, wait out attempt-1
  7. hedge raises                  -> guard: primary's good result survives
  8. _fits False (P3 gate)         -> NO hedge

Time scale is compressed (HEDGE_DELAY_S=0.25 stands in for the 40s
production gate); the algorithm is a faithful copy of the planned
integration, including the defensive outer bound in _resolve_hedge.

Run on awrawr-pc:  python3 /tmp/hedge_harness.py
Exit 0 = all scenarios pass, 1 = failures.
"""
import concurrent.futures as cf
import sys
import time

sys.path.insert(0, "/home/toxic/sovereign/agents/oracle-market/bin")
import engine

HEDGE_DELAY_S = 0.25  # scaled stand-in for the 40s production tail gate
T1 = 1.0              # scaled attempt-1 timeout
T2 = 0.5              # scaled attempt-2 timeout

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print("ok   %s" % name)
    else:
        print("FAIL %s %s" % (name, detail))
        FAILURES.append(name)


# ---------------------------------------------------------------------------
# Algorithm under test (faithful copy of the planned oracle_ask.py integration)
# ---------------------------------------------------------------------------

def _synth_hedge_exception(alias, attempt_no, exc, provider_of, correlation_id):
    """A judge_fn that RAISED inside the hedge race (contract violation)
    becomes a real, non-live attempt record — the other attempt's outcome
    must survive. Returns (jp, att)."""
    preq = provider_of(alias)
    jp = engine.JudgePosterior(judge_id=alias, posterior=0.5, refused=False,
                               valid=False,
                               failure_category=engine.FAILURE_UNKNOWN,
                               provider=preq)
    jp.error = "hedge-race exception: %r" % (exc,)
    att = engine.JudgeAttempt(
        attempt_no=attempt_no, slot_alias=alias, provider_requested=preq,
        correlation_id=correlation_id, failure_category=engine.FAILURE_UNKNOWN,
        error_excerpt="hedge-race exception: %r" % (exc,))
    return jp, att


def _resolve_hedge(futures, slot_alias, timeout_s, t2):
    """Drain a hedged attempt pair; first LIVE success wins.

    futures: {future: (alias, attempt_no)}. Both are internally
    timeout-bounded by their own _call timeouts (judge_fn contract), so
    the drain always terminates; `bound` is a defensive outer bound only.
    Returns (jp, served_by, synth) where synth = [(alias, no, exc)] for
    futures that raised instead of returning.
    """
    pending = dict(futures)
    order = []  # (alias, attempt_no, jp-or-exc) in completion order
    winner_alias, winner_jp = None, None
    bound = max(5.0, timeout_s + t2 + 10.0)
    t_end = time.time() + bound
    while pending:
        rem = t_end - time.time()
        if rem <= 0:
            break
        done, _ = cf.wait(list(pending), timeout=rem,
                          return_when=cf.FIRST_COMPLETED)
        if not done:
            break
        for f in done:
            alias, no = pending.pop(f)
            try:
                res = f.result()
            except Exception as e:  # judge_fn contract says never; be safe
                res = e
            order.append((alias, no, res))
            if (winner_alias is None and not isinstance(res, Exception)
                    and getattr(res, "live", False)):
                winner_alias, winner_jp = alias, res
    synth = [(a, n, r) for (a, n, r) in order if isinstance(r, Exception)]
    if winner_alias is not None:
        return winner_jp, winner_alias, synth
    usable = [(a, n, r) for (a, n, r) in order
              if not isinstance(r, Exception)]
    if usable:
        # No live winner: the last completed outcome is the working
        # result (same shape as the sequential cascade, where jp ends as
        # attempt-2's outcome). served_by stays the slot alias.
        return usable[-1][2], slot_alias, synth
    return None, slot_alias, synth  # pathological: contract violated


def run_slot(model, panel, provider_of, call, fits, correlation_id="corr-h",
             timeout_s=T1, t2=T2):
    """Driver mirroring the planned _resilient_judge head. Returns a dict."""
    attempts = []
    hedged = False
    t0 = time.time()
    jp, served_by = None, model
    with cf.ThreadPoolExecutor(max_workers=2) as hex_:
        f1 = hex_.submit(call, model, timeout_s, 1, attempts)
        try:
            jp = f1.result(timeout=HEDGE_DELAY_S)
        except cf.TimeoutError:
            prov = provider_of(model)
            alt = next((a for a in panel
                        if a != model
                        and provider_of(a) not in (prov, "unknown")), None)
            if alt is not None and fits(t2):
                hedged = True
                fh = hex_.submit(call, alt, t2, 2, attempts)
                wjp, walias, synth = _resolve_hedge(
                    {f1: (model, 1), fh: (alt, 2)}, model, timeout_s, t2)
                for (a, n, exc) in synth:
                    sjp, satt = _synth_hedge_exception(
                        a, n, exc, provider_of, correlation_id)
                    attempts.append(satt)
                    if wjp is None:
                        wjp = sjp
                jp, served_by = wjp, walias
            else:
                jp = f1.result()  # bounded by the stub's own behavior
    attempts.sort(key=lambda a: a.attempt_no)
    return {"jp": jp, "served_by": served_by, "attempts": attempts,
            "hedged": hedged, "wall_s": time.time() - t0}


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

def mk_provider_of(mapping):
    return lambda alias: mapping.get(alias, "unknown")


def mk_call(judge_fn, provider_of, correlation_id="corr-h"):
    """Mimics _call's tuple branch: appends the attempt record, returns jp."""
    def call(alias, t, no, attempts):
        jp, att = judge_fn(alias, "p", t, attempt_no=no,
                           provider_requested=provider_of(alias),
                           correlation_id=correlation_id)
        attempts.append(att)
        if not getattr(jp, "provider", None):
            jp.provider = att.provider_requested
        return jp
    return call


def mk_judge_fn(plan):
    """plan: {alias: (delay_s, outcome)}; outcome in ok/timeout/http5xx/raise."""
    def fn(alias, prompt, t, attempt_no=1, provider_requested=None,
           correlation_id=None):
        delay, outcome = plan[alias]
        time.sleep(delay)
        if outcome == "raise":
            raise RuntimeError("boom from %s" % alias)
        ok = outcome == "ok"
        cat = {  # noqa: E731
            "ok": engine.FAILURE_OK,
            "timeout": engine.FAILURE_TIMEOUT,
            "http5xx": engine.FAILURE_HTTP_5XX,
        }[outcome]
        att = engine.JudgeAttempt(
            attempt_no=attempt_no, slot_alias=alias,
            provider_requested=provider_requested, correlation_id=correlation_id,
            failure_category=cat, latency_s=delay)
        jp = engine.JudgePosterior(
            judge_id=alias, posterior=0.7 if ok else 0.5,
            valid=ok, failure_category=cat, provider=provider_requested)
        return jp, att
    return fn


PROV = {"a": "p1", "b": "p1", "c": "p2", "oracle-judge-local": "local"}


def run_case(name, model, panel, plan, fits=True):
    provider_of = mk_provider_of(PROV)
    call = mk_call(mk_judge_fn(plan), provider_of)
    return run_slot(model, panel, provider_of, call,
                    fits=(lambda t: fits), correlation_id="corr-" + name)


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

def s1_slow_primary_fast_alternate():
    """Tail: primary slow-but-ok, alternate fast-ok -> hedge fires,
    first success (alternate) wins, primary's real outcome ledgered."""
    r = run_case("s1", "a", ["a", "b", "c"],
                 {"a": (0.6, "ok"), "c": (0.1, "ok")})
    check("s1: hedge fired", r["hedged"])
    check("s1: alternate won", r["served_by"] == "c", r["served_by"])
    check("s1: jp live", r["jp"].live)
    check("s1: both attempts ledgered", len(r["attempts"]) == 2,
          len(r["attempts"]))
    check("s1: ledger in attempt order",
          [a.attempt_no for a in r["attempts"]] == [1, 2])
    check("s1: loser has real outcome",
          r["attempts"][0].failure_category == engine.FAILURE_OK
          and r["attempts"][0].slot_alias == "a")
    check("s1: faster than sequential tail (wall<1.2s)",
          r["wall_s"] < 1.2, round(r["wall_s"], 3))


def s2_alternate_fails():
    """Primary slow-timeout, alternate fast-5xx -> no winner; both
    failures ledgered with their REAL categories (not phantom skips)."""
    r = run_case("s2", "a", ["a", "b", "c"],
                 {"a": (0.6, "timeout"), "c": (0.1, "http5xx")})
    check("s2: hedge fired", r["hedged"])
    check("s2: no winner -> jp not live", not r["jp"].live)
    check("s2: both attempts ledgered", len(r["attempts"]) == 2)
    cats = {a.slot_alias: a.failure_category for a in r["attempts"]}
    check("s2: real categories kept", cats == {
        "a": engine.FAILURE_TIMEOUT, "c": engine.FAILURE_HTTP_5XX}, cats)
    check("s2: bounded (wall<1.5s)", r["wall_s"] < 1.5,
          round(r["wall_s"], 3))


def s3_both_timeout():
    """Both attempts time out -> drain terminates, no hang."""
    r = run_case("s3", "a", ["a", "b", "c"],
                 {"a": (0.7, "timeout"), "c": (0.5, "timeout")})
    check("s3: hedge fired", r["hedged"])
    check("s3: no live winner", not r["jp"].live)
    check("s3: both ledgered as timeout",
          [a.failure_category for a in r["attempts"]] ==
          [engine.FAILURE_TIMEOUT] * 2)
    check("s3: no hang (wall<2.0s)", r["wall_s"] < 2.0,
          round(r["wall_s"], 3))


def s4_primary_fast_success():
    """Primary answers fast -> tail gate never fires, single attempt."""
    r = run_case("s4", "a", ["a", "b", "c"], {"a": (0.05, "ok")})
    check("s4: no hedge", not r["hedged"])
    check("s4: single attempt", len(r["attempts"]) == 1)
    check("s4: served by a", r["served_by"] == "a" and r["jp"].live)


def s5_primary_fast_failure():
    """Primary fails fast -> NO hedge; the sequential cascade owns
    fast failures (hedge is tail-only)."""
    r = run_case("s5", "a", ["a", "b", "c"], {"a": (0.05, "http5xx")})
    check("s5: no hedge on fast failure", not r["hedged"])
    check("s5: attempt-1 only here", len(r["attempts"]) == 1)
    check("s5: jp not live", not r["jp"].live)


def s6_no_alternate_provider():
    """Only same-provider aliases -> nothing to hedge with; attempt-1
    is waited out, sequential path takes over."""
    r = run_case("s6", "a", ["a", "b"], {"a": (0.6, "ok")})
    check("s6: no hedge (no alternate)", not r["hedged"])
    check("s6: primary result kept", r["jp"].live and r["served_by"] == "a")
    check("s6: single attempt", len(r["attempts"]) == 1)


def s7_hedge_raises():
    """Alternate explodes -> guard converts it to a real attempt record;
    primary's good result survives (sequential path would have kept it)."""
    r = run_case("s7", "a", ["a", "b", "c"],
                 {"a": (0.6, "ok"), "c": (0.1, "raise")})
    check("s7: hedge fired", r["hedged"])
    check("s7: primary won", r["served_by"] == "a" and r["jp"].live,
          r["served_by"])
    check("s7: loser ledgered as real attempt",
          len(r["attempts"]) == 2
          and r["attempts"][1].failure_category == engine.FAILURE_UNKNOWN
          and "hedge-race exception" in (r["attempts"][1].error_excerpt or ""),
          [a.failure_category for a in r["attempts"]])
    check("s7: no exception escaped", True)


def s8_fits_gate():
    """P3 _fits False -> hedge never issued even in the tail."""
    r = run_case("s8", "a", ["a", "b", "c"],
                 {"a": (0.6, "ok"), "c": (0.1, "ok")}, fits=False)
    check("s8: no hedge when it can't fit", not r["hedged"])
    check("s8: primary result kept", r["jp"].live and r["served_by"] == "a")
    check("s8: single attempt", len(r["attempts"]) == 1)


def main():
    t0 = time.time()
    for fn in [s1_slow_primary_fast_alternate, s2_alternate_fails,
               s3_both_timeout, s4_primary_fast_success,
               s5_primary_fast_failure, s6_no_alternate_provider,
               s7_hedge_raises, s8_fits_gate]:
        try:
            fn()
        except Exception as e:
            import traceback
            traceback.print_exc()
            print("FAIL %s raised %r" % (fn.__name__, e))
            FAILURES.append(fn.__name__)
    wall = time.time() - t0
    check("harness: global no-hang (wall<30s)", wall < 30, round(wall, 2))
    print("---")
    if FAILURES:
        print("%d FAILURES: %s" % (len(FAILURES), ", ".join(FAILURES)))
        return 1
    print("harness clean: all hedge race scenarios pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
