p = '/home/toxic/mesh-bruteforce-20260914/tau/engine/crates/pi-vcs/src/jj/ops.rs'
s = open(p).read()

# 1. Imports: drop dead CopyId, add CopyRecords + futures StreamExt.
old = '\tbackend::{CommitId, CopyId, TreeValue},\n\tcommit::Commit,\n'
new = '\tbackend::{CommitId, TreeValue},\n\tcommit::Commit,\n'
assert s.count(old) == 1, 'import anchor'
s = s.replace(old, new)

old = '\tconflicts::{ConflictMarkerStyle, ConflictMaterializeOptions, materialize_tree_value},\n'
new = '\tconflicts::{ConflictMarkerStyle, ConflictMaterializeOptions, materialize_tree_value},\n\tcopies::CopyRecords,\n'
assert s.count(old) == 1, 'copies import anchor'
s = s.replace(old, new)

old = 'use std::{\n\tcollections::{BTreeMap, BTreeSet, BinaryHeap},\n\tfuture::Future,\n\tpath::PathBuf,\n\tpin::Pin,\n\tsync::Arc,\n};\n'
new = old + '\nuse futures::StreamExt as _;\n'
assert s.count(old) == 1, 'std import anchor'
s = s.replace(old, new)

# 2. working_copy_trees also returns the working-copy commit.
old = '''async fn working_copy_trees(
\tworkspace: &Workspace,
\trepo: &dyn Repo,
\tcontext: &'static str,
) -> Result<Option<(MergedTree, MergedTree)>> {
\tlet Some(wc_id) = repo.view().get_wc_commit_id(workspace.workspace_name()) else {
\t\treturn Ok(None);
\t};
\tlet commit = repo
\t\t.store()
\t\t.get_commit(wc_id)
\t\t.map_err(|err| Error::backend(context, err))?;
\tlet parent_tree = commit
\t\t.parent_tree(repo)
\t\t.map_err(|err| Error::backend(context, err))?;
\tlet tree = commit.tree().map_err(|err| Error::backend(context, err))?;
\tOk(Some((parent_tree, tree)))
}'''
new = '''async fn working_copy_trees(
\tworkspace: &Workspace,
\trepo: &dyn Repo,
\tcontext: &'static str,
) -> Result<Option<(MergedTree, MergedTree, Commit)>> {
\tlet Some(wc_id) = repo.view().get_wc_commit_id(workspace.workspace_name()) else {
\t\treturn Ok(None);
\t};
\tlet commit = repo
\t\t.store()
\t\t.get_commit(wc_id)
\t\t.map_err(|err| Error::backend(context, err))?;
\tlet parent_tree = commit
\t\t.parent_tree(repo)
\t\t.map_err(|err| Error::backend(context, err))?;
\tlet tree = commit.tree().map_err(|err| Error::backend(context, err))?;
\tOk(Some((parent_tree, tree, commit)))
}

/// Backend copy records between each parent of the working-copy commit and the
/// working-copy commit itself, mirroring `jj st`/`jj diff` rename detection.
/// The git backend derives these from content-similarity rewrite tracking;
/// copy ids are placeholders in this jj-lib version and carry no signal.
#[allow(
\tclippy::future_not_send,
\treason = "driven on a per-call current-thread runtime; `&dyn Repo` is !Send"
)]
async fn working_copy_copy_records(
\trepo: &dyn Repo,
\twc_commit: &Commit,
\tfiles: &[String],
\tcontext: &'static str,
) -> Result<CopyRecords> {
\tlet mut copy_records = CopyRecords::default();
\tfor parent_id in wc_commit.parent_ids() {
\t\tlet mut records = repo
\t\t\t.store()
\t\t\t.get_copy_records(None, parent_id, wc_commit.id())
\t\t\t.map_err(|err| Error::backend(context, err))?;
\t\twhile let Some(record) = records.next().await {
\t\t\tlet record = record.map_err(|err| Error::backend(context, err))?;
\t\t\t// Keep only records whose target is selected, so a rename can
\t\t\t// never hide a delete the caller asked about.
\t\t\tif path_selected(&record.target, &record.target, files) {
\t\t\t\tcopy_records
\t\t\t\t\t.add_records([Ok(record)])
\t\t\t\t\t.map_err(|err| Error::backend(context, err))?;
\t\t\t}
\t\t}
\t}
\tOk(copy_records)
}'''
assert s.count(old) == 1, 'working_copy_trees anchor'
s = s.replace(old, new)

