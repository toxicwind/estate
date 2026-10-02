#!/usr/bin/env python3
"""Tau bruteforce fix batch 2 (robust): jj/ops.rs sync API adaptations."""
import re, sys

P = "/home/toxic/tau-bf-20260914/tau/engine/crates/pi-vcs/src/jj/ops.rs"
with open(P) as f:
    src = f.read()

def rep(old, new, count=1, label=""):
    global src
    n = src.count(old)
    if n != count:
        print(f"FAIL [{label}]: found {n}x, expected {count}x")
        print(old[:350])
        sys.exit(1)
    src = src.replace(old, new, count)
    print(f"OK [{label}]")

# --- renames: get_commit_async -> get_commit (all 4 occurrences)
n = src.count(".get_commit_async(")
src = src.replace(".get_commit_async(", ".get_commit(")
print(f"OK [get_commit_async rename]: {n}x")

# --- delete .await lines that directly follow these sync calls
# Each pattern: <call line>\n<tabs>.await\n  ->  <call line>\n
sync_calls = [
    ".is_ancestor(id, &wc_id)",
    ".heads(&mut candidate_iter)",
    ".get_commit(wc_id)",
    ".get_commit(&initial_wc_id)",
    ".load_at_head()",
    ".start_working_copy_mutation()",
    ".load_at(&operation)",
    ".parent_tree(repo)",
]
for call in sync_calls:
    pat = re.compile(r"(" + re.escape(call) + r"\n[ \t]*)\.await\n")
    src, n = pat.subn(r"\1", src)
    print(f"OK [await drop after {call}]: {n}x")
    if n == 0:
        print(f"FAIL: no await dropped after {call}")
        sys.exit(1)

# --- check_stale(...)\n.await  (await on its own line after closing paren)
pat = re.compile(r"(\t\)\n)(\t\.await\n)(\t\.map_err\(\|err\| Error::backend\(\"jj snapshot\", err\)\)\?)")
src, n = pat.subn(r"\1\3", src)
print(f"OK [check_stale await]: {n}x")
if n != 1:
    print("FAIL: check_stale await"); sys.exit(1)

# --- parents(): restructure for-loop (iterator of Results)
rep(
"""\t\tfor parent in commit
\t\t\t.parents()
\t\t\t.await
\t\t\t.map_err(|err| Error::backend(context, err))?
\t\t{
\t\t\tif parent.id() != root_id && queued.insert(parent.id().clone()) {
\t\t\t\theap.push((parent.committer().timestamp, parent));
\t\t\t}
\t\t}""",
"""\t\tfor parent in commit.parents() {
\t\t\tlet parent = parent.map_err(|err| Error::backend(context, err))?;
\t\t\tif parent.id() != root_id && queued.insert(parent.id().clone()) {
\t\t\t\theap.push((parent.committer().timestamp, parent));
\t\t\t}
\t\t}""",
label="parents loop")

# --- visible_with_offsets -> explicit visibility filter
rep(
"""\t\tif let PrefixResolution::SingleMatch(targets) = resolution {
\t\t\tlet mut visible = targets.visible_with_offsets().map(|(_, id)| id.clone());
\t\t\tlet first = visible.next();
\t\t\tif first.is_some() && visible.next().is_none() {
\t\t\t\treturn Ok(first);
\t\t\t}
\t\t}""",
"""\t\tif let PrefixResolution::SingleMatch(targets) = resolution {
\t\t\tlet index = repo.index();
\t\t\tlet heads = repo.view().heads();
\t\t\tlet mut visible = targets.into_iter().filter(|id| {
\t\t\t\theads.contains(id)
\t\t\t\t\t|| heads
\t\t\t\t\t\t.iter()
\t\t\t\t\t\t.any(|head| index.is_ancestor(id, head).unwrap_or(false))
\t\t\t});
\t\t\tlet first = visible.next();
\t\t\tif first.is_some() && visible.next().is_none() {
\t\t\t\treturn Ok(first);
\t\t\t}
\t\t}""",
label="visible filter")

