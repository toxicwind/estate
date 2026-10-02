#!/usr/bin/env python3
"""Nightjar cycle 4: integrate P2 (hedged attempt-2) into oracle_ask.py.

Applies 4 additive edits; asserts each anchor occurs exactly once.
Run on awrawr-pc. Idempotent guard: refuses to run twice.
"""
import sys

P = "/home/toxic/sovereign/agents/oracle-market/bin/oracle_ask.py"
src = open(P).read()

if "HEDGE_ENABLED" in src:
    print("already integrated; refusing to run twice")
    sys.exit(2)


def rep(old, new):
    global src
    n = src.count(old)
    assert n == 1, "anchor occurs %d times: %r" % (n, old[:70])
    src = src.replace(old, new)


# --- Edit 1: module-level hedge constants, next to FALLBACK_JUDGE ---
rep('FALLBACK_JUDGE = "oracle-judge-local"  # local last resort, router-owned\n',
    '''FALLBACK_JUDGE = "oracle-judge-local"  # local last resort, router-owned

# P2 (nightjar cycle 4): hedged attempt-2 for judge calls — Dean & Barroso,
# "The Tail at Scale"; Envoy HedgePolicy. When attempt-1 is still
# outstanding after HEDGE_DELAY_S, fire ONE attempt-2 on an ALTERNATE
# provider in parallel; first success wins, the loser is ledgered as a
# normal attempt with its real outcome. Guards: tail-only (below the 60s
# attempt-2 timeout floor), max one hedge, alternate provider only, gated
# by P3's _fits() against the ask deadline. HEDGE_ENABLED=False restores
# the exact pre-hedge sequential behavior (attempt-1 runs synchronously).
# Default ON: the 40s tail gate makes it ~2%-extra-load per the paper, the
# common path (<40s) is untouched, and the existing 73-check suite never
# reaches the tail with its fast stubs.
HEDGE_ENABLED = True
HEDGE_DELAY_S = 40.0  # ~p95 of observed free-tier judge latency; tail-only
''')

# --- Edit 2: hedge helpers, just before _resilient_judge ---
rep("def _resilient_judge(model, prompt, timeout_s, judge_fn=None,\n",
    '''def _synth_hedge_exception(alias, attempt_no, exc, targets,
                           correlation_id):
    """A judge_fn that RAISED inside a hedge race (contract violation:
    herd_chat/judge_once never raise) becomes a real, non-live attempt
    record — the other attempt's outcome must survive. Without this, a
    hedge that explodes while attempt-1 later succeeds would sink the
    good result, a hazard the sequential path never had."""
    preq = provider_of_alias(alias, targets)
    jp = engine.JudgePosterior(judge_id=alias, posterior=0.5, refused=False,
                               valid=False,
                               failure_category=engine.FAILURE_UNKNOWN,
                               provider=preq)
    jp.error = "hedge-race exception: %r" % (exc,)
    att = engine.JudgeAttempt(
        attempt_no=attempt_no, slot_alias=alias, provider_requested=preq,
        correlation_id=correlation_id,
        failure_category=engine.FAILURE_UNKNOWN,
        error_excerpt="hedge-race exception: %r" % (exc,))
    return jp, att


def _resolve_hedge(futures, slot_alias, timeout_s, t2):
    """Drain a hedged attempt pair; first LIVE success wins.

    futures: {future: (alias, attempt_no)}, both submitted via
    _call_or_skip and therefore internally timeout-bounded by their own
    timeouts (timeout_s for attempt-1, t2 for the hedge) under the
    judge_fn contract — the drain always terminates. `bound` is a defensive outer
    bound only, for a judge_fn that violates its timeout contract (the
    old synchronous _call would hang outright in that case; this is
    strictly more robust).

    Returns (jp, served_by, synth): the winning live posterior (or, with
    no live winner, the last completed outcome — same shape as the
    sequential cascade where jp ends as attempt-2's outcome), the alias
    that served it (slot_alias when nobody did), and [(alias, no, exc)]
    for futures that raised instead of returning.
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
            except Exception as e:  # contract says never; be safe
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
        return usable[-1][2], slot_alias, synth
    # Pathological (contract violated, nothing completed inside the
    # bound): the caller synthesizes attempt-1 as a timeout, mirroring
    # what judge_once would have returned at its internal timeout.
    return None, slot_alias, synth


def _resilient_judge(model, prompt, timeout_s, judge_fn=None,
''')

