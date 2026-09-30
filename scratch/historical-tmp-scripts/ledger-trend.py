import json, time
L = "/home/toxic/sovereign/agents/oracle-market/ledger/ledger.jsonl"
now = time.time()
buckets = {"1h": (0, 0, 0), "6h": (0, 0, 0), "24h": (0, 0, 0), "all": (0, 0, 0)}
# (success, fail, slashed)
for line in open(L):
    try:
        d = json.loads(line)
    except Exception:
        continue
    ev = d.get("event")
    ts = d.get("ts", 0)
    age = now - ts
    for name, limit in (("1h", 3600), ("6h", 21600), ("24h", 86400), ("all", 1e18)):
        if age < limit:
            s, f, sl = buckets[name]
            if ev == "settled" and (d.get("success") or d.get("verified") is True or d.get("verified") == "True"):
                s += 1
            elif ev == "settled":
                f += 1
            elif ev == "slashed":
                sl += 1
            buckets[name] = (s, f, sl)
for k, (s, f, sl) in buckets.items():
    print(k, "success:", s, "fail-settle:", f, "slashed:", sl)
