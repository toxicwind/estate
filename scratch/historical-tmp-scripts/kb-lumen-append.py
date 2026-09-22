import sys
from pathlib import Path
kb = Path(sys.argv[1])
lines = kb.read_text().splitlines(keepends=True)
row = ("| lumen | Squawk feed UI readability: keeper-driven visual audit (CDP :9223) of /squawk-feed/ui "
       "at desktop 1440x900 + mobile 390x844; root-caused empty bodies (pre-HMAC msgs fail verify_on_read -> "
       "body withheld); fix = serve bodies flagged unverified + card-layout redesign | Lumen (Ember's crew) | "
       "DONE (2026-09-21) -- relay fix e5fdce9c95 (serve pre-HMAC plaintext flagged invalid, fail-closed on "
       "ciphertext; 12/12 feed tests OK), UI redesign cb6bd69f82 (cards, unverified badges, scroll-to-bottom, "
       "mobile, favicon); keeper-verified 1440x900 + 390x844, 0 console/page errors; deployed live :25135 |\n")
for i, l in enumerate(lines):
    if l.startswith("| tau-router-recon |"):
        lines.insert(i + 1, row)
        print("appended after tau-router-recon")
        break
else:
    print("anchor not found")
    sys.exit(1)
kb.write_text("".join(lines))
