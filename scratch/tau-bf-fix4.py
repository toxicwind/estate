#!/usr/bin/env python3
"""Fix batch 4: remaining compile errors (precise)."""
import re, sys

BASE = "/home/toxic/tau-bf-20260914/tau/engine"

def edit_file(path, old, new, count=1, label=""):
    with open(path) as f:
        content = f.read()
    n = content.count(old)
    if n != count:
        print(f"FAIL [{label}] {path}: found {n}x, expected {count}x")
        print(old[:400])
        sys.exit(1)
    content = content.replace(old, new, count)
    with open(path, "w") as f:
        f.write(content)
    print(f"OK [{label}]")

# --- git/mod.rs: write_commit generic + head_peel_to_id helper
p = f"{BASE}/crates/pi-vcs/src/git/mod.rs"
edit_file(p,
"""pub(crate) fn write_commit(
\trepo: &gix::Repository,
\tcommitter: &gix::actor::Signature,
\tauthor: &gix::actor::Signature,
\tmessage: &str,
\ttree: gix::hash::ObjectId,
\tparents: &[gix::hash::ObjectId],
) -> Result<gix::hash::ObjectId, gix::object::write::Error> {
\tlet commit = gix::objs::Commit {
\t\tmessage: message.into(),
\t\ttree,
\t\tauthor: author.clone(),
\t\tcommitter: committer.clone(),
\t\tencoding: None,
\t\tparents: parents.iter().copied().collect(),
\t\textra_headers: Vec::new(),
\t};
\trepo.write_object(&commit).map(|id| id.detach())
}""",
"""pub(crate) fn write_commit(
\trepo: &gix::Repository,
\tcommitter: impl Into<gix::actor::Signature>,
\tauthor: impl Into<gix::actor::Signature>,
\tmessage: &str,
\ttree: gix::hash::ObjectId,
\tparents: &[gix::hash::ObjectId],
) -> Result<gix::hash::ObjectId, gix::object::write::Error> {
\tlet commit = gix::objs::Commit {
\t\tmessage: message.into(),
\t\ttree,
\t\tauthor: author.into(),
\t\tcommitter: committer.into(),
\t\tencoding: None,
\t\tparents: parents.iter().copied().collect(),
\t\textra_headers: Vec::new(),
\t};
\trepo.write_object(&commit).map(|id| id.detach())
}

/// Peel `HEAD` to the commit id it resolves to, or `None` if unborn.
///
/// Newer `gix` removed `Head::try_peel_to_id`; a symbolic `HEAD` is peeled
/// via its referent reference, a detached `HEAD` yields its id directly.
pub(crate) fn head_peel_to_id(
\thead: gix::Head<'_>,
) -> Result<Option<gix::hash::ObjectId>, gix::reference::peel::Error> {
\tlet direct = head.id().map(|id| id.detach());
\tmatch head.try_into_referent() {
\t\tSome(mut reference) => reference.peel_to_id_in_place().map(|id| Some(id.detach())),
\t\tNone => Ok(direct),
\t}
}""",
label="write_commit generic + head_peel_to_id")

# --- mutate.rs ---
p = f"{BASE}/crates/pi-vcs/src/git/mutate.rs"
edit_file(p,
"""use super::{
\tGitRepo, normalize_path, write_commit,
""",
"""use super::{
\tGitRepo, head_peel_to_id, normalize_path, write_commit,
""",
label="mutate import")

edit_file(p,
"""\t\tlet id = write_commit(&repo, &committer, &author, &message, tree, &parents)
\t\t\t.map_err(|err| Error::backend("git commit", err))?;""",
"""\t\tlet id = write_commit(&repo, committer, author, &message, tree, &parents)
\t\t\t.map_err(|err| Error::backend("git commit", err))?;""",
label="mutate write_commit call")

edit_file(p,
"""\t\tlet old_commit = head
\t\t\t.try_peel_to_id()
\t\t\t.map_err(|err| Error::backend("git commit", err))?
\t\t\t.map(|id| id.detach());""",
"""\t\tlet old_commit = head_peel_to_id(head)
\t\t\t.map_err(|err| Error::backend("git commit", err))?;""",
label="mutate head peel 1")

