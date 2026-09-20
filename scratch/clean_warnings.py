p = '/home/toxic/mesh-bruteforce-20260914/tau/engine/crates/pi-vcs/src/jj/ops.rs'
s = open(p).read()

# 1. Drop the now-unused TreeValue import.
old = '\tbackend::{CommitId, TreeValue},\n'
new = '\tbackend::CommitId,\n'
assert s.count(old) == 1, 'treevalue import'
s = s.replace(old, new)

# 2. materialize_diff_parts: drop unused before_tree/after_tree params.
old = '''async fn materialize_diff_parts(
\trepo: &dyn Repo,
\tbefore_tree: &MergedTree,
\tafter_tree: &MergedTree,
\tchange: &TreeChange,
\toptions: &ConflictMaterializeOptions,
) -> Result<(GitDiffPart, GitDiffPart)> {'''
new = '''async fn materialize_diff_parts(
\trepo: &dyn Repo,
\tchange: &TreeChange,
\toptions: &ConflictMaterializeOptions,
) -> Result<(GitDiffPart, GitDiffPart)> {'''
assert s.count(old) == 1, 'materialize sig'
s = s.replace(old, new)

old = '\t\tlet (before_part, after_part) =\n\t\t\tmaterialize_diff_parts(repo, before_tree, after_tree, &change, &materialize_options)\n\t\t\t\t.await?;'
new = '\t\tlet (before_part, after_part) =\n\t\t\tmaterialize_diff_parts(repo, &change, &materialize_options).await?;'
assert s.count(old) == 1, 'materialize call site'
s = s.replace(old, new)

open(p, 'w').write(s)
print('warnings cleaned')
