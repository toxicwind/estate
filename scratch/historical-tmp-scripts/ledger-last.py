import json
L = "/home/toxic/sovereign/agents/oracle-market/ledger/ledger.jsonl"
last_tid = None
for line in open(L):
    try:
        d = json.loads(line)
    except Exception:
        continue
    if d.get("task_id"):
        last_tid = d["task_id"]
print("last task:", last_tid)
for line in open(L):
    d = json.loads(line)
    if d.get("task_id") == last_tid:
        print(json.dumps(d, indent=1)[:1800])
        print("-----")
