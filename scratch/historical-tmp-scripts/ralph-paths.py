import json, datetime, os
from collections import defaultdict

LED = "/home/toxic/sovereign/agents/oracle-market/ledger/ledger.jsonl"
WORK = "/home/toxic/sovereign/agents/oracle-market/work"

settles = [json.loads(l) for l in open(LED)
           if json.loads(l).get("event") == "settled"]

def path_of(task_id, winner):
    b = (winner or "").replace("bidder-", "")
    d = os.path.join(WORK, b, task_id)
    if os.path.isfile(os.path.join(d, "ralph-invocation.txt")):
        return "ralph"
    if os.path.isdir(d):
        return "python"
    return "gone"

d = defaultdict(lambda: defaultdict(lambda: [0, 0]))
for s in settles:
    hr = datetime.datetime.fromtimestamp(
        s["ts"], datetime.timezone.utc).strftime("%m-%d %H")
    p = path_of(s["task_id"], s.get("winner"))
    d[hr][p][1] += 1
    if s.get("verified") and s.get("success"):
        d[hr][p][0] += 1

tot = defaultdict(lambda: [0, 0])
for k in sorted(d):
    for p, v in d[k].items():
        tot[p][1] += v[1]
        tot[p][0] += v[0]
    print(k, {p: "%d/%d" % tuple(v) for p, v in d[k].items()})
print("TOTALS:", {p: "%d/%d (%.0f%%)" % (v[0], v[1], 100.0*v[0]/max(1, v[1]))
                  for p, v in tot.items()})
