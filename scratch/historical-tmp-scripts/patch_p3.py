"""Nightjar cycle-2: apply P3 (deadline-aware retry budget) to
_resilient_judge in bin/oracle_ask.py. Read-only analysis first, then
exact-string replacements (each asserted to match exactly once). Backup
written only after all replacements succeed. No daemons touched."""
import shutil
import sys

P = "/home/toxic/sovereign/agents/oracle-market/bin/oracle_ask.py"
BAK = P + ".bak-nightjar-p3"

with open(P) as f:
    src = f.read()


def rep(old, new):
    global src
    n = src.count(old)
    if n != 1:
        print("PATTERN COUNT %d (expected 1):\n%s" % (n, old[:220]))
        sys.exit(1)
    src = src.replace(old, new)


# 1. signature: optional deadline kwarg (default None = check disabled)
rep("""def _resilient_judge(model, prompt, timeout_s, judge_fn=None,
                     panel_aliases=None, targets=None, correlation_id=None):""",
    """def _resilient_judge(model, prompt, timeout_s, judge_fn=None,
                     panel_aliases=None, targets=None, correlation_id=None,
                     deadline=None):""")

# 2. docstring: document the new parameter
rep("""    (engine.classify_failures) attributes correlated failures to the
    provider instead of counting them as independent judge failures.
    \"\"\"""",
    """    (engine.classify_failures) attributes correlated failures to the
    provider instead of counting them as independent judge failures.

    deadline (epoch seconds, optional): the ask-level deadline from
    run_ask's budget_s. An attempt whose own timeout cannot plausibly fit
    inside the remaining budget is never issued — it is skipped (logged to
    stderr, counted on slot_info["budget_skips"]). gRPC deadline dominance
    / Temporal ScheduleToCloseTimeout. deadline=None disables the check.
    \"\"\"""")

# 3. helpers: _fits / _skip + budget_skips ledger
rep("""    attempts = []

    def _call(alias, t, no):""",
    """    attempts = []
    budget_skips = []  # P3: attempts refused for budget reasons — logged to
                       # stderr and counted here, NOT appended to `attempts`
                       # (the failure taxonomy has no "not attempted"
                       # category; classify_failures reads last-attempt
                       # categories, so skips stay out of the ledger)

    def _fits(planned_timeout_s):
        \"\"\"True iff an attempt with this timeout can plausibly complete
        before the ask deadline. deadline=None disables the check.\"\"\"
        if deadline is None:
            return True
        return (deadline - time.time()) >= planned_timeout_s

    def _skip(attempt_no, alias, planned_timeout_s):
        remaining = (deadline - time.time()) if deadline is not None else 0.0
        budget_skips.append({"attempt_no": attempt_no, "alias": alias,
                             "planned_timeout_s": round(planned_timeout_s, 3),
                             "remaining_budget_s": round(max(0.0, remaining), 3)})
        # stderr, not stdout: main() prints the verdict as JSON on stdout.
        print("[nightjar-P3] budget skip: slot=%s attempt=%d alias=%s "
              "planned_timeout=%.1fs remaining_budget=%.1fs"
              % (model, attempt_no, alias, planned_timeout_s,
                 max(0.0, remaining)), file=sys.stderr, flush=True)

    def _call(alias, t, no):""")

