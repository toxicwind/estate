import json, time
from collections import Counter
L = "/home/toxic/sovereign/agents/oracle-market/ledger/ledger.jsonl"
tasks = {}
for line in open(L):
    try:
        d = json.loads(line)
    except Exception:
        continue
    tid = d.get("task_id")
    if tid:
        tasks.setdefault(tid, []).append(d)
print("tasks:", len(tasks))
full = 0
ok_settle = 0
slash = 0
for tid, evs in tasks.items():
    names = {e.get("event") for e in evs}
    if {"task_open", "assigned"} <= names and ("settled" in names or "slashed" in names):
        full += 1
    for e in evs:
        if e.get("event") == "settled" and (e.get("success") or e.get("verified")):
            ok_settle += 1
        if e.get("event") == "slashed":
            slash += 1
print("full-lifecycle:", full, "/", len(tasks))
print("settled-success:", ok_settle, "| slashed:", slash)
for line in open(L):
    d = json.loads(line)
    if d.get("event") == "settled":
        print("settled keys:", sorted(d.keys()))
        print("settled sample:", {k: str(d[k])[:70] for k in d})
        break
# last 5 tasks: event sequence
for tid in list(tasks)[-5:]:
    print(tid, sorted({e.get("event") for e in tasks[tid]}))
