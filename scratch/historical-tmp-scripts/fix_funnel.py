#!/usr/bin/env python3
# fix_funnel_parser.py — one-char fix: ${entry#*\t} strips only to the FIRST
# tab, but MAP entries use TWO tabs, leaving a leading tab in the target URL
# and making every NEW mount fail with "invalid control character in URL".
# ${entry##*\t} (longest match) strips through the last tab. Idempotent.
path = "/home/toxic/sovereign/projects/yote/ops/funnel-map.sh"
c = open(path).read()
old = 'target="${entry#*\t}"'
new = 'target="${entry##*\t}"'
if old in c:
    c = c.replace(old, new)
    open(path, "w").write(c)
    print("parser fixed: # -> ##")
else:
    print("already fixed" if new in c else "PATTERN MISSING")
