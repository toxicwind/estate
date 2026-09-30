from pathlib import Path
p = Path("/home/toxic/.worktrees/vex-html/docs/fleet-knowledgebase.md")
t = p.read_text()
old = "| Vex (Ember's crew) | RUNNING |"
assert t.count(old) == 1, t.count(old)
new = ("| Vex (Ember's crew) | DONE (2026-09-21) -- commit 615a38c69a "
       "(origin/main, ls-remote verified): ui.html renderer first-class HTML, "
       "squawk_feed.py CORS, 2 new tests; proofs: 14/14 feed tests, 19/19 "
       "node renderer checks, live POST round-trip byte-identical (fleet seq "
       "12898), preflight 204 + ACAO live on :25135 |")
t = t.replace(old, new)
p.write_text(t)
print("KB row marked DONE")
