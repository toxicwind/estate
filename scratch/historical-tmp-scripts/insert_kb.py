import sys

path = "/tmp/benchlink-kb/docs/fleet-knowledgebase.md"
with open(path) as f:
    lines = f.readlines()

rows = [
    "| router-proof | head-to-head router benchmark: sovereign-router :25104 (sovereign/free) vs dumb direct :25100 (pinned north-mini-code:free); 180 requests + 60 judge calls, EXACT/QUALITY/CODE prompt types; verdict: intelligent router wins on availability 3.4-6.3x via failover under dead keypool (75x 502 on dumb route); raw data projects/openrouter-probe/router-proof-20260921.json; doc ROUTER_PROOF.md on nim-probe-20260920 @ 8d7f3d24 | Ember (Ember's crew) | DONE (2026-09-21) |\n",
    "| benchlink | router benchmark inventory + bench-based wiring: bench-priors.json generator (GuideLLM v3 quality + MODEL-MAX liveness/latency + router-proof availability signal) feeding sovereign-router Elo prior seeding; hot-reload via /admin/reload + SIGHUP (untouched providers keep live-learned Elo); live outcomes keep updating Elo | benchlink (Ember's crew) | RUNNING (2026-09-21) |\n",
]

# insert after the last crew row (line 169, 1-indexed) -> index 169 in 0-indexed lines list
assert lines[168].startswith("| end4-corrective"), "anchor moved: " + lines[168][:40]
lines[169:169] = rows

with open(path, "w") as f:
    f.writelines(lines)
print("inserted", len(rows), "rows")