# --- Edit 3: docstring gains the hedge paragraph (after the P1 paragraph) ---
rep("""    behavior (breaker disabled).
    \"\"\"
""",
    """    behavior (breaker disabled).

    P2 hedge (HEDGE_ENABLED): if attempt-1 is still outstanding after
    HEDGE_DELAY_S (tail-only, below the 60s attempt-2 floor), ONE
    attempt-2 fires on an alternate provider in parallel — never the same
    alias — via _call_or_skip (so an OPEN breaker on the alternate
    provider still converts it to a ledgered skip, never a wasted call),
    gated by _fits(t2) against the ask deadline. First live success wins;
    the loser is ledgered as a normal attempt with its real outcome
    (attempts are re-sorted by attempt_no afterwards, preserving the
    ledger invariant engine.classify_failures relies on). A hedged
    attempt-2 counts as attempt-2: the sequential cascade is skipped, and
    a double failure falls through to the local fallback as attempt-3.
    \"\"\"
""")

# --- Edit 4: the attempt-1 head becomes hedge-aware (breaker-aware: the
# hedge is issued via _call_or_skip so an OPEN alternate-provider breaker
# still converts it to a ledgered skip, never a wasted call) ---
rep("""    jp = _call_or_skip(model, timeout_s, 1)
    served_by = model
    if not jp.live:
""",
    """    jp = None
    served_by = model
    hedged = False  # True once the hedged attempt-2 has been issued
    if not HEDGE_ENABLED:
        jp = _call_or_skip(model, timeout_s, 1)  # exact pre-hedge behavior
    else:
        # P2: hedged attempt-2 (Tail at Scale / Envoy HedgePolicy).
        # Attempt-1 runs in a small pool so the tail gate can fire
        # without blocking the slot thread; the pool is joined on exit.
        # Every submitted call is internally timeout-bounded by its own
        # _call timeout (judge_fn contract), so the join always
        # terminates — the same guarantee the old synchronous _call had.
        with cf.ThreadPoolExecutor(max_workers=2,
                                   thread_name_prefix="nightjar-hedge") as hex_:
            f1 = hex_.submit(_call_or_skip, model, timeout_s, 1)
            try:
                jp = f1.result(timeout=HEDGE_DELAY_S)
            except cf.TimeoutError:
                # Tail: attempt-1 still outstanding past the hedge gate.
                alt = next((a for a in panel
                            if a != model and a != FALLBACK_JUDGE
                            and provider_of_alias(a, targets)
                            not in (prov, "unknown")), None)
                if alt is not None and _fits(t2):
                    hedged = True
                    fh = hex_.submit(_call_or_skip, alt, t2, 2)
                    wjp, walias, synth = _resolve_hedge(
                        {f1: (model, 1), fh: (alt, 2)}, model,
                        timeout_s, t2)
                    for (sa, sn, exc) in synth:
                        sjp, satt = _synth_hedge_exception(
                            sa, sn, exc, targets, correlation_id)
                        attempts.append(satt)
                        if wjp is None:
                            wjp = sjp
                    if wjp is None:
                        # Pathological: the drain's defensive bound
                        # tripped with nothing completed (judge_fn
                        # violated its timeout contract). Synthesize
                        # attempt-1 as a timeout so the slot degrades to
                        # the sequential cascade instead of crashing.
                        wjp = engine.JudgePosterior(
                            judge_id=model, posterior=0.5, refused=False,
                            valid=False,
                            failure_category=engine.FAILURE_TIMEOUT,
                            provider=prov)
                        wjp.error = ("hedge drain: no attempt completed "
                                     "inside bound")
                        attempts.append(engine.JudgeAttempt(
                            attempt_no=1, slot_alias=model,
                            provider_requested=prov,
                            correlation_id=correlation_id,
                            failure_category=engine.FAILURE_TIMEOUT,
                            error_excerpt=wjp.error))
                    jp, served_by = wjp, walias
                else:
                    # No hedge (no alternate provider, or the hedge can't
                    # fit the ask budget): wait out attempt-1, then run
                    # the normal sequential cascade below.
                    jp = f1.result()
        # Hedge-race attempts complete out of order; restore the ledger
        # invariant (attempts in attempt-number order).
        attempts.sort(key=lambda a: a.attempt_no)
    if not hedged and not jp.live:
""")

open(P, "w").write(src)
print("edits applied")