# 4. attempt-2: gate every retry on the budget before issuing it
rep("""    jp = _call(model, timeout_s, 1)
    served_by = model
    if not jp.live:
        if getattr(jp, "failure_category", engine.FAILURE_UNKNOWN) \\
                in engine.PROVIDER_CLASS_FAILURES:
            alt = next((a for a in panel
                        if a != model and a != FALLBACK_JUDGE
                        and provider_of_alias(a, targets) not in (prov, "unknown")),
                       None)
            if alt is not None:
                jp = _call(alt, min(timeout_s, 60.0), 2)
                if jp.live:
                    served_by = alt
            else:
                # jittered backoff before re-rolling the SAME alias:
                # immediate re-rolls of a flaky alias self-inflict retry storms
                # (RetryGuard 2511.23278; LiteLLM _calculate_retry_after; resilience4j).
                time.sleep(random.uniform(0.25, 1.0))
                jp = _call(model, min(timeout_s, 60.0), 2)
        else:
            # jittered backoff before re-rolling the SAME alias:
            # immediate re-rolls of a flaky alias self-inflict retry storms
            # (RetryGuard 2511.23278; LiteLLM _calculate_retry_after; resilience4j).
            time.sleep(random.uniform(0.25, 1.0))
            jp = _call(model, min(timeout_s, 60.0), 2)
    if not jp.live and model != FALLBACK_JUDGE:
        fb = _call(FALLBACK_JUDGE, 120.0, len(attempts) + 1)
        if fb.live:
            jp = fb
            served_by = FALLBACK_JUDGE
        else:
            jp = fb""",
    """    t2 = min(timeout_s, 60.0)  # P3: attempt-2's planned timeout, reused by the budget check
    jp = _call(model, timeout_s, 1)
    served_by = model
    if not jp.live:
        # P3: deadline-aware retry budget (gRPC deadline dominance /
        # Temporal ScheduleToCloseTimeout). Never ISSUE an attempt that
        # cannot complete before the ask deadline: run_ask's fut.result()
        # would abandon it anyway — and worse, the TimeoutError path wipes
        # the slot's attempts with FAILURE_EXECUTOR. Skipping preserves the
        # real evidence AND saves provider quota / local compute.
        if getattr(jp, "failure_category", engine.FAILURE_UNKNOWN) \\
                in engine.PROVIDER_CLASS_FAILURES:
            alt = next((a for a in panel
                        if a != model and a != FALLBACK_JUDGE
                        and provider_of_alias(a, targets) not in (prov, "unknown")),
                       None)
            if alt is not None and _fits(t2):
                jp = _call(alt, t2, 2)
                if jp.live:
                    served_by = alt
            elif _fits(t2):
                # jittered backoff before re-rolling the SAME alias:
                # immediate re-rolls of a flaky alias self-inflict retry storms
                # (RetryGuard 2511.23278; LiteLLM _calculate_retry_after; resilience4j).
                time.sleep(random.uniform(0.25, 1.0))
                jp = _call(model, t2, 2)
            else:
                _skip(2, alt or model, t2)
        elif _fits(t2):
            # jittered backoff before re-rolling the SAME alias:
            # immediate re-rolls of a flaky alias self-inflict retry storms
            # (RetryGuard 2511.23278; LiteLLM _calculate_retry_after; resilience4j).
            time.sleep(random.uniform(0.25, 1.0))
            jp = _call(model, t2, 2)
        else:
            _skip(2, model, t2)
    if not jp.live and model != FALLBACK_JUDGE:
        if _fits(120.0):
            fb = _call(FALLBACK_JUDGE, 120.0, len(attempts) + 1)
            if fb.live:
                jp = fb
                served_by = FALLBACK_JUDGE
            else:
                jp = fb
        else:
            # Local fallback is separate infrastructure, but a 120s attempt
            # issued with <120s of budget is doomed: the result would be
            # discarded at the deadline and the slot's evidence wiped by
            # FAILURE_EXECUTOR. Skip it and keep attempt-1/2's evidence.
            _skip(len(attempts) + 1, FALLBACK_JUDGE, 120.0)""")

# 5. slot_info: surface the skip count (additive key)
rep('''            "provider_serving": jp.provider,
            "attempts": len(attempts)}''',
    '''            "provider_serving": jp.provider,
            "attempts": len(attempts),
            "budget_skips": budget_skips}''')

# 6. run_ask: compute deadline before submit, pass it to every slot
rep("""    with cf.ThreadPoolExecutor(max_workers=len(models)) as ex:
        futs = {ex.submit(_resilient_judge, m, prompt_for(i), timeout_s,
                          None, models, targets, correlation_id): (m, i)
                for i, m in enumerate(models)}
        deadline = t0 + budget_s""",
    """    # P3: every slot gets the ask deadline; attempts that cannot fit
    # the remaining budget are skipped (never issued), not killed mid-flight.
    deadline = t0 + budget_s
    with cf.ThreadPoolExecutor(max_workers=len(models)) as ex:
        futs = {ex.submit(_resilient_judge, m, prompt_for(i), timeout_s,
                          None, models, targets, correlation_id,
                          deadline=deadline): (m, i)
                for i, m in enumerate(models)}""")

shutil.copy2(P, BAK)
with open(P, "w") as f:
    f.write(src)
print("patched OK; backup at", BAK)
