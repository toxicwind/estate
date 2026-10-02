#!/usr/bin/env python3
"""Nightjar cycle-4: apply P1 (per-provider circuit breaker) to
agents/oracle-market/bin/oracle_ask.py + breaker isolation in the test suite.
Exact-match replacements; every replacement asserts its expected count.
Exits nonzero on any mismatch (no partial application)."""
import sys

ASK = "/home/toxic/sovereign/agents/oracle-market/bin/oracle_ask.py"
TST = "/home/toxic/sovereign/agents/oracle-market/bin/test_oracle_reliability.py"


def replace_once(path, old, new, expect=1):
    with open(path) as f:
        text = f.read()
    n = text.count(old)
    if n != expect:
        print("MISMATCH in %s: anchor found %d times, expected %d:\n%r"
              % (path, n, expect, old[:120]))
        sys.exit(1)
    text = text.replace(old, new)
    with open(path, "w") as f:
        f.write(text)
    print("ok: applied anchor (%r...)" % old[:60].replace("\n", "\\n"))


BREAKER_BLOCK = '''# ---------------------------------------------------------------------------
# P1: per-provider circuit breaker (Nightjar cycle-4; resilience4j pattern)
# ---------------------------------------------------------------------------
# Extends the within-ask "never re-roll a dead provider" cascade to
# ACROSS-ask memory: when a provider fails 3 consecutive judge calls with
# provider-class failures (timeout/5xx/429/402/connection), its breaker
# OPENS for 300s. While open, attempts against it become ledgered skips
# (no quota burned, no phantom attempts in the ledger) and the cascade
# jumps straight to the alternate-provider attempt / local fallback. After
# the cooldown, one half-open probe is admitted; success closes the
# breaker, failure re-opens it.
#
# State lives in a small JSON file under WORK/ (gitignored runtime state,
# like the market's task-backlog): survives daemon restarts, no new infra.
# All read-modify-write goes through fcntl.flock (shared for reads,
# exclusive for writes) -- run_ask's thread pool plus concurrent asks are
# separate processes, so flock is the multi-process safety mechanism.
# Missing or corrupt state file -> fail closed to old behavior (breaker
# disabled: every attempt allowed). Unattributable providers ("unknown")
# never trip the breaker.
#
# Thresholds: tonight's failure-evidence log holds only synthetic test data
# (providers p1/p2/local), so no production failure distribution exists to
# fit yet. Defaults follow the pattern sources, sized for ASK frequency
# (judge volume is ~3-9 calls/ask, asks minutes apart -- not RPS):
#   ALLOWED_FAILS=3 consecutive provider-class failures (LiteLLM
#     allowed_fails default; the consecutive count IS the resilience4j
#     minimum-call gating at our volume -- a success resets it)
#   COOLDOWN_S=300 (LiteLLM's 5s proxy default assumes high RPS; 300s means
#     a dead provider costs one 90s rediscovery per ~5 min, not per ask)
# Tune via JUDGE_BREAKER_ALLOWED_FAILS / JUDGE_BREAKER_COOLDOWN_S, disable
# with JUDGE_BREAKER=0, redirect state with JUDGE_BREAKER_PATH (tests use
# this for isolation).


def _breaker_enabled():
    return os.environ.get(
        "JUDGE_BREAKER", "1").lower() not in ("0", "false", "no")


def _breaker_path():
    return os.environ.get(
        "JUDGE_BREAKER_PATH",
        os.path.join(WORK, "judge-breaker-state.json"))


def _breaker_allowed_fails():
    try:
        return max(1, int(os.environ.get("JUDGE_BREAKER_ALLOWED_FAILS", "3")))
    except Exception:
        return 3


def _breaker_cooldown_s():
    try:
        return max(1.0, float(os.environ.get("JUDGE_BREAKER_COOLDOWN_S", "300")))
    except Exception:
        return 300.0


_BREAKER_PROBE_LEASE_S = 300.0  # a half-open probe this old is stale


def _breaker_load():
    """Read breaker state. Missing/corrupt file -> {} (fail closed:
    breaker disabled, old behavior). Never raises."""
    try:
        with open(_breaker_path(), "r", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                data = json.load(f)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _breaker_mutate(fn):
    """fn(state, now) -> state (or None to skip the write). Read-modify-write
    under one exclusive flock: atomic wrt other processes. Never raises."""
    try:
        path = _breaker_path()
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(path, "a+", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                f.seek(0)
                raw = f.read()
                try:
                    state = json.loads(raw) if raw.strip() else {}
                except Exception:
                    state = {}
                if not isinstance(state, dict):
                    state = {}
                new_state = fn(state, time.time())
                if new_state is not None:
                    f.seek(0)
                    f.truncate()
                    json.dump(new_state, f)
                    f.write("\\n")
                    f.flush()
                    os.fsync(f.fileno())
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    except Exception:
        pass


def _breaker_allows(provider):
    """True if a call against this provider may be issued.

    OPEN + inside cooldown -> False. OPEN + cooldown expired -> half-open:
    exactly one probe is admitted (claimed atomically under the write
    lock); concurrent callers see the in-flight probe and skip. Anything
    unattributable ("unknown") or any state problem -> True (old behavior).
    """
    if not _breaker_enabled():
        return True
    if not provider or provider == "unknown":
        return True
    try:
        state = _breaker_load()
        e = state.get(provider)
        if not isinstance(e, dict) or e.get("state") != "open":
            return True
        now = time.time()
        if now - float(e.get("opened_at", 0)) < _breaker_cooldown_s():
            return False
        if e.get("probe_in_flight") and \\
                now - float(e.get("probe_at", 0)) < _BREAKER_PROBE_LEASE_S:
            return False
        claimed = []

        def _claim(st, t):
            cur = st.get(provider)
            if not isinstance(cur, dict) or cur.get("state") != "open":
                return None  # someone closed it meanwhile: no write needed
            if cur.get("probe_in_flight") and \\
                    t - float(cur.get("probe_at", 0)) < _BREAKER_PROBE_LEASE_S:
                return None  # lost the race: no write needed
            cur["probe_in_flight"] = True
            cur["probe_at"] = t
            claimed.append(True)
            return st

        _breaker_mutate(_claim)
        return bool(claimed)
    except Exception:
        return True


def _breaker_record(provider, jp):
    """Feed one ISSUED call's outcome into the breaker. Never raises.

    jp.live (a usable posterior) resets the consecutive-failure count and
    closes a half-open probe. Provider-class failures increment; anything
    else (refusal/parse/schema/unknown) is provider-infra-neutral and
    leaves the count alone.
    """
    if not _breaker_enabled():
        return
    if not provider or provider == "unknown":
        return
    try:
        if bool(getattr(jp, "live", False)):
            outcome = "ok"
        elif getattr(jp, "failure_category", engine.FAILURE_UNKNOWN) \\
                in engine.PROVIDER_CLASS_FAILURES:
            outcome = "fail"
        else:
            return
        allowed = _breaker_allowed_fails()

        def _apply(state, now):
            if outcome == "ok":
                # success resets consecutive failures; a probe success
                # closes the breaker. Either way the entry is clean: drop it.
                state.pop(provider, None)
                return state
            e = state.get(provider)
            if not isinstance(e, dict):
                e = {"state": "closed", "fails": 0, "opened_at": 0.0,
                     "probe_in_flight": False, "probe_at": 0.0}
            was_probe = bool(e.get("probe_in_flight"))
            e["fails"] = int(e.get("fails", 0)) + 1
            e["probe_in_flight"] = False
            e["probe_at"] = 0.0
            if was_probe or e["fails"] >= allowed:
                e["state"] = "open"
                e["opened_at"] = now
            state[provider] = e
            return state

        _breaker_mutate(_apply)
    except Exception:
        pass


'''

