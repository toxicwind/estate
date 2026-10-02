#!/usr/bin/env python3
"""Nightjar cycle-4: functional test for P1 per-provider circuit breaker.
Stub-based (no network, no live judges). Exit 0 = all pass."""
import importlib.util
import json
import os
import sys
import tempfile
import time

_iso = tempfile.mkdtemp(prefix="nightjar-p1-")
BPATH = os.path.join(_iso, "judge-breaker-state.json")
os.environ["JUDGE_BREAKER_PATH"] = BPATH

BIN = "/home/toxic/sovereign/agents/oracle-market/bin"
sys.path.insert(0, BIN)
_spec = importlib.util.spec_from_file_location(
    "oracle_ask_p1", os.path.join(BIN, "oracle_ask.py"))
_oa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_oa)
engine = _oa.engine

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print("ok   %s" % name)
    else:
        print("FAIL %s %s" % (name, detail))
        FAILURES.append(name)


_TARGETS = {"a": ["p1/x"], "b": ["p1/y"], "c": ["p2/z"],
            "oracle-judge-local": ["local/m"]}


def _mk_jp(alias, ok, cat, provider):
    return engine.JudgePosterior(
        judge_id=alias, posterior=0.7, refused=False, valid=ok,
        failure_category=cat if not ok else engine.FAILURE_OK,
        provider=provider)


def _mk_att(alias, no, cat, provider):
    return engine.JudgeAttempt(attempt_no=no, slot_alias=alias,
                               provider_requested=provider,
                               failure_category=cat,
                               correlation_id="corr-p1")


def _stub(seen, fail_aliases=(), fail_cat=engine.FAILURE_TIMEOUT):
    """fail_aliases: aliases that fail with fail_cat; others succeed."""
    def fn(alias, prompt, t, attempt_no=1, provider_requested=None,
           correlation_id=None):
        seen.append(alias)
        prov = {"a": "p1", "b": "p1", "c": "p2",
                "oracle-judge-local": "local"}.get(alias, "unknown")
        if alias in fail_aliases:
            return (_mk_jp(alias, False, fail_cat, prov),
                    _mk_att(alias, attempt_no, fail_cat, prov))
        return (_mk_jp(alias, True, engine.FAILURE_OK, prov),
                _mk_att(alias, attempt_no, engine.FAILURE_OK, prov))
    return fn


def _ask(seen, **kw):
    kw.setdefault("panel_aliases", ["a", "b", "c"])
    kw.setdefault("targets", _TARGETS)
    return _oa._resilient_judge("a", "p", 10, **kw)


def _state():
    with open(os.environ["JUDGE_BREAKER_PATH"]) as f:
        return json.load(f)


# --- 1. three consecutive provider-class failures trip the breaker ---
seen = []
for _ in range(3):
    _ask(seen, judge_fn=_stub(seen, fail_aliases=("a",)))
st = _state()
check("trip: p1 open after 3 consecutive fails",
      st.get("p1", {}).get("state") == "open", repr(st))

seen4 = []
jp, slot, attempts = _ask(seen4, judge_fn=_stub(seen4, fail_aliases=("a",)))
check("trip: attempt-1 skipped when open", seen4 == ["c"], repr(seen4))
check("trip: no phantom attempt in ledger",
      len(attempts) == 1 and attempts[0].slot_alias == "c",
      repr([(a.slot_alias, a.attempt_no) for a in attempts]))
check("trip: breaker_skips ledgered",
      slot["breaker_skips"] == [{"attempt_no": 1, "alias": "a",
                                 "provider": "p1", "reason": "breaker_open"}],
      repr(slot["breaker_skips"]))
check("trip: slot JSON-serializable", bool(json.dumps(slot)))
check("trip: served_by c", slot["served_by"] == "c")

# --- 2. half-open probe success closes ---
st = _state()
st["p1"]["opened_at"] = time.time() - 400  # expire the 300s cooldown
with open(BPATH, "w") as f:
    json.dump(st, f)
seen5 = []
jp, slot, attempts = _ask(seen5, judge_fn=_stub(seen5, fail_aliases=()))
check("half-open: probe issued after cooldown", seen5[0] == "a", repr(seen5))
check("half-open: success closes breaker", "p1" not in _state(), repr(_state()))
seen6 = []
_ask(seen6, judge_fn=_stub(seen6, fail_aliases=()))
check("half-open: next ask issues attempt-1 normally",
      seen6[0] == "a", repr(seen6))

# --- 3. half-open probe failure re-opens ---
with open(BPATH, "w") as f:
    json.dump({"p1": {"state": "open", "fails": 3,
                      "opened_at": time.time() - 400,
                      "probe_in_flight": False, "probe_at": 0.0}}, f)
seen7 = []
_ask(seen7, judge_fn=_stub(seen7, fail_aliases=("a",)))
check("re-open: failed probe re-issues attempt-1", seen7[0] == "a",
      repr(seen7))
st = _state()
check("re-open: breaker open again",
      st.get("p1", {}).get("state") == "open", repr(st))
check("re-open: opened_at refreshed",
      st["p1"]["opened_at"] > time.time() - 60, repr(st["p1"]))
seen8 = []
_ask(seen8, judge_fn=_stub(seen8, fail_aliases=("a",)))
check("re-open: next ask skips again", seen8 == ["c"], repr(seen8))

# --- 4. unknown provider never trips ---
os.environ["JUDGE_BREAKER_PATH"] = BPATH + ".u2"
seen9 = []
for _ in range(5):
    _ask(seen9, judge_fn=_stub(seen9, fail_aliases=("a",)),
         targets={})  # no topology -> provider "unknown"
