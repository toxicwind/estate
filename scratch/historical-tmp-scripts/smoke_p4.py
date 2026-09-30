import sys, json, os
sys.path.insert(0, "/home/toxic/sovereign/agents/oracle-market/bin")
import oracle_ask as oa, engine

calls = []
def fake_judge(alias, prompt, t, attempt_no=1, provider_requested=None, correlation_id=None):
    calls.append((alias, attempt_no))
    att = engine.JudgeAttempt(attempt_no=attempt_no, slot_alias=alias,
        provider_requested="openrouter-free", latency_s=1.5, http_status=None,
        failure_category=engine.FAILURE_TIMEOUT,
        error_excerpt="timeout after 1.5s" * 100,  # 1500 chars -> must truncate
        response_excerpt="partial json", correlation_id="smoke42")
    jp = engine.JudgePosterior(judge_id=alias, posterior=0.5, valid=False,
        failure_category=engine.FAILURE_TIMEOUT, provider="openrouter-free")
    return jp, att

jp, slot, attempts = oa._resilient_judge("oracle-judge-a", "Q?", 5,
    judge_fn=fake_judge, panel_aliases=["oracle-judge-a", "oracle-judge-b"],
    targets={}, correlation_id="smoke42")
lines = open("/tmp/jfe_smoke/evidence.jsonl").read().strip().split("\n")
recs = [json.loads(l) for l in lines]
print("calls:", calls)
print("n_lines:", len(lines))
print("keys:", sorted(recs[0].keys()))
print("err_len:", len(recs[0]["error_excerpt"]), "(<=500 required)")
print("classes:", [r["error_class"] for r in recs])
print("slot:", recs[0]["slot"], "cid:", recs[0]["correlation_id"],
      "provider:", recs[0]["provider"], "latency_ms:", recs[0]["latency_ms"])
print("attempt_nos:", [r["attempt_no"] for r in recs])

# disabled path: flip constant, emitter must write nothing
oa.JUDGE_FAILURE_EVIDENCE_ENABLED = False
before = os.path.getsize("/tmp/jfe_smoke/evidence.jsonl")
oa._emit_failure_evidence(recs[0] and engine.JudgeAttempt(
    attempt_no=9, slot_alias="x", failure_category=engine.FAILURE_TIMEOUT), slot="x")
after = os.path.getsize("/tmp/jfe_smoke/evidence.jsonl")
print("disabled_path_unchanged:", before == after)

# never-raises: point at a directory path
oa.JUDGE_FAILURE_EVIDENCE_ENABLED = True
oa.JUDGE_FAILURE_EVIDENCE_PATH = "/tmp/jfe_smoke"  # a dir, open() fails
oa._emit_failure_evidence(engine.JudgeAttempt(
    attempt_no=9, slot_alias="x", failure_category=engine.FAILURE_TIMEOUT), slot="x")
print("never_raises: OK")
