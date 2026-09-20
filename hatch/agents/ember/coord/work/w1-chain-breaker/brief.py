#!/usr/bin/env python3
"""w1-chain-breaker: pre-send storm-body scrubber.
Plan: (1) implement scrub(turns); (2) test on synthetic poisoned context with
stand-in digests (never the real bodies); (3) assert zero storm bytes survive;
(4) measure latency; (5) write RESULT.json + proof log.
"""
import json, os, time, hashlib

WORK = os.path.dirname(os.path.abspath(__file__))
REAL_STORMS = {"b4aefd29108f232f9c0d5a4b030215c1": 384,
               "582bcbd080daeb3f826c45ed4a83b265": 96}
STORMS = dict(REAL_STORMS)

def scrub(turns):
    out, last_md5, run = [], None, 0
    for t in turns:
        h = hashlib.md5(t["text"].encode("utf-8", "replace")).hexdigest()
        if h in STORMS:
            if h == last_md5:
                run += 1
                if run >= 2:
                    continue  # collapse 3rd+ consecutive identical storm turn
            else:
                run = 0
            last_md5 = h
            out.append({"role": t["role"],
                        "text": f"[storm-body quarantined md5={h} len={STORMS[h]}]"})
        else:
            last_md5, run = None, 0
            out.append(t)
    return out

def test():
    log = []
    # synthetic stand-ins (NOT real storm bodies)
    fake1, fake2 = "Q" * 384, "Z" * 96
    STORMS.clear()
    STORMS.update({hashlib.md5(fake1.encode()).hexdigest(): 384,
                   hashlib.md5(fake2.encode()).hexdigest(): 96})
    turns = []
    for i in range(100):
        txt = f"benign turn {i} about infrastructure"
        if i in (10, 11, 12):
            txt = fake1  # 3 consecutive identical -> collapse the 3rd
        elif i in (13, 77):
            txt = fake2
        elif i == 50:
            txt = fake1
        turns.append({"role": "user" if i % 2 else "assistant", "text": txt})
    t0 = time.time()
    out = scrub(turns)
    dt = (time.time() - t0) * 1000
    blob = "\n".join(t["text"] for t in out)
    assert fake1 not in blob and fake2 not in blob, "storm bytes survived!"
    assert len(out) == len(turns) - 1, f"expected exactly 1 collapse, got {len(turns)-len(out)}"
    assert dt < 50, f"too slow: {dt:.1f}ms"
    log.append(f"in=100 out={len(out)} storm_bytes_surviving=0 latency_ms={dt:.2f}")
    # real digests still registered in default config
    STORMS.clear(); STORMS.update(REAL_STORMS)
    log.append("real storm digests registered in default config: 2")
    open(os.path.join(WORK, "PROOF.txt"), "w").write("\n".join(log) + "\n")
    return log

log = test()
r = {"lane": "w1-chain-breaker",
     "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
     "claims": ["scrub() quarantines byte-identical storm bodies by digest",
                "collapses 3rd+ consecutive identical storm turns",
                "synthetic test: 0 storm bytes survive, <50ms per 100 turns"],
     "evidence": {"test_log": log},
     "proof_files": ["PROOF.txt", "brief.py"]}
json.dump(r, open(os.path.join(WORK, "RESULT.json"), "w"), indent=1)
print(json.dumps(r, indent=1))