# per ask: ["a", "a", "oracle-judge-local"] (attempt-1, same-alias retry,
# fallback). The 5th ask still issues attempt-1:
check("unknown: 5th ask still issues attempt-1",
      seen9[-3] == "a", repr(seen9[-4:]))
check("unknown: no state recorded",
      not os.path.exists(BPATH + ".u2"))
os.environ["JUDGE_BREAKER_PATH"] = BPATH

# --- 5. non-provider failures (parse) do not trip ---
os.environ["JUDGE_BREAKER_PATH"] = BPATH + ".p2"


def _parse_stub(seen):
    def fn(alias, prompt, t, attempt_no=1, provider_requested=None,
           correlation_id=None):
        seen.append(alias)
        if attempt_no == 1:
            return (_mk_jp(alias, False, engine.FAILURE_PARSE, "p1"),
                    _mk_att(alias, attempt_no, engine.FAILURE_PARSE, "p1"))
        return (_mk_jp(alias, True, engine.FAILURE_OK, "p1"),
                _mk_att(alias, attempt_no, engine.FAILURE_OK, "p1"))
    return fn


seen10 = []
for _ in range(6):
    _ask(seen10, judge_fn=_parse_stub(seen10))
check("parse: 6th ask still issues attempt-1",
      seen10[-2:] == ["a", "a"], repr(seen10[-4:]))
os.environ["JUDGE_BREAKER_PATH"] = BPATH

# --- 6. success resets the consecutive count ---
# Scripted per-CALL outcomes for alias "a" only (other aliases succeed):
# fail,fail -> 2 consecutive (no trip); ok -> reset; fail,fail -> 2;
# fail -> 3rd consecutive trips mid-ask (retry skipped); next ask skips a1.
os.environ["JUDGE_BREAKER_PATH"] = BPATH + ".r2"
seen11 = []


def _flap_stub(seen, script):
    it = iter(list(script))

    def fn(alias, prompt, t, attempt_no=1, provider_requested=None,
           correlation_id=None):
        seen.append(alias)
        if alias != "a":
            ok = True
        else:
            ok = next(it, True)
        cat = engine.FAILURE_OK if ok else engine.FAILURE_TIMEOUT
        prov = "p1" if alias == "a" else "p2"
        return (_mk_jp(alias, ok, cat, prov),
                _mk_att(alias, attempt_no, cat, prov))
    return fn


_ask(seen11, judge_fn=_flap_stub(seen11, [False, False]),
     panel_aliases=["a"])
_ask(seen11, judge_fn=_flap_stub(seen11, [True]), panel_aliases=["a"])
check("reset: success clears consecutive count",
      "p1" not in _state(), repr(_state()))
seen12 = []
jp12, slot12, att12 = _ask(seen12, judge_fn=_flap_stub(seen12, [False, False]),
                           panel_aliases=["a"])
check("reset: 2 consecutive fails do not trip", seen12[:2] == ["a", "a"],
      repr(seen12))
seen13 = []
jp13, slot13, att13 = _ask(seen13, judge_fn=_flap_stub(seen13, [False, True]),
                           panel_aliases=["a"])
check("reset: 3rd consecutive fail trips mid-ask (retry skipped)",
      seen13 == ["a", "oracle-judge-local"], repr(seen13))
check("reset: mid-ask trip ledgered as breaker skip",
      slot13["breaker_skips"] == [{"attempt_no": 2, "alias": "a",
                                   "provider": "p1",
                                   "reason": "breaker_open"}],
      repr(slot13["breaker_skips"]))
check("reset: breaker open in state",
      _state().get("p1", {}).get("state") == "open", repr(_state()))
seen14b = []
jp14b, slot14b, att14b = _ask(
    seen14b, judge_fn=_flap_stub(seen14b, [True]), panel_aliases=["a"])
check("reset: next ask skips attempt-1 AND retry (open)",
      seen14b == ["oracle-judge-local"], repr(seen14b))
check("reset: two breaker skips ledgered, no phantom attempts",
      len(slot14b["breaker_skips"]) == 2
      and len(att14b) == 1 and att14b[0].slot_alias == "oracle-judge-local",
      repr((slot14b["breaker_skips"],
            [(a.slot_alias, a.attempt_no) for a in att14b])))
os.environ["JUDGE_BREAKER_PATH"] = BPATH

# --- 7. corrupt state file -> old behavior ---
with open(BPATH, "w") as f:
    f.write("this is not json {{{")
seen14 = []
jp, slot, attempts = _ask(seen14, judge_fn=_stub(seen14, fail_aliases=()))
check("corrupt: attempt-1 issued", seen14[0] == "a", repr(seen14))
check("corrupt: no breaker skips", slot["breaker_skips"] == [])

# --- 8. missing state file -> old behavior ---
if os.path.exists(BPATH):
    os.unlink(BPATH)
seen15 = []
jp, slot, attempts = _ask(seen15, judge_fn=_stub(seen15, fail_aliases=()))
check("missing: attempt-1 issued", seen15[0] == "a", repr(seen15))

# --- 9. disabled via env -> old behavior even when state says open ---
with open(BPATH, "w") as f:
    json.dump({"p1": {"state": "open", "fails": 9, "opened_at": time.time(),
                      "probe_in_flight": False, "probe_at": 0.0}}, f)
os.environ["JUDGE_BREAKER"] = "0"
seen16 = []
_ask(seen16, judge_fn=_stub(seen16, fail_aliases=("a",)))
check("disabled: attempt-1 issued despite open state",
      seen16[0] == "a", repr(seen16))
del os.environ["JUDGE_BREAKER"]

print("---")
if FAILURES:
    print("%d FAILURES: %s" % (len(FAILURES), ", ".join(FAILURES)))
    sys.exit(1)
print("all P1 functional tests passed")
