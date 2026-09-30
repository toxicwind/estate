"""P4 patch: append-only JSONL failure-evidence logger for judge attempts."""
import sys

P = "/home/toxic/sovereign/agents/oracle-market/bin/oracle_ask.py"
src = open(P).read()

# --- Edit 1: module-level constants after WORK ---
anchor1 = 'WORK = os.environ.get("ORACLE_WORK", "/home/toxic/sovereign/agents/oracle-market/work")'
assert src.count(anchor1) == 1, "anchor1 count=%d" % src.count(anchor1)
consts = anchor1 + '''

# Judge failure-evidence log (P4, Nightjar cycle-2): append-only JSONL of
# FAILED judge attempts under WORK/, one line per attempt. The verdict ledger
# keeps per-ask evidence; this file aggregates ACROSS asks for diagnosis
# (per-provider failure rates, latency/error-class distributions).
# Harmless by construction: additive only (no behavior change), default ON,
# disable with JUDGE_FAILURE_EVIDENCE=0, every I/O error is swallowed, and
# writes are single O_APPEND line writes (atomic under the run_ask thread
# pool). No rotation yet -- lines are small and failures are rare; see
# open items in nightjar-overnight/evidence-preservation.md.
JUDGE_FAILURE_EVIDENCE_ENABLED = os.environ.get(
    "JUDGE_FAILURE_EVIDENCE", "1").lower() not in ("0", "false", "no")
JUDGE_FAILURE_EVIDENCE_PATH = os.environ.get(
    "JUDGE_FAILURE_EVIDENCE_PATH",
    os.path.join(WORK, "judge-failure-evidence.jsonl"))
JUDGE_FAILURE_EVIDENCE_MAXCHARS = 500  # per excerpt field, per line'''
src = src.replace(anchor1, consts)

# --- Edit 2: emitter function before _resilient_judge ---
anchor2 = "def _resilient_judge(model, prompt, timeout_s, judge_fn=None,"
assert src.count(anchor2) == 1, "anchor2 count=%d" % src.count(anchor2)
emitter = '''def _emit_failure_evidence(attempt, slot):
    """Append one failed judge attempt to the failure-evidence JSONL log.

    attempt: engine.JudgeAttempt with failure_category != engine.FAILURE_OK.
    slot: the panel slot alias this attempt belongs to.
    Never raises: a logging failure must never break the ask path.
    """
    if not JUDGE_FAILURE_EVIDENCE_ENABLED:
        return
    try:
        mc = JUDGE_FAILURE_EVIDENCE_MAXCHARS
        record = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "correlation_id": getattr(attempt, "correlation_id", None),
            "slot": slot,
            "judge_alias": getattr(attempt, "slot_alias", None),
            "attempt_no": getattr(attempt, "attempt_no", None),
            "latency_ms": round(float(getattr(attempt, "latency_s", 0) or 0) * 1000, 1),
            "http_status": getattr(attempt, "http_status", None),
            "error_class": getattr(attempt, "failure_category", None),
            "provider": getattr(attempt, "provider_requested", None),
            "model_served": getattr(attempt, "model_served", None),
            "error_excerpt": (getattr(attempt, "error_excerpt", None) or "")[:mc],
            "partial_output": (getattr(attempt, "response_excerpt", None) or "")[:mc],
        }
        line = json.dumps(record, ensure_ascii=False)
        path = JUDGE_FAILURE_EVIDENCE_PATH
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\\n")
    except Exception:
        pass


'''
src = src.replace(anchor2, emitter + anchor2)

# --- Edit 3: hook at end of _resilient_judge ---
anchor3 = '    slot = {"slot": model, "served_by": served_by,'
assert src.count(anchor3) == 1, "anchor3 count=%d" % src.count(anchor3)
hook = '''    # P4: aggregate every failed attempt (superseded attempt-1s included --
    # they are the tail-latency/provider-outage data) to the failure-evidence
    # log. Only failures; successful attempts stay in the verdict ledger.
    for att in attempts:
        if getattr(att, "failure_category", engine.FAILURE_OK) != engine.FAILURE_OK:
            _emit_failure_evidence(att, slot=model)
'''
src = src.replace(anchor3, hook + anchor3)

open(P, "w").write(src)
print("patched OK")
