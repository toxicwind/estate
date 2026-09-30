p = "/tmp/kb-wt/docs/fleet-knowledgebase.md"
t = open(p).read()
old = "sovereign-projects  (origin/main, ls-remote verified)"
new = "sovereign-projects 858647e758 (origin/main, ls-remote verified)"
assert old in t, "anchor not found"
open(p, "w").write(t.replace(old, new, 1))
print("row repaired")
