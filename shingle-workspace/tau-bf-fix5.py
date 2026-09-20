#!/usr/bin/env python3
"""Fix batch 5: head_tree object lookup, read.rs peel, set_config_file lifetime."""
import sys

BASE = "/home/toxic/tau-bf-20260914/tau/engine"

def edit_file(path, old, new, count=1, label=""):
    with open(path) as f:
        content = f.read()
    n = content.count(old)
    if n != count:
        print(f"FAIL [{label}] {path}: found {n}x, expected {count}x")
        sys.exit(1)
    content = content.replace(old, new, count)
    with open(path, "w") as f:
        f.write(content)
    print(f"OK [{label}]")

# --- mutate.rs: head_tree - repo.find_object instead of id.object() ---
p = f"{BASE}/crates/pi-vcs/src/git/mutate.rs"
edit_file(p,
"""\t\tSome(id) => Ok(Some(
\t\t\tid.object()
\t\t\t\t.map_err(|e| Error::backend("git reset", e))?
\t\t\t\t.peel_to_commit()
\t\t\t\t.map_err(|e| Error::backend("git reset", e))?
\t\t\t\t.tree_id()
\t\t\t\t.map_err(|e| Error::backend("git reset", e))?
\t\t\t\t.detach(),
\t\t)),""",
"""\t\tSome(id) => Ok(Some(
\t\t\trepo
\t\t\t\t.find_object(id)
\t\t\t\t.map_err(|e| Error::backend("git reset", e))?
\t\t\t\t.peel_to_commit()
\t\t\t\t.map_err(|e| Error::backend("git reset", e))?
\t\t\t\t.tree_id()
\t\t\t\t.map_err(|e| Error::backend("git reset", e))?
\t\t\t\t.detach(),
\t\t)),""",
label="head_tree find_object")

# --- mutate.rs: set_config_file - bind key ref to extend temporary lifetime ---
edit_file(p,
"""\tlet mut config: gix::config::File<'_> = if path.exists() {
\t\tgix::config::File::from_path_no_includes(path.to_owned(), gix::config::Source::Local)
\t\t\t.map_err(|e| Error::backend("git config", e))?
\t} else {
\t\tgix::config::File::default()
\t};
\tconfig
\t\t.set_raw_value(&key, value)
\t\t.map_err(|e| Error::backend("git config", e))?;""",
"""\tlet mut config: gix::config::File<'_> = if path.exists() {
\t\tgix::config::File::from_path_no_includes(path.to_owned(), gix::config::Source::Local)
\t\t\t.map_err(|e| Error::backend("git config", e))?
\t} else {
\t\tgix::config::File::default()
\t};
\tlet key_ref = &key;
\tconfig
\t\t.set_raw_value(key_ref, value)
\t\t.map_err(|e| Error::backend("git config", e))?;""",
label="set_config_file key_ref")

# --- read.rs: peel_to_id -> peel_to_id_in_place ---
p = f"{BASE}/crates/pi-vcs/src/git/read.rs"
with open(p) as f:
    c = f.read()
n = c.count(".peel_to_id()")
c = c.replace(".peel_to_id()", ".peel_to_id_in_place()")
with open(p, "w") as f:
    f.write(c)
print(f"OK [read.rs peel_to_id_in_place]: {n}x")
if n != 1:
    print("FAIL: expected 1"); sys.exit(1)

print("FIX-5 DONE")