# --- SnapshotOptions: drop force_tracking_matcher
rep(
"""\tlet everything = EverythingMatcher;
\tlet nothing = NothingMatcher;
\tlet options = SnapshotOptions {
\t\tbase_ignores:           GitIgnoreFile::empty(),
\t\tprogress:               None,
\t\tstart_tracking_matcher: &everything,
\t\tforce_tracking_matcher: &nothing,
\t\tmax_new_file_size:      1024 * 1024,
\t};""",
"""\tlet everything = EverythingMatcher;
\tlet options = SnapshotOptions {
\t\tbase_ignores:           GitIgnoreFile::empty(),
\t\tprogress:               None,
\t\tstart_tracking_matcher: &everything,
\t\tmax_new_file_size:      1024 * 1024,
\t};""",
label="SnapshotOptions")

# --- snapshot() returns (bool, SnapshotStats); use current_tree_id; sync tx fns
rep(
"""\tlet (new_tree, _) = locked_workspace
\t\t.locked_wc()
\t\t.snapshot(&options)
\t\t.await
\t\t.map_err(|err| Error::backend("jj snapshot", err))?;
\tlet repo = if new_tree.tree_ids_and_labels() == wc_commit.tree().tree_ids_and_labels() {
\t\trepo
\t} else {
\t\tlet mut transaction = repo.start_transaction();
\t\ttransaction.set_workspace_name(&workspace_name);
\t\ttransaction.set_is_snapshot(true);
\t\tlet new_commit = transaction
\t\t\t.repo_mut()
\t\t\t.rewrite_commit(&wc_commit)
\t\t\t.set_tree(new_tree)
\t\t\t.write()
\t\t\t.await
\t\t\t.map_err(|err| Error::backend("jj snapshot", err))?;
\t\ttransaction
\t\t\t.repo_mut()
\t\t\t.set_wc_commit(workspace_name, new_commit.id().clone())
\t\t\t.map_err(|err| Error::backend("jj snapshot", err))?;
\t\ttransaction
\t\t\t.repo_mut()
\t\t\t.rebase_descendants()
\t\t\t.await
\t\t\t.map_err(|err| Error::backend("jj snapshot", err))?;
\t\ttransaction
\t\t\t.commit("snapshot working copy")
\t\t\t.await
\t\t\t.map_err(|err| Error::backend("jj snapshot", err))?
\t};
\tlocked_workspace
\t\t.finish(repo.op_id().clone())
\t\t.await
\t\t.map_err(|err| Error::backend("jj snapshot", err))?;""",
"""\tlocked_workspace
\t\t.locked_wc()
\t\t.snapshot(&options)
\t\t.map_err(|err| Error::backend("jj snapshot", err))?;
\tlet new_tree_id = locked_workspace.locked_wc().current_tree_id().clone();
\tlet repo = if new_tree_id == *wc_commit.tree_id() {
\t\trepo
\t} else {
\t\tlet mut transaction = repo.start_transaction();
\t\ttransaction.set_workspace_name(&workspace_name);
\t\ttransaction.set_is_snapshot(true);
\t\tlet new_commit = transaction
\t\t\t.repo_mut()
\t\t\t.rewrite_commit(&wc_commit)
\t\t\t.set_tree_id(new_tree_id)
\t\t\t.write()
\t\t\t.map_err(|err| Error::backend("jj snapshot", err))?;
\t\ttransaction
\t\t\t.repo_mut()
\t\t\t.set_wc_commit(workspace_name, new_commit.id().clone())
\t\t\t.map_err(|err| Error::backend("jj snapshot", err))?;
\t\ttransaction
\t\t\t.repo_mut()
\t\t\t.rebase_descendants()
\t\t\t.map_err(|err| Error::backend("jj snapshot", err))?;
\t\ttransaction
\t\t\t.commit("snapshot working copy")
\t\t\t.map_err(|err| Error::backend("jj snapshot", err))?
\t};
\tlocked_workspace
\t\t.finish(repo.op_id().clone())
\t\t.map_err(|err| Error::backend("jj snapshot", err))?;""",
label="snapshot block")

# --- git_diff_part is sync (2 occurrences)
pat = re.compile(r"(git_diff_part\(&change\.(?:before|after)_path, (?:before|after)_value, options\)\n[ \t]*)\.await\n")
src, n = pat.subn(r"\1", src)
print(f"OK [git_diff_part await]: {n}x")
if n != 2:
    print("FAIL: git_diff_part await"); sys.exit(1)

with open(P, "w") as f:
    f.write(src)
print("ALL FIX-2 EDITS APPLIED")
