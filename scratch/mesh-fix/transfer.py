#!/usr/bin/env python3
"""Transfer local files to awrawr-pc worktree via the awrawr-mcp bridge (base64)."""
import base64
import subprocess
import sys

BRIDGE = "/home/hatch/workspace/skills/awrawr-mcp/bin/exec.py"

TRANSFERS = [
    ("/home/hatch/workspace/mesh-fix/registry.ts",
     "/home/toxic/mesh-bruteforce-20260914/src/services/registry.ts"),
    ("/home/hatch/workspace/mesh-fix/pitchfork.ts",
     "/home/toxic/mesh-bruteforce-20260914/src/generators/pitchfork.ts"),
    ("/home/hatch/workspace/mesh-fix/index.ts",
     "/home/toxic/mesh-bruteforce-20260914/src/services/index.ts"),
]

for src, dst in TRANSFERS:
    with open(src, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    # base64 alphabet has no shell-special chars; safe in single quotes.
    cmd = "echo '%s' | base64 -d > '%s' && wc -c '%s'" % (b64, dst, dst)
    r = subprocess.run(
        ["python3", BRIDGE, cmd, "/home/toxic"],
        capture_output=True, text=True, timeout=120,
    )
    tail = (r.stdout or "")[-200:]
    print(dst, "->", "OK" if r.returncode == 0 else "FAIL", tail.replace("\n", " "))
    if r.returncode != 0:
        print(r.stderr[-500:], file=sys.stderr)
        sys.exit(1)
print("all transfers done")
