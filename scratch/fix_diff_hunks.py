import sys

p = '/home/toxic/mesh-bruteforce-20260914/tau/engine/crates/pi-vcs/src/git/diff.rs'
s = open(p).read()

old = (
    '\t\t// Reconstruct the header with git\'s convention: gix emits\n'
    '\t\t// "@@ -1,0 +1,1 @@" for empty/new hunks, but git renders\n'
    '\t\t// "@@ -0,0 +1 @@". When len==0 start is 0; when len==1 the\n'
    '\t\t// ",1" is omitted.\n'
    '\t\tfn fmt_range(start: u32, len: u32) -> String {\n'
    '\t\t\tlet start = if len == 0 { 0 } else { start };\n'
    '\t\t\tif len == 1 {\n'
    '\t\t\t\tformat!("{start}")\n'
    '\t\t\t} else {\n'
    '\t\t\t\tformat!("{start},{len}")\n'
    '\t\t\t}\n'
    '\t\t}\n'
)
new = (
    '\t\t// Reconstruct the header with git\'s convention: gix reports the\n'
    '\t\t// 1-based position one past a zero-length range, but git renders\n'
    '\t\t// the position of the line before the change: "@@ -5,0 +6 @@"\n'
    '\t\t// for an insertion after old line 5, "@@ -0,0 +1 @@" for a new\n'
    '\t\t// file. When len==1 the ",1" is omitted.\n'
    '\t\tfn fmt_range(start: u32, len: u32) -> String {\n'
    '\t\t\tlet start = if len == 0 { start.saturating_sub(1) } else { start };\n'
    '\t\t\tif len == 1 {\n'
    '\t\t\t\tformat!("{start}")\n'
    '\t\t\t} else {\n'
    '\t\t\t\tformat!("{start},{len}")\n'
    '\t\t\t}\n'
    '\t\t}\n'
)
assert old in s, 'fmt_range block not found'
s = s.replace(old, new)

old2 = (
    '\t\tself.out.push(\'\\n\');\n'
    '\t\t// Every hunk line is prefixed with \' \', \'+\', or \'-\' by UnifiedDiff,\n'
    '\t\t// so the first byte is always the kind marker.\n'
    '\t\tfor line in hunk.split(|byte| *byte == b\'\\n\') {\n'
    '\t\t\tmatch line.first() {\n'
    '\t\t\t\tSome(b\'+\') => self.added += 1,\n'
    '\t\t\t\tSome(b\'-\') => self.removed += 1,\n'
    '\t\t\t\t_ => {},\n'
    '\t\t\t}\n'
    '\t\t}\n'
    '\t\tself.out.push_str(&String::from_utf8_lossy(hunk));\n'
    '\t\tOk(())\n'
)
new2 = (
    '\t\tself.out.push(\'\\n\');\n'
    '\t\t// Every hunk line is prefixed with \' \', \'+\', or \'-\' by UnifiedDiff,\n'
    '\t\t// so the first byte is always the kind marker. Tokens keep their\n'
    '\t\t// terminator; a piece without one is the final line of a side that\n'
    '\t\t// does not end in a newline, which git marks explicitly.\n'
    '\t\tfor piece in hunk.split_inclusive(|byte| *byte == b\'\\n\') {\n'
    '\t\t\tmatch piece.first() {\n'
    '\t\t\t\tSome(b\'+\') => self.added += 1,\n'
    '\t\t\t\tSome(b\'-\') => self.removed += 1,\n'
    '\t\t\t\t_ => {},\n'
    '\t\t\t}\n'
    '\t\t\tself.out.push_str(&String::from_utf8_lossy(piece));\n'
    '\t\t\tif !piece.ends_with(b"\\n") {\n'
    '\t\t\t\tself.out.push(\'\\n\');\n'
    '\t\t\t\tself.out.push_str("\\\\ No newline at end of file\\n");\n'
    '\t\t\t}\n'
    '\t\t}\n'
    '\t\tOk(())\n'
)
assert old2 in s, 'hunk body block not found'
s = s.replace(old2, new2)
open(p, 'w').write(s)
print('diff.rs fixes applied')
