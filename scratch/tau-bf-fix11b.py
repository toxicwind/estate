#!/usr/bin/env python3
"""Fix the misplaced parse_commit_date helper."""
import sys

BASE = "/home/toxic/tau-bf-20260914/tau/engine"
p = f"{BASE}/crates/pi-vcs/src/git/mutate.rs"

with open(p) as f:
    lines = f.readlines()

# The helper is lines 21-61 (1-indexed), i.e., indices 20-60
# Verify it starts with the doc comment and ends with }
assert lines[20].strip().startswith("/// Parse a commit author date string."), lines[20]
assert lines[60].strip() == "}", lines[60]

helper = lines[20:61]  # includes the trailing blank lines? Let's check
# lines[61] and [62] are blank, then line 63 is "\terror::{Error, Result},"
# We want to remove lines 20-60 (the helper) and the extra blank lines

# Remove helper (indices 20-60 inclusive)
del lines[20:61]

# Now lines[20] should be blank, lines[21] blank, lines[22] is "\terror::{Error, Result},"
# Remove the two blank lines that were after the helper
# Actually, let's just ensure clean structure

# Find the end of the use crate::{ block (the "};" line)
# After deletion, the use block should be contiguous
with open(p, "w") as f:
    f.writelines(lines)

print("Removed misplaced helper")

# Now re-insert it after the use block closes
with open(p) as f:
    c = f.read()

# Find the end of use crate::{...};
# The block ends with "};\n\nconst INDEX_WRITE"
old = "};\n\nconst INDEX_WRITE:"
new = "};\n" + "".join(helper) + "\nconst INDEX_WRITE:"

if c.count(old) != 1:
    print(f"FAIL: anchor found {c.count(old)}x")
    sys.exit(1)

c = c.replace(old, new)
with open(p, "w") as f:
    f.write(c)

print("OK [helper repositioned]")
