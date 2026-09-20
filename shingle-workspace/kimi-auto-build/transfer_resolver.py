#!/usr/bin/env python3
"""Transfer resolver.py to awrawr-pc via base64 (no backticks in bridge cmd)."""
import base64
import subprocess

SRC = "/home/hatch/workspace/kimi-auto-build/resolver.py"
DST = "/home/toxic/kimi-auto/resolver.py"

with open(SRC, "rb") as fh:
    b64 = base64.b64encode(fh.read()).decode("ascii")

# base64 alphabet: no shell-special chars, safe inside single quotes.
remote = (
    "printf '%s' '" + b64 + "' | base64 -d > " + DST
    + " && chmod +x " + DST
    + " && wc -c " + DST
)

r = subprocess.run(
    ["python3", "bin/exec.py", remote],
    capture_output=True, text=True, timeout=180,
    cwd="/home/hatch/workspace/skills/awrawr-mcp",
)
print("STDOUT:", (r.stdout or "")[-600:])
print("STDERR:", (r.stderr or "")[-400:])
print("RC:", r.returncode)
