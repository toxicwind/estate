#!/usr/bin/env python3
"""Fix batch 9: test errors - clone_candidates Vec, init_internal_git sync."""
import sys

BASE = "/home/toxic/tau-bf-20260914/tau/engine"

# --- pi-iso: clone_candidates returns Vec ---
p = f"{BASE}/crates/pi-iso/src/lib.rs"
with open(p) as f:
    c = f.read()
old = """pub fn clone_candidates(preferred: Option<BackendKind>) -> impl Iterator<Item = BackendKind> {
\tlet mut seen = std::collections::HashSet::new();
\tpreferred
\t\t.into_iter()
\t\t.chain(auto_order().iter().copied())
\t\t.filter(move |kind| seen.insert(*kind))
}"""
new = """pub fn clone_candidates(preferred: Option<BackendKind>) -> Vec<BackendKind> {
\tlet mut seen = std::collections::HashSet::new();
\tpreferred
\t\t.into_iter()
\t\t.chain(auto_order().iter().copied())
\t\t.filter(|kind| seen.insert(*kind))
\t\t.collect()
}"""
if c.count(old) != 1:
    print("FAIL: clone_candidates"); sys.exit(1)
c = c.replace(old, new)
with open(p, "w") as f:
    f.write(c)
print("OK [clone_candidates Vec]")

# --- jj/ops.rs test: init_internal_git is sync with 2 args ---
p = f"{BASE}/crates/pi-vcs/src/jj/ops.rs"
with open(p) as f:
    c = f.read()
old = """\t\tlet settings = user_settings().unwrap();
\t\tlet runtime = tokio::runtime::Builder::new_current_thread()
\t\t\t.enable_all()
\t\t\t.build()
\t\t\t.unwrap();
\t\truntime
\t\t\t.block_on(Workspace::init_internal_git(&settings, root, gix::hash::Kind::Sha1))
\t\t\t.unwrap();"""
new = """\t\tlet settings = user_settings().unwrap();
\t\tWorkspace::init_internal_git(&settings, root).unwrap();"""
if c.count(old) != 1:
    print("FAIL: init_internal_git test"); sys.exit(1)
c = c.replace(old, new)
with open(p, "w") as f:
    f.write(c)
print("OK [init_internal_git test]")

print("FIX-9 DONE")
