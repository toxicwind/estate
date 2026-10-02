p = '/home/toxic/mesh-bruteforce-20260914/tau/engine/crates/pi-vcs/src/jj/ops.rs'
s = open(p).read()

old = '''async fn render_git_diff(
\trepo: &dyn Repo,
\tbefore_tree: &MergedTree,
\tafter_tree: &MergedTree,
\tchanges: Vec<TreeChange>,
) -> Result<String> {'''
new = '''async fn render_git_diff(repo: &dyn Repo, changes: Vec<TreeChange>) -> Result<String> {'''
assert s.count(old) == 1, 'render_git_diff sig'
s = s.replace(old, new)

old = '\t\t\t\trender_git_diff(repo.as_ref(), &before, &after, changes).await\n'
new = '\t\t\t\trender_git_diff(repo.as_ref(), changes).await\n'
assert s.count(old) == 1, 'render_git_diff call'
s = s.replace(old, new)

open(p, 'w').write(s)
print('render_git_diff cleaned')