# --- oracle_ask.py edits ---

replace_once(ASK,
             "import concurrent.futures as cf\nimport json\n",
             "import concurrent.futures as cf\nimport fcntl\nimport json\n")

replace_once(ASK,
             "def _resilient_judge(model, prompt, timeout_s, judge_fn=None,\n",
             BREAKER_BLOCK + "def _resilient_judge(model, prompt, timeout_s, judge_fn=None,\n")

old_doc = """    / Temporal ScheduleToCloseTimeout. deadline=None disables the check.
    \"\"\""""
new_doc = """    / Temporal ScheduleToCloseTimeout. deadline=None disables the check.

    breaker (P1, resilience4j): before each provider call, the per-provider
    circuit breaker (keyed by provider_of_alias(), state in
    work/judge-breaker-state.json under flock) is consulted. An OPEN
    breaker converts the attempt into a ledgered skip (stderr +
    slot_info["breaker_skips"]) instead of burning quota on a known-dead
    provider -- the cascade then proceeds to the alternate provider /
    fallback exactly as if attempt-1 had failed. Skips are never appended
    to the attempts ledger. Missing/corrupt state file fails closed to old
    behavior (breaker disabled).
    \"\"\""""
replace_once(ASK, old_doc, new_doc)

old_skips = """    budget_skips = []  # P3: attempts refused for budget reasons — logged to
                       # stderr and counted here, NOT appended to `attempts`
                       # (the failure taxonomy has no "not attempted"
                       # category; classify_failures reads last-attempt
                       # categories, so skips stay out of the ledger)
"""
new_skips = old_skips + """    breaker_skips = []  # P1: attempts refused by the provider circuit
                        # breaker (same convention as budget_skips: stderr +
                        # slot_info key, never appended to `attempts`)
"""
replace_once(ASK, old_skips, new_skips)

