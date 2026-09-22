#!/usr/bin/env python3
"""Update the squawk-feed-perf KB row to DONE in a checked-out remote copy."""
import re, sys

src, dst = sys.argv[1], sys.argv[2]
s = open(src).read()
pat = re.compile(r"\| squawk-feed-perf \|[^\n]*\| RUNNING \(2026-09-21\) \|")
new = ("| squawk-feed-perf | Squawk feed + UI perf & hot-reload | "
       "Ember's crew (squawk lane) | DONE (2026-09-21) -- sovereign-projects "
       "8a9293184b: tail=N snapshots (UI boots in 1 request), numeric seq order, "
       "channel param honored, ghost-record cursor fix, tolerant frontmatter; "
       "tests 9+9 OK; live deploy verified (tail 8ms, park-wake 4ms, no-store UI) |")
s2, n = pat.subn(new, s)
assert n == 1, "replacements=%d" % n
open(dst, "w").write(s2)
print("edited OK")
