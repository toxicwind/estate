import json, sys
L = "/home/toxic/sovereign/agents/oracle-market/ledger/ledger.jsonl"
tid = "loop-liveness-proof-20260921"
for line in open(L):
    try:
        d = json.loads(line)
    except Exception:
        continue
    if d.get("task_id") == tid:
        ev = d.get("event")
        extra = ""
        if ev == "bid_accepted":
            extra = " bidder=%s amt=%s" % (d.get("bidder"), d.get("amount"))
        elif ev == "assigned":
            extra = " winner=%s price=%s" % (d.get("winner"), d.get("price_paid"))
        elif ev == "settled":
            extra = " winner=%s verified=%s success=%s" % (d.get("winner"), d.get("verified"), d.get("success"))
        elif ev == "slashed":
            extra = " bidder=%s reason=%s" % (d.get("bidder"), d.get("reason"))
        print("%s %s%s" % (d.get("ts"), ev, extra))
