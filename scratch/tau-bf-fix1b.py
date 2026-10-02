#!/usr/bin/env python3
"""Tau bruteforce fix batch 1b: remaining edits (corrected anchors)."""
import sys

BASE = "/home/toxic/tau-bf-20260914/tau/engine"

def edit(path, old, new, count=1):
    with open(path) as f:
        content = f.read()
    n = content.count(old)
    if n < count:
        print(f"FAIL {path}: anchor found {n}x, expected >={count}")
        print("--- anchor start ---")
        print(old[:300])
        print("--- anchor end ---")
        sys.exit(1)
    content = content.replace(old, new, count)
    with open(path, "w") as f:
        f.write(content)
    print(f"OK {path}: replaced {count}x")

# ---------------------------------------------------------------- git/mutate.rs (2-tab indent)
p = f"{BASE}/crates/pi-vcs/src/git/mutate.rs"
edit(p,
"""\t\tlet commit = repo
\t\t\t.new_commit_as(committer, author, message, tree, parents)
\t\t\t.map_err(|err| Error::backend("git commit", err))?;
\t\tlet id = commit.id;""",
"""\t\tlet id = write_commit(&repo, &committer, &author, &message, tree, &parents)
\t\t\t.map_err(|err| Error::backend("git commit", err))?;""")

# ---------------------------------------------------------------- git/patch.rs
p = f"{BASE}/crates/pi-vcs/src/git/patch.rs"
edit(p,
"""use super::{GitRepo, mutate::update_reference, open::load_index_or_head};""",
"""use super::{GitRepo, mutate::update_reference, open::load_index_or_head, write_commit};""")
edit(p,
"""\t\tlet label = message.unwrap_or("WIP");
\t\tlet index_commit = repo
\t\t\t.new_commit(format!("index on HEAD: {label}"), index_tree, [head_id])
\t\t\t.map_err(|err| Error::backend("git stash index commit", err))?;
\t\tlet untracked_commit = repo
\t\t\t.new_commit("untracked files on HEAD", untracked_tree, std::iter::empty::<gix::ObjectId>())
\t\t\t.map_err(|err| Error::backend("git stash untracked commit", err))?;
\t\tlet stash_commit = repo
\t\t\t.new_commit(label, worktree_tree, [
\t\t\t\thead_id,
\t\t\t\tindex_commit.id().detach(),
\t\t\t\tuntracked_commit.id().detach(),
\t\t\t])
\t\t\t.map_err(|err| Error::backend("git stash commit", err))?;
\t\tupdate_stash_ref(
\t\t\t&repo,
\t\t\tstash_commit.id().detach(),""",
"""\t\tlet label = message.unwrap_or("WIP");
\t\tlet committer = repo
\t\t\t.committer()
\t\t\t.ok_or_else(|| Error::backend("git stash", "committer identity is not configured"))?
\t\t\t.map_err(|err| Error::backend("git stash", err))?;
\t\tlet author = repo
\t\t\t.author()
\t\t\t.ok_or_else(|| Error::backend("git stash", "author identity is not configured"))?
\t\t\t.map_err(|err| Error::backend("git stash", err))?;
\t\tlet index_commit = write_commit(
\t\t\t&repo,
\t\t\t&committer,
\t\t\t&author,
\t\t\t&format!("index on HEAD: {label}"),
\t\t\tindex_tree,
\t\t\t&[head_id],
\t\t)
\t\t.map_err(|err| Error::backend("git stash index commit", err))?;
\t\tlet untracked_commit = write_commit(
\t\t\t&repo,
\t\t\t&committer,
\t\t\t&author,
\t\t\t"untracked files on HEAD",
\t\t\tuntracked_tree,
\t\t\t&[],
\t\t)
\t\t.map_err(|err| Error::backend("git stash untracked commit", err))?;
\t\tlet stash_commit = write_commit(
\t\t\t&repo,
\t\t\t&committer,
\t\t\t&author,
\t\t\tlabel,
\t\t\tworktree_tree,
\t\t\t&[head_id, index_commit, untracked_commit],
\t\t)
\t\t.map_err(|err| Error::backend("git stash commit", err))?;
\t\tupdate_stash_ref(
\t\t\t&repo,
\t\t\tstash_commit,""")

# ---------------------------------------------------------------- git/read.rs
p = f"{BASE}/crates/pi-vcs/src/git/read.rs"
edit(p,
"""\t\tlet date = author
\t\t\t.time()
\t\t\t.map_err(|err| Error::backend("git show", err))?
\t\t\t.format(gix::date::time::format::ISO8601_STRICT)
\t\t\t.map_err(|err| Error::backend("git show", err))?;""",
"""\t\tlet date = author
\t\t\t.time()
\t\t\t.map_err(|err| Error::backend("git show", err))?
\t\t\t.format(gix::date::time::format::ISO8601_STRICT);""")

# ---------------------------------------------------------------- git/diff.rs
p = f"{BASE}/crates/pi-vcs/src/git/diff.rs"
edit(p,
"""\t\t\tauthor_time.format_or_unix(gix::date::time::format::DEFAULT)""",
"""\t\t\tauthor_time.format(gix::date::time::format::DEFAULT)""")
edit(p,
"""\t\t\t\tout.push(index_change(repo, change.into_owned())?);
\t\t\t\tOk(std::ops::ControlFlow::Continue(()))""",
"""\t\t\t\tout.push(index_change(repo, change.into_owned())?);
\t\t\t\tOk(gix::diff::index::Action::Continue)""")

print("ALL FIX-1b EDITS APPLIED")
