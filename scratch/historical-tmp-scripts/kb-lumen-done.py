import sys
from pathlib import Path
kb = Path(sys.argv[1])
lines = kb.read_text().splitlines(keepends=True)
for i, l in enumerate(lines):
    if l.startswith("| lumen |"):
        parts = l.rstrip("\n").split(" | ")
        parts[-1] = ("DONE (2026-09-21) -- relay fix e5fdce9c95 (serve pre-HMAC plaintext "
                     "flagged invalid, fail-closed on ciphertext; 12/12 feed tests OK), UI "
                     "redesign cb6bd69f82 (cards, unverified badges, scroll-to-bottom, mobile, "
                     "favicon); keeper-verified 1440x900 + 390x844, 0 console/page errors; "
                     "deployed live :25135 |")
        lines[i] = " | ".join(parts) + "\n"
        print("marked DONE")
        break
else:
    print("lumen row not found")
    sys.exit(1)
kb.write_text("".join(lines))
