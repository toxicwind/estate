#!/usr/bin/env python3
"""Transfer herd.d/kimi-auto.yaml to awrawr-pc repo (base64, no backticks)."""
import base64
import subprocess

SRC = "/home/hatch/workspace/kimi-auto-build/herd.d/kimi-auto.yaml"
DST = "/home/toxic/kimi-auto/herd.d/kimi-auto.yaml"

with open(SRC, "rb") as fh:
    b64 = base64.b64encode(fh.read()).decode("ascii")

remote = (
    "printf '%s' '" + b64 + "' | base64 -d > " + DST
    + " && wc -c " + DST
    + " && rmdir /home/toxic/kimi-auto/systemd 2>/dev/null; ls -la /home/toxic/kimi-auto/"
)

r = subprocess.run(
    ["python3", "bin/exec.py", remote],
    capture_output=True, text=True, timeout=180,
    cwd="/home/hatch/workspace/skills/awrawr-mcp",
)
print("STDOUT:", (r.stdout or "")[-600:])
print("STDERR:", (r.stderr or "")[-400:])
print("RC:", r.returncode)
