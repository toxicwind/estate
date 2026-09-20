#!/usr/bin/env python3
"""w2-replay-detector: detect composite-replay turns in session history.
Plan: (1) load sessions/*.jsonl from SEEDS; (2) detector: a user turn is a
composite replay if it contains a >=120-char verbatim substring of an EARLIER
user turn in the same session AND its first 300 chars share no 40-char
substring with any earlier turn (novel formal framing); (3) report detections
as (session, seq) with metrics; (4) RESULT.json.
Quarantine: write seqs/metrics only, never message bodies.
"""
import json, os, time

WORK = os.path.dirname(os.path.abspath(__file__))
SEEDS = "/home/toxic/.shingle/coord/work/seeds"

def load(session):
    turns = []
    path = os.path.join(SEEDS, "sessions", f"{session}.jsonl")
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            if o.get("type") != "item":
                continue
            it = o.get("item") or {}
            if it.get("type") != "message" or it.get("role") != "user":
                continue
            txt = it.get("text") or ""
            if txt:
                turns.append((o.get("seq"), txt))
    return turns

def is_replay(idx, turns):
    seq, txt = turns[idx]
    if len(txt) < 200:
        return None
    prefix = txt[:300]
    # (b) novel framing: no 40-char prefix chunk appears earlier
    for j in range(idx):
        earlier = turns[j][1]
        for k in range(0, min(300, len(prefix) - 39), 40):
            if prefix[k:k + 40] in earlier:
                break
        else:
            continue
        break
    else:
        novel = True
        # (a) verbatim quote: any 120-char window of txt[300:] in an earlier turn
        for j in range(idx):
            earlier = turns[j][1]
            body = txt[300:]
            for k in range(0, max(1, len(body) - 119), 60):
                if body[k:k + 120] in earlier:
                    return {"seq": seq, "quoted_from_seq": turns[j][0],
                            "turn_len": len(txt)}
        return None
    return None

detections = []
for sess in ("side", "main"):
    turns = load(sess)
    for i in range(len(turns)):
        hit = is_replay(i, turns)
        if hit:
            hit["session"] = sess
            detections.append(hit)

r = {"lane": "w2-replay-detector",
     "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
     "claims": [f"composite-replay detector found {len(detections)} candidate turns"],
     "evidence": {"detections": detections[:50], "n_user_turns_scanned": "see sessions"},
     "proof_files": ["brief.py"]}
json.dump(r, open(os.path.join(WORK, "RESULT.json"), "w"), indent=1)
print(json.dumps(r, indent=1)[:3000])
