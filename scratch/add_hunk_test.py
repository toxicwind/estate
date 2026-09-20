p = '/home/toxic/mesh-bruteforce-20260914/tau/engine/crates/pi-vcs/src/git/diff.rs'
s = open(p).read()
anchor = '''\t#[cfg(unix)]
\t#[test]
\tfn no_index_text_binary_executable_and_symlink_match_git() {'''
assert s.count(anchor) == 1
test = '''\t#[test]
\tfn insertion_and_deletion_hunk_ranges_match_git() {
\t\tlet dir = fixture();
\t\tlet no_context = DiffOptions { context: Some(0), ..DiffOptions::default() };
\t\t// file.txt starts as seven lines: one..seven.
\t\t// Pure insertion after line 3: git renders the zero-length old range
\t\t// with the position of the line before the change, `@@ -3,0 +4,2 @@`.
\t\tfs::write(
\t\t\tdir.path().join("file.txt"),
\t\t\t"one\\ntwo\\nthree\\nINSERTED-A\\nINSERTED-B\\nfour\\nfive\\nsix\\nseven\\n",
\t\t)
\t\t.expect("insert lines");
\t\tlet repo = GitRepo::discover(dir.path()).expect("discover").expect("repository");
\t\tlet diff = repo.diff_text(&no_context).expect("diff");
\t\tassert!(diff.contains("@@ -3,0 +4,2 @@"), "insertion header:\\n{diff}");
\t\tassert_eq!(diff, git(dir.path(), &["diff", "-U0"]));
\t\tgit(dir.path(), &["add", "."]);
\t\tgit(dir.path(), &["commit", "-qm", "insert"]);

\t\t// Pure deletion of lines 7-8 ("five","six"): `@@ -7,2 +6,0 @@`.
\t\tfs::write(
\t\t\tdir.path().join("file.txt"),
\t\t\t"one\\ntwo\\nthree\\nINSERTED-A\\nINSERTED-B\\nfour\\nseven\\n",
\t\t)
\t\t.expect("delete lines");
\t\tlet diff = repo.diff_text(&no_context).expect("diff");
\t\tassert!(diff.contains("@@ -7,2 +6,0 @@"), "deletion header:\\n{diff}");
\t\tassert_eq!(diff, git(dir.path(), &["diff", "-U0"]));
\t\t// And with default context the merged hunks still match byte for byte.
\t\tassert_eq!(
\t\t\trepo.diff_text(&DiffOptions::default()).expect("diff"),
\t\t\tgit(dir.path(), &["diff"])
\t\t);
\t}

'''
s = s.replace(anchor, test + anchor)
open(p, 'w').write(s)
print('hunk range test added')
