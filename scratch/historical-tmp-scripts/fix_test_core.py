"""One-shot patch of bench/test_core.py for the oracle-market reliability redesign."""
import re

p = "/home/toxic/sovereign/agents/oracle-market/bench/test_core.py"
src = open(p).read()

# 1) RefusalGate (removed) -> emission-gate honesty checks.
old_gate = '''g = cal.RefusalGate()
g.set("a", "PASS", "ok"); g.set("b", "NOT_CHECKED", "later")
check("gate strict: NOT_CHECKED blocks ok()", not g.ok() and g.failures() == {},
      "NOT_CHECKED must never pass silently")
check("limitations line", "NOT_CHECKED" in g.limitations_line())'''
new_gate = '''import tempfile as _tf
_tmpd = _tf.mkdtemp(prefix="tc-gate-")
cal.CAL_DIR = _tmpd
cal.HISTORY_PATH = _tmpd + "/accepted_history.jsonl"
cal.DATASHEET_PATH = _tmpd + "/judge_datasheets.json"
cal.CAL_STATE_PATH = _tmpd + "/calibration_state.json"
_g, _reason, _op = cal.abstention_gate(cal.labeled_history(), 0.8, 0.05)
check("gate strict: no labels withholds", _g == "withhold",
      "no labels must never emit silently: %s" % _reason)
check("gate withhold never writes synthetic rows",
      not os.path.exists(cal.HISTORY_PATH), "withhold is read-only")'''
assert old_gate in src, "gate block not found"
src = src.replace(old_gate, new_gate)

# 2) _resilient_judge now returns 3-tuple (jp, slot, attempts).
src = src.replace("jp, info = oracle_ask._resilient_judge(",
                  "jp, info, _att = oracle_ask._resilient_judge(")
assert "_att = oracle_ask._resilient_judge(" in src

# 3) judge_once now returns (jp, attempt); null content -> parse_failure.
old_judge = '''    _njp = oracle_ask.judge_once("oracle-judge-a", "Q?", 30)
finally:
    oracle_ask.herd_chat = _orig_herd
check("judge_once null content -> refused not crash",
      _njp.refused and _njp.posterior == 0.5,
      "%s %s" % (_njp.refused, _njp.posterior))'''
new_judge = '''    _njp, _natt = oracle_ask.judge_once("oracle-judge-a", "Q?", 30)
finally:
    oracle_ask.herd_chat = _orig_herd
check("judge_once null content -> parse_failure not crash",
      not _njp.refused and not _njp.valid
      and _njp.failure_category == engine.FAILURE_PARSE
      and _njp.posterior == 0.5,
      "%s %s %s" % (_njp.refused, _njp.valid, _njp.failure_category))'''
assert old_judge in src, "judge_once block not found"
src = src.replace(old_judge, new_judge)

# 4) _slow_slot monkeypatch must return the 3-tuple.
old_slot = '''    jp = engine.JudgePosterior(judge_id=model, posterior=0.5, refused=True)
    return jp, {"slot": model, "served_by": model, "refused": True,
                "attempts": 0}'''
new_slot = '''    jp = engine.JudgePosterior(judge_id=model, posterior=0.5, refused=True)
    return jp, {"slot": model, "served_by": model, "refused": True,
                "attempts": 0}, []'''
assert old_slot in src, "slow slot block not found"
src = src.replace(old_slot, new_slot)

open(p, "w").write(src)
print("test_core.py patched OK")
