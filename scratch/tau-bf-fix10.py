#!/usr/bin/env python3
"""Fix batch 10: git-compatible hunk header format."""
import sys

BASE = "/home/toxic/tau-bf-20260914/tau/engine"
p = f"{BASE}/crates/pi-vcs/src/git/diff.rs"

with open(p) as f:
    c = f.read()

old = "\t\t// `header` arrives as \"@@ -a,b +c,d @@\\n\"; splice function context\n\t\t// in before the trailing newline, the way git renders it.\n\t\tlet header = header.strip_suffix('\\n').unwrap_or(header);\n\t\tself.out.push_str(header);"

new = "\t\t// Reconstruct the header with git's convention: gix emits\n\t\t// \"@@ -1,0 +1,1 @@\" for empty/new hunks, but git renders\n\t\t// \"@@ -0,0 +1 @@\". When len==0 start is 0; when len==1 the\n\t\t// \",1\" is omitted.\n\t\tfn fmt_range(start: u32, len: u32) -> String {\n\t\t\tlet start = if len == 0 { 0 } else { start };\n\t\t\tif len == 1 {\n\t\t\t\tformat!(\"{start}\")\n\t\t\t} else {\n\t\t\t\tformat!(\"{start},{len}\")\n\t\t\t}\n\t\t}\n\t\tlet header = format!(\n\t\t\t\"@@ -{} +{} @@\",\n\t\t\tfmt_range(before_hunk_start, before_hunk_len),\n\t\t\tfmt_range(after_hunk_start, after_hunk_len)\n\t\t);\n\t\tself.out.push_str(&header);"

if c.count(old) != 1:
    print(f"FAIL: found {c.count(old)}x, expected 1x")
    sys.exit(1)

c = c.replace(old, new)
c = c.replace("\t\t_before_hunk_len: u32,", "\t\tbefore_hunk_len: u32,")
c = c.replace("\t\t_after_hunk_len: u32,", "\t\tafter_hunk_len: u32,")
c = c.replace("\t\theader: &str,", "\t\t_header: &str,")

with open(p, "w") as f:
    f.write(c)
print("OK [hunk header git format]")
print("FIX-10 DONE")
