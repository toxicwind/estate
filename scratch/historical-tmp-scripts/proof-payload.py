import json, time, hashlib
from pathlib import Path
# LIVE PROOF payload (autonomy-weaver, 2026-09-21): verifies the market loop
# itself is alive by reading the live ledger — real behavior, no network.
ledger = Path("/home/toxic/sovereign/agents/oracle-market/ledger/ledger.jsonl")
now = time.time()
recent = 0
by_event = {}
for line in ledger.open():
    try:
        d = json.loads(line)
    except Exception:
        continue
    ev = d.get("event", "?")
    by_event[ev] = by_event.get(ev, 0) + 1
    if now - d.get("ts", 0) < 3600:
        recent += 1
readme = Path("/home/toxic/sovereign/agents/oracle-market/README.md")
h = hashlib.sha256(readme.read_bytes()).hexdigest()[:16]
assert recent > 0, "no ledger activity in the last hour - loop is dead"
Path("proof-report.txt").write_text(
    "recent_events_1h=%d\nreadme_sha16=%s\nledger_events=%s\n" % (recent, h, sorted(by_event)[:8]))
print("PROOF_OK recent_1h=%d readme=%s" % (recent, h))