replace_once(ASK,
             "        attempts.append(att)\n        if not getattr(jp, \"provider\", None):\n",
             "        attempts.append(att)\n"
             "        # P1: every ISSUED call feeds the provider circuit breaker\n"
             "        # (success resets, provider-class failure increments,\n"
             "        # anything else is infra-neutral).\n"
             "        _breaker_record(preq, jp)\n"
             "        if not getattr(jp, \"provider\", None):\n")

old_t2 = """    t2 = min(timeout_s, 60.0)  # P3: attempt-2's planned timeout, reused by the budget check
    jp = _call(model, timeout_s, 1)
"""
new_t2 = """    t2 = min(timeout_s, 60.0)  # P3: attempt-2's planned timeout, reused by the budget check

    def _breaker_skip_jp(alias, no, skipped_provider):
        \"\"\"An OPEN-breaker skip: no quota burned, no phantom attempt.

        Returns a synthetic dead JudgePosterior with a provider-class
        failure category so the existing cascade (alternate-provider
        attempt-2, local fallback) proceeds unchanged. The skip is recorded
        on breaker_skips (additive slot_info key), never on `attempts` --
        like P3's budget skips.
        \"\"\"
        breaker_skips.append({"attempt_no": no, "alias": alias,
                              "provider": skipped_provider,
                              "reason": "breaker_open"})
        # stderr, not stdout: main() prints the verdict as JSON on stdout.
        print("[nightjar-P1] breaker skip: slot=%s attempt=%d alias=%s "
              "provider=%s (breaker OPEN)" % (model, no, alias,
                                              skipped_provider),
              file=sys.stderr, flush=True)
        jp = engine.JudgePosterior(
            judge_id=alias, posterior=0.5, refused=False, valid=False,
            failure_category=engine.FAILURE_TIMEOUT, provider=skipped_provider)
        jp.latency_s = 0.0
        return jp

    def _call_or_skip(alias, t, no):
        \"\"\"Issue _call unless that alias's provider breaker is OPEN.

        Breaker-inside-retry ordering (resilience4j decorator guidance):
        an OPEN breaker converts the attempt into a ledgered skip, not a
        phantom attempt and not a wasted call against a known-dead provider.
        \"\"\"
        preq = provider_of_alias(alias, targets)
        if not _breaker_allows(preq):
            return _breaker_skip_jp(alias, no, preq)
        return _call(alias, t, no)

    jp = _call_or_skip(model, timeout_s, 1)
"""
replace_once(ASK, old_t2, new_t2)

replace_once(ASK,
             "                jp = _call(alt, t2, 2)\n",
             "                jp = _call_or_skip(alt, t2, 2)\n")

replace_once(ASK,
             "                jp = _call(model, t2, 2)\n",
             "                jp = _call_or_skip(model, t2, 2)\n",
             expect=2)

replace_once(ASK,
             "            fb = _call(FALLBACK_JUDGE, 120.0, len(attempts) + 1)\n",
             "            fb = _call_or_skip(FALLBACK_JUDGE, 120.0, len(attempts) + 1)\n")

replace_once(ASK,
             '            "attempts": len(attempts),\n            "budget_skips": budget_skips}\n',
             '            "attempts": len(attempts),\n'
             '            "budget_skips": budget_skips,\n'
             '            "breaker_skips": breaker_skips}\n')

# --- test_oracle_reliability.py: breaker isolation in main() ---
old_main = """def main():
    fns = sorted([v for k, v in list(globals().items())
                  if k.startswith("test_") and callable(v)],
                 key=lambda f: f.__name__)
    for fn in fns:
        try:
            fn()
        except Exception as e:
            import traceback
            traceback.print_exc()
            print("FAIL %s raised %r" % (fn.__name__, e))
            FAILURES.append(fn.__name__)
    print("---")
"""
new_main = """def main():
    # P1 (Nightjar cycle-4): isolate the provider circuit breaker from the
    # production state file. This suite deliberately fails stub providers;
    # those failures must neither trip nor read the live breaker.
    _iso = tempfile.mkdtemp(prefix="oracle-breaker-")
    os.environ["JUDGE_BREAKER_PATH"] = os.path.join(
        _iso, "judge-breaker-state.json")
    try:
        fns = sorted([v for k, v in list(globals().items())
                      if k.startswith("test_") and callable(v)],
                     key=lambda f: f.__name__)
        for fn in fns:
            try:
                fn()
            except Exception as e:
                import traceback
                traceback.print_exc()
                print("FAIL %s raised %r" % (fn.__name__, e))
                FAILURES.append(fn.__name__)
    finally:
        shutil.rmtree(_iso, ignore_errors=True)
    print("---")
"""
replace_once(TST, old_main, new_main)

print("ALL EDITS APPLIED")
