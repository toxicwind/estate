p = '/home/toxic/mesh-bruteforce-20260914/tau/engine/crates/pi-vcs/src/git/diff.rs'
s = open(p).read()

# 1. Struct: add new_data.
old = '''struct GitHunks<'a> {
\tout:      &'a mut String,
\told_data: &'a [u8],
\tadded:    u32,
\tremoved:  u32,
}'''
new = '''struct GitHunks<'a> {
\tout:      &'a mut String,
\told_data: &'a [u8],
\tnew_data: &'a [u8],
\tadded:    u32,
\tremoved:  u32,
}

/// Number of lines in `data`, counting a trailing unterminated chunk as a line.
fn line_count(data: &[u8]) -> u32 {
\tlet mut count = data.iter().filter(|byte| **byte == b'\\n').count() as u32;
\tif !data.is_empty() && !data.ends_with(b"\\n") {
\t\tcount += 1;
\t}
\tcount
}'''
assert s.count(old) == 1, 'struct anchor'
s = s.replace(old, new)

# 2. Construction site: pass new_data.
old = '''\t\t\tlet old_data = prepared.old.data.as_slice().unwrap_or_default();
\t\t\tlet mut hunks = String::new();
\t\t\tlet unified = gix::diff::blob::UnifiedDiff::new(
\t\t\t\t&input,
\t\t\t\tGitHunks { out: &mut hunks, old_data, added: 0, removed: 0 },'''
new = '''\t\t\tlet old_data = prepared.old.data.as_slice().unwrap_or_default();
\t\t\t\tlet new_data = prepared.new.data.as_slice().unwrap_or_default();
\t\t\tlet mut hunks = String::new();
\t\t\tlet unified = gix::diff::blob::UnifiedDiff::new(
\t\t\t\t&input,
\t\t\t\tGitHunks { out: &mut hunks, old_data, new_data, added: 0, removed: 0 },'''
assert s.count(old) == 1, 'construction anchor'
s = s.replace(old, new)

# 3. consume_hunk body: correlate each printed line with its side's data.
old = '''\t\tself.out.push('\\n');
\t\t// Every hunk line is prefixed with ' ', '+', or '-' by UnifiedDiff,
\t\t// so the first byte is always the kind marker. Tokens keep their
\t\t// terminator; a piece without one is the final line of a side that
\t\t// does not end in a newline, which git marks explicitly.
\t\tfor piece in hunk.split_inclusive(|byte| *byte == b'\\n') {
\t\t\tmatch piece.first() {
\t\t\t\tSome(b'+') => self.added += 1,
\t\t\t\tSome(b'-') => self.removed += 1,
\t\t\t\t_ => {},
\t\t\t}
\t\t\tself.out.push_str(&String::from_utf8_lossy(piece));
\t\t\tif !piece.ends_with(b"\\n") {
\t\t\t\tself.out.push('\\n');
\t\t\t\tself.out.push_str("\\\\ No newline at end of file\\n");
\t\t\t}
\t\t}
\t\tOk(())'''
new = '''\t\tself.out.push('\\n');
\t\t// gix normalizes hunk lines with a trailing '\\n', hiding whether the
\t\t// source line had a terminator. Correlate each printed line with its
\t\t// side's original data: git marks a final line without a terminator
\t\t// with `\\ No newline at end of file`.
\t\tlet old_total = line_count(self.old_data);
\t\tlet new_total = line_count(self.new_data);
\t\tlet old_missing_nl = !self.old_data.is_empty() && !self.old_data.ends_with(b"\\n");
\t\tlet new_missing_nl = !self.new_data.is_empty() && !self.new_data.ends_with(b"\\n");
\t\tlet mut old_line = before_hunk_start;
\t\tlet mut new_line = after_hunk_start;
\t\t// Every hunk line is prefixed with ' ', '+', or '-' by UnifiedDiff,
\t\t// so the first byte is always the kind marker.
\t\tfor piece in hunk.split_inclusive(|byte| *byte == b'\\n') {
\t\t\t// A context line is byte-identical on both sides (xdiff compares
\t\t\t// lines with their terminators), so checking the old side covers
\t\t\t// both.
\t\t\tlet missing_newline = match piece.first() {
\t\t\t\tSome(b'+') => {
\t\t\t\t\tself.added += 1;
\t\t\t\t\tlet line = new_line;
\t\t\t\t\tnew_line += 1;
\t\t\t\t\tline == new_total && new_missing_nl
\t\t\t\t}
\t\t\t\tSome(b'-') => {
\t\t\t\t\tself.removed += 1;
\t\t\t\t\tlet line = old_line;
\t\t\t\t\told_line += 1;
\t\t\t\t\tline == old_total && old_missing_nl
\t\t\t\t}
\t\t\t\t_ => {
\t\t\t\t\tlet line = old_line;
\t\t\t\t\told_line += 1;
\t\t\t\t\tnew_line += 1;
\t\t\t\t\tline == old_total && old_missing_nl
\t\t\t\t}
\t\t\t};
\t\t\tself.out.push_str(&String::from_utf8_lossy(piece));
\t\t\tif missing_newline {
\t\t\t\tif !piece.ends_with(b"\\n") {
\t\t\t\t\tself.out.push('\\n');
\t\t\t\t}
\t\t\t\tself.out.push_str("\\\\ No newline at end of file\\n");
\t\t\t}
\t\t}
\t\tOk(())'''
assert s.count(old) == 1, 'consume_hunk body anchor'
s = s.replace(old, new)

open(p, 'w').write(s)
print('no-newline correlation fix applied')
