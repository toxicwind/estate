import sys
from pathlib import Path
kb = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/toxic/sovereign/docs/fleet-knowledgebase.md")
lines = kb.read_text().splitlines(keepends=True)
if any(l.startswith("| lumen |") for l in lines):
    print("row already present, skipping")
else:
    row = ("| lumen | Squawk feed UI readability: keeper-driven visual audit (CDP :9223) "
           "of /squawk-feed/ui at desktop 1600x900 + mobile 390x844; root-caused empty bodies "
           "(pre-HMAC msgs fail verify_on_read -> body withheld); fix = serve bodies flagged "
           "unverified + typography/layout redesign; deploy + keeper-verify both widths "
           "| Lumen (Ember's crew) | RUNNING (2026-09-21) |\n")
    idx = next(i for i, l in enumerate(lines) if l.startswith("| nightjar |"))
    lines.insert(idx + 1, row)
    kb.write_text("".join(lines))
    print("inserted lumen row after line", idx + 1)
