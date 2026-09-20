p = '/home/toxic/mesh-bruteforce-20260914/tau/engine/crates/pi-vcs/src/jj/ops.rs'
s = open(p).read()

old = '''async fn render_numstat(
\trepo: &dyn Repo,
\tbefore_tree: &MergedTree,
\tafter_tree: &MergedTree,
\tchanges: Vec<TreeChange>,
) -> Result<Vec<NumstatEntry>> {'''
new = '''async fn render_numstat(repo: &dyn Repo, changes: Vec<TreeChange>) -> Result<Vec<NumstatEntry>> {'''
assert s.count(old) == 1, 'render_numstat sig'
s = s.replace(old, new)

old = '\t\t\tmaterialize_diff_parts(repo, before_tree, after_tree, &change, &options).await?;'
new = '\t\t\tmaterialize_diff_parts(repo, &change, &options).await?;'
assert s.count(old) == 1, 'render_numstat call'
s = s.replace(old, new)

open(p, 'w').write(s)

# find remaining render_numstat call sites
import re
for m in re.finditer(r'render_numstat\(repo\.as_ref\(\), [^)]+\)', s):
    print('CALL:', m.group(0))
