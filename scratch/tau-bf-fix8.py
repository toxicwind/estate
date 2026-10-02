#!/usr/bin/env python3
"""Fix batch 8: clean up warnings (tabs)."""
import sys

BASE = "/home/toxic/tau-bf-20260914/tau/engine"

p = f"{BASE}/crates/pi-vcs/src/jj/ops.rs"
with open(p) as f:
    c = f.read()

old_imp = "\tmatchers::{EverythingMatcher, NothingMatcher},"
new_imp = "\tmatchers::EverythingMatcher,"
if c.count(old_imp) != 1:
    print("FAIL: NothingMatcher import"); sys.exit(1)
c = c.replace(old_imp, new_imp)

old_imp2 = "\tmerge::{Diff, MergedTreeValue},"
new_imp2 = "\tmerge::MergedTreeValue,"
if c.count(old_imp2) != 1:
    print("FAIL: Diff import"); sys.exit(1)
c = c.replace(old_imp2, new_imp2)

old_sig = "\tbefore_tree: &MergedTree,"
new_sig = "\t_before_tree: &MergedTree,"
if c.count(old_sig) != 1:
    print("FAIL: before_tree param"); sys.exit(1)
c = c.replace(old_sig, new_sig)

old_sig2 = "\tafter_tree: &MergedTree,"
new_sig2 = "\t_after_tree: &MergedTree,"
if c.count(old_sig2) != 1:
    print("FAIL: after_tree param"); sys.exit(1)
c = c.replace(old_sig2, new_sig2)

with open(p, "w") as f:
    f.write(c)
print("OK [jj/ops.rs warnings]")

p = f"{BASE}/crates/pi-vcs/src/git/mutate.rs"
with open(p) as f:
    c = f.read()
old_mut = "\t\tlet mut head = repo\n\t\t\t.head()\n\t\t\t.map_err(|err| Error::backend(\"git commit\", err))?;"
new_mut = "\t\tlet head = repo\n\t\t\t.head()\n\t\t\t.map_err(|err| Error::backend(\"git commit\", err))?;"
if c.count(old_mut) != 1:
    print("FAIL: mut head"); sys.exit(1)
c = c.replace(old_mut, new_mut)
with open(p, "w") as f:
    f.write(c)
print("OK [mutate.rs mut]")

print("FIX-8 DONE")
