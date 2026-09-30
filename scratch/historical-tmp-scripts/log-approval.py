import json, time
ev = {
    "event": "oracle-approval",
    "question": "Will the oracle-market loop settle at least one task successfully on 2026-09-22?",
    "verdict": "escalate",
    "probability": 0.42643632098307754,
    "evidence_ids": ["ledger-flow", "recent-activity", "daemons-up"],
    "agent": "pack-loop-proof",
    "note": "oracle abstained (fail-closed: CP lower bound 0.000 < 0.80, no calibration data) -> HUMAN step per escalation ladder",
    "ts": time.time(),
}
with open("/home/toxic/sovereign/agents/oracle-market/ledger/ledger.jsonl", "a") as f:
    f.write(json.dumps(ev) + "\n")
print("logged oracle-approval:", ev["verdict"])