# 3. collect_changes: take copy_records, use them for rename/copy.
old = '''fn collect_changes(
\tbefore_tree: &MergedTree,
\tafter_tree: &MergedTree,
\tfiles: &[String],
\tcontext: &'static str,
) -> Result<Vec<TreeChange>> {'''
new = '''fn collect_changes(
\tbefore_tree: &MergedTree,
\tafter_tree: &MergedTree,
\tcopy_records: &CopyRecords,
\tfiles: &[String],
\tcontext: &'static str,
) -> Result<Vec<TreeChange>> {'''
assert s.count(old) == 1, 'collect_changes sig anchor'
s = s.replace(old, new)

old = '''\t\tlet source = non_placeholder_copy_id(after_value).and_then(|copy_id| {
\t\t\tbefore.iter().find_map(|(source_path, source_value)| {
\t\t\t\t(non_placeholder_copy_id(source_value) == Some(copy_id)).then_some(source_path)
\t\t\t})
\t\t});
\t\tif let Some(source_path) = source {
\t\t\tlet operation = if removed.remove(source_path) {
\t\t\t\t"rename"
\t\t\t} else {
\t\t\t\t"copy"
\t\t\t};
\t\t\tif path_selected(source_path, path, files) {
\t\t\t\tchanges.push(TreeChange {
\t\t\t\t\tbefore_path:    source_path.clone(),
\t\t\t\t\tafter_path:     path.clone(),
\t\t\t\t\tbefore:         before[source_path].clone(),
\t\t\t\t\tafter:          after_value.clone(),
\t\t\t\t\tcopy_operation: Some(operation),
\t\t\t\t});
\t\t\t}
\t\t} else if path_selected(path, path, files) {'''
new = '''\t\t// Rename/copy detection from the backend's copy records, mirroring
\t\t// `jj st`: a target whose source was deleted is a rename, otherwise
\t\t// it is a copy.
\t\tlet source = copy_records
\t\t\t.for_target(path)
\t\t\t.map(|record| record.source.clone())
\t\t\t.filter(|source_path| before.contains_key(source_path));
\t\tif let Some(source_path) = source {
\t\t\tlet operation = if removed.remove(&source_path) {
\t\t\t\t"rename"
\t\t\t} else {
\t\t\t\t"copy"
\t\t\t};
\t\t\tif path_selected(&source_path, path, files) {
\t\t\t\tchanges.push(TreeChange {
\t\t\t\t\tbefore_path:    source_path.clone(),
\t\t\t\t\tafter_path:     path.clone(),
\t\t\t\t\tbefore:         before[&source_path].clone(),
\t\t\t\t\t\tafter:          after_value.clone(),
\t\t\t\t\tcopy_operation: Some(operation),
\t\t\t\t});
\t\t\t}
\t\t} else if path_selected(path, path, files) {'''
assert s.count(old) == 1, 'copy_id lookup anchor'
s = s.replace(old, new)

old = '''\tfor path in removed {
\t\tif path_selected(&path, &path, files) {'''
new = '''\tfor path in removed {
\t\t// The source side of a rename is covered by the rename entry above.
\t\tif copy_records.has_source(&path) {
\t\t\tcontinue;
\t\t}
\t\tif path_selected(&path, &path, files) {'''
assert s.count(old) == 1, 'removed loop anchor'
s = s.replace(old, new)

# 4. Remove the now-dead copy-id helper.
old = '''fn non_placeholder_copy_id(value: &MergedTreeValue) -> Option<&CopyId> {
\tmatch value.as_resolved()? {
\t\tSome(TreeValue::File { copy_id, .. }) if !copy_id.as_bytes().is_empty() => Some(copy_id),
\t\t_ => None,
\t}
}

'''
assert s.count(old) == 1, 'non_placeholder_copy_id anchor'
s = s.replace(old, '')

