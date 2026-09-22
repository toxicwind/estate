import json, datetime
from collections import defaultdict

tasks = {}
for l in open("/home/toxic/sovereign/agents/oracle-market/ledger/ledger.jsonl"):
    e = json.loads(l)
    if e.get("event") in ("task_open", "task-open", "open", "task-posted"):
        tasks[e.get("task_id")] = e.get("exec_mode", e.get("mode", "?"))

settles = [json.loads(l) for l in open(
    "/home/toxic/sovereign/agents/oracle-market/ledger/ledger.jsonl")
    if json.loads(l).get("event") == "settled"]

d = defaultdict(lambda: defaultdict(lambda: [0, 0]))
for s in settles:
    hr = datetime.datetime.fromtimestamp(
        s["ts"], datetime.timezone.utc).strftime("%m-%d %H")
    m = tasks.get(s["task_id"], "?")
    d[hr][m][1] += 1
    if s.get("verified") and s.get("success"):
        d[hr][m][0] += 1

for k in sorted(d):
    modes = {m: "%d/%d" % tuple(v) for m, v in d[k].items()}
    print(k, modes)

print("--- task_open event names seen ---")
names = defaultdict(int)
for l in open("/home/toxic/sovereign/agents/oracle-market/ledger/ledger.jsonl"):
    e = json.loads(l)
    names[e.get("event")] += 1
for n, c in sorted(names.items(), key=lambda x: -x[1])[:12]:
    print(n, c)
