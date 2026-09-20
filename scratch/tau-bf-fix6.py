#!/usr/bin/env python3
"""Fix batch 6: jj snapshot await, set_workspace_name removal, tree() Result, unified_diff_hunks array."""
import sys

BASE = "/home/toxic/tau-bf-20260914/tau/engine"
p = f"{BASE}/crates/pi-vcs/src/jj/ops.rs"

def edit_file(old, new, count=1, label=""):
    with open(p) as f:
        content = f.read()
    n = content.count(old)
    if n != count:
        print(f"FAIL [{label}]: found {n}x, expected {count}x")
        sys.exit(1)
    content = content.replace(old, new, count)
    with open(p, "w") as f:
        f.write(content)
    print(f"OK [{label}]")

# 1. snapshot returns Future<(MergedTreeId, SnapshotStats)> - await and use returned id
edit_file(
"""\tlocked_workspace
\t\t.locked_wc()
\t\t.snapshot(&options)
\t\t.map_err(|err| Error::backend("jj snapshot", err))?;
\tlet new_tree_id = locked_workspace.locked_wc().current_tree_id().clone();""",
"""\tlet (new_tree_id, _stats) = locked_workspace
\t\t.locked_wc()
\t\t.snapshot(&options)
\t\t.await
\t\t.map_err(|err| Error::backend("jj snapshot", err))?;""",
label="snapshot await")

# 2. Transaction::set_workspace_name was removed in jj-lib 0.35 - delete the call
edit_file(
"""\t\tlet mut transaction = repo.start_transaction();
\t\ttransaction.set_workspace_name(&workspace_name);
\t\ttransaction.set_is_snapshot(true);""",
"""\t\tlet mut transaction = repo.start_transaction();
\t\ttransaction.set_is_snapshot(true);""",
label="set_workspace_name removed")

# 3. working_copy_trees: commit.tree() returns Result
edit_file(
"""\tlet parent_tree = commit
\t\t.parent_tree(repo)
\t\t\t\t.map_err(|err| Error::backend(context, err))?;
\tOk(Some((parent_tree, commit.tree())))""",
"""\tlet parent_tree = commit
\t\t.parent_tree(repo)
\t\t\t\t.map_err(|err| Error::backend(context, err))?;
\tlet tree = commit
\t\t.tree()
\t\t\t.map_err(|err| Error::backend(context, err))?;
\tOk(Some((parent_tree, tree)))""",
label="working_copy_trees tree Result")

# 4. jj files: commit.tree() returns Result
edit_file(
"""\t\t\t\tOk(tree_entries(&commit.tree(), "jj files")?""",
"""\t\t\t\tlet tree = commit.tree().map_err(|err| Error::backend("jj files", err))?;
\t\t\t\tOk(tree_entries(&tree, "jj files")?""",
label="jj files tree Result")

# 5. unified_diff_hunks takes [&BStr; 2], not Diff::new (2 occurrences)
with open(p) as f:
    c = f.read()
old = "Diff::new(before_part.content.contents.as_ref(), after_part.content.contents.as_ref())"
new = "[before_part.content.contents.as_ref(), after_part.content.contents.as_ref()]"
n = c.count(old)
c = c.replace(old, new)
with open(p, "w") as f:
    f.write(c)
print(f"OK [unified_diff_hunks array]: {n}x")
if n != 2:
    print("FAIL: expected 2"); sys.exit(1)

print("FIX-6 DONE")