# 5. Call sites: destructure the commit, build copy records, pass them in.
old = '\t\t\t\tlet Some((before, after)) =\n'
new = '\t\t\t\tlet Some((before, after, wc_commit)) =\n'
assert s.count(old) == 5, 'destructure sites: %d' % s.count(old)
s = s.replace(old, new)

old = '\t\t\t\tlet changes = collect_changes(&before, &after, &[], "jj status")?;\n'
new = ('\t\t\t\tlet copy_records =\n'
       '\t\t\t\t\tworking_copy_copy_records(repo.as_ref(), &wc_commit, &[], "jj status").await?;\n'
       '\t\t\t\tlet changes = collect_changes(&before, &after, &copy_records, &[], "jj status")?;\n')
assert s.count(old) == 1, 'status_summary site'
s = s.replace(old, new)

old = '\t\t\t\tlet changes = collect_changes(&before, &after, &pathspecs, "jj status")?;\n'
new = ('\t\t\t\tlet copy_records =\n'
       '\t\t\t\t\tworking_copy_copy_records(repo.as_ref(), &wc_commit, &pathspecs, "jj status")\n'
       '\t\t\t\t\t\t.await?;\n'
       '\t\t\t\tlet changes =\n'
       '\t\t\t\t\tcollect_changes(&before, &after, &copy_records, &pathspecs, "jj status")?;\n')
assert s.count(old) == 1, 'status_porcelain site'
s = s.replace(old, new)

old = '\t\t\t\tlet changes = collect_changes(&before, &after, &files, "jj diff")?;\n\t\t\t\trender_git_diff(repo.as_ref(), &before, &after, changes).await\n'
new = ('\t\t\t\tlet copy_records =\n'
       '\t\t\t\t\tworking_copy_copy_records(repo.as_ref(), &wc_commit, &files, "jj diff").await?;\n'
       '\t\t\t\tlet changes = collect_changes(&before, &after, &copy_records, &files, "jj diff")?;\n'
       '\t\t\t\trender_git_diff(repo.as_ref(), &before, &after, changes).await\n')
assert s.count(old) == 1, 'diff_text site'
s = s.replace(old, new)

old = '\t\t\t\tOk(collect_changes(&before, &after, &files, "jj diff")?\n'
new = ('\t\t\t\tlet copy_records =\n'
       '\t\t\t\t\tworking_copy_copy_records(repo.as_ref(), &wc_commit, &files, "jj diff").await?;\n'
       '\t\t\t\tOk(collect_changes(&before, &after, &copy_records, &files, "jj diff")?\n')
assert s.count(old) == 1, 'changed_files site'
s = s.replace(old, new)

old = '\t\t\t\tlet changes = collect_changes(&before, &after, &files, "jj diff")?;\n\t\t\t\trender_numstat(repo.as_ref(), &before, &after, changes).await\n'
new = ('\t\t\t\tlet copy_records =\n'
       '\t\t\t\t\tworking_copy_copy_records(repo.as_ref(), &wc_commit, &files, "jj diff").await?;\n'
       '\t\t\t\tlet changes = collect_changes(&before, &after, &copy_records, &files, "jj diff")?;\n'
       '\t\t\t\trender_numstat(repo.as_ref(), &before, &after, changes).await\n')
assert s.count(old) == 1, 'numstat site'
s = s.replace(old, new)

open(p, 'w').write(s)
print('jj rename fix applied')

# 6. futures dependency for StreamExt.
p = '/home/toxic/mesh-bruteforce-20260914/tau/engine/crates/pi-vcs/Cargo.toml'
s = open(p).read()
old = 'gix-utils = { version = "0.3.6", default-features = false }\n'
new = old + 'futures.workspace = true\n'
assert s.count(old) == 1, 'cargo deps anchor'
s = s.replace(old, new)
open(p, 'w').write(s)
print('futures dep added')
