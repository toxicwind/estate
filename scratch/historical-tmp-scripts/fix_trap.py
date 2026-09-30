#!/usr/bin/env python3
"""One-line fix: EXIT trap must preserve the script's exit code."""
import sys

path = "/home/toxic/super-ralph/scripts/reconcile-resume.sh"
with open(path) as f:
    s = f.read()

old = "trap 'rm -rf \"$TMPDIR\"' EXIT"
new = "trap 'rc=$?; rm -rf \"$TMPDIR\"; exit $rc' EXIT"
n = s.count(old)
if n != 1:
    print("ABORT: expected 1 occurrence, found %d" % n)
    sys.exit(1)
with open(path, "w") as f:
    f.write(s.replace(old, new))
print("patched OK")
