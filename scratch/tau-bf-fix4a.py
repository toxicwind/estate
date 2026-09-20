#!/usr/bin/env python3
"""Fix batch 4: remaining compile errors."""
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

# --- write_commit: accept Into<Signature> for flexibility
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

# --- mutate.rs: use head_peel_to_id, fix peel_to_id, fix write_commit call, fix set_config_file
p = f"{BASE}/crates/pi-vcs/src/git/mutate.rs"
edit_file(p,
"""use super::{
\tGitRepo, normalize_path, write_commit,
""",
"""use super::{
\tGitRepo, head_peel_to_id, normalize_path, write_commit,
""",
label="mutate import head_peel_to_id")

edit_file(p,
"""\t\tlet id = write_commit(&repo, &committer, &author, &message, tree, &parents)
\t\t\t.map_err(|err| Error::backend("git commit", err))?;""",
"""\t\tlet id = write_commit(&repo, committer, author, &message, tree, &parents)
\t\t\t.map_err(|err| Error::backend("git commit", err))?;""",
label="mutate write_commit call")

# head.try_peel_to_id() -> head_peel_to_id(head)
with open(p) as f:
    c = f.read()
n = c.count(".try_peel_to_id()")
c = c.replace(".try_peel_to_id()", "")
# Now fix the two call sites: they were `head\n.try_peel_to_id()` and `...head()\n...\n.try_peel_to_id()`
# Site 1: `let old_commit = head\n.map_err...` - actually let's do targeted
with open(p, "w") as f:
    f.write(c)
print(f"OK [try_peel_to_id removed]: {n}x")

# --- patch.rs: write_commit takes owned Signature now
p = f"{BASE}/crates/pi-vcs/src/git/patch.rs"
with open(p) as f:
    c = f.read()
c = c.replace("""\t\tlet index_commit = write_commit(
\t\t\t&repo,
\t\t\t&committer,
\t\t\t&author,""", """\t\tlet index_commit = write_commit(
\t\t\t&repo,
\t\t\tcommitter.clone(),
\t\t\tauthor.clone(),""")
c = c.replace("""\t\tlet untracked_commit = write_commit(
\t\t\t&repo,
\t\t\t&committer,
\t\t\t&author,""", """\t\tlet untracked_commit = write_commit(
\t\t\t&repo,
\t\t\tcommitter.clone(),
\t\t\tauthor.clone(),""")
c = c.replace("""\t\tlet stash_commit = write_commit(
\t\t\t&repo,
\t\t\t&committer,
\t\t\t&author,""", """\t\tlet stash_commit = write_commit(
\t\t\t&repo,
\t\t\tcommitter,
\t\t\tauthor,""")
with open(p, "w") as f:
    f.write(c)
print("OK [patch write_commit owned sigs]")

print("FIX-4 PART 1 DONE")