edit_file(p,
"""\tmatch repo
\t\t.head()
\t\t.map_err(|e| Error::backend("git reset", e))?
\t\t.try_peel_to_id()
\t\t.map_err(|e| Error::backend("git reset", e))?
\t{""",
"""\tmatch head_peel_to_id(
\t\trepo
\t\t\t.head()
\t\t\t.map_err(|e| Error::backend("git reset", e))?,
\t)
\t.map_err(|e| Error::backend("git reset", e))?
\t{""",
label="mutate head peel 2")

with open(p) as f:
    c = f.read()
n = c.count(".peel_to_id()")
c = c.replace(".peel_to_id()", ".peel_to_id_in_place()")
with open(p, "w") as f:
    f.write(c)
print(f"OK [peel_to_id_in_place]: {n}x")
if n != 2:
    print("FAIL: expected 2 peel_to_id"); sys.exit(1)

edit_file(p,
"""fn set_config_file(path: &Path, key: &str, value: &str) -> Result<()> {
\tlet mut config = if path.exists() {""",
"""fn set_config_file(path: &Path, key: &str, value: &str) -> Result<()> {
\tlet mut config: gix::config::File<'_> = if path.exists() {""",
label="set_config_file lifetime")

# --- patch.rs: write_commit takes owned Signature via Into ---
p = f"{BASE}/crates/pi-vcs/src/git/patch.rs"
with open(p) as f:
    c = f.read()
c = c.replace(
"\t\tlet index_commit = write_commit(\n\t\t\t&repo,\n\t\t\t&committer,\n\t\t\t&author,",
"\t\tlet index_commit = write_commit(\n\t\t\t&repo,\n\t\t\tcommitter.clone(),\n\t\t\tauthor.clone(),")
c = c.replace(
"\t\tlet untracked_commit = write_commit(\n\t\t\t&repo,\n\t\t\t&committer,\n\t\t\t&author,",
"\t\tlet untracked_commit = write_commit(\n\t\t\t&repo,\n\t\t\tcommitter.clone(),\n\t\t\tauthor.clone(),")
c = c.replace(
"\t\tlet stash_commit = write_commit(\n\t\t\t&repo,\n\t\t\t&committer,\n\t\t\t&author,",
"\t\tlet stash_commit = write_commit(\n\t\t\t&repo,\n\t\t\tcommitter,\n\t\t\tauthor,")
with open(p, "w") as f:
    f.write(c)
print("OK [patch write_commit owned sigs]")

# --- jj/ops.rs ---
p = f"{BASE}/crates/pi-vcs/src/jj/ops.rs"
with open(p) as f:
    c = f.read()
for call in [".get_commit(&wc_id)", ".get_commit(&commit_id)"]:
    pat = re.compile(r"(" + re.escape(call) + r"\n[ \t]*)\.await\n")
    c, n = pat.subn(r"\1", c)
    print(f"OK [await drop after {call}]: {n}x")
    if n == 0:
        print(f"FAIL: no await dropped after {call}"); sys.exit(1)
old_b = "\tlet before_value = materialize_tree_value(\n\t\trepo.store(),\n\t\t&change.before_path,\n\t\tchange.before.clone(),\n\t\tbefore_tree.labels(),\n\t)"
new_b = "\tlet before_value = materialize_tree_value(\n\t\trepo.store(),\n\t\t&change.before_path,\n\t\tchange.before.clone(),\n\t)"
if c.count(old_b) != 1:
    print("FAIL: before_value anchor"); sys.exit(1)
c = c.replace(old_b, new_b)
old_a = "\tlet after_value = materialize_tree_value(\n\t\trepo.store(),\n\t\t&change.after_path,\n\t\tchange.after.clone(),\n\t\tafter_tree.labels(),\n\t)"
new_a = "\tlet after_value = materialize_tree_value(\n\t\trepo.store(),\n\t\t&change.after_path,\n\t\tchange.after.clone(),\n\t)"
if c.count(old_a) != 1:
    print("FAIL: after_value anchor"); sys.exit(1)
c = c.replace(old_a, new_a)
with open(p, "w") as f:
    f.write(c)
print("OK [materialize_tree_value labels dropped]")

print("FIX-4 DONE")
