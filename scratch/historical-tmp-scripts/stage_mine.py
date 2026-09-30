#!/usr/bin/env python3
# stage_mine.py — stage only Forge's hunks, leaving other agents' dirty hunks
# in the working tree. Then the caller commits the index.
import subprocess
import sys

REPO = "/home/toxic/sovereign"


def split_hunks(diff):
    header, hunks, cur = [], [], None
    for ln in diff.split("\n"):
        if ln.startswith("@@"):
            cur = [ln]
            hunks.append(cur)
        elif cur is None:
            header.append(ln)
        else:
            cur.append(ln)
    return header, hunks


def filter_file(path, drop_if):
    r = subprocess.run(["git", "diff", "--", path], capture_output=True,
                       text=True, cwd=REPO)
    diff = r.stdout
    if not diff.strip():
        print(path, ": no diff")
        return
    header, hunks = split_hunks(diff)
    kept = []
    for h in hunks:
        text = "\n".join(h)
        if any(d in text for d in drop_if):
            print(path, ": dropping hunk", h[0][:40])
        else:
            kept.append(h)
    if not kept:
        print(path, ": nothing to stage")
        return
    new_diff = "\n".join(header + [ln for h in kept for ln in h])
    p = subprocess.run(["git", "apply", "--cached", "-"], input=new_diff,
                       capture_output=True, text=True, cwd=REPO)
    if p.returncode != 0:
        print(path, "APPLY FAILED:", p.stderr[:500])
        sys.exit(1)
    print(path, ": staged", len(kept), "hunk(s)")


# pitchfork.toml: drop the nats hunks (another agent's), keep loopback + gate.
filter_file("pitchfork.toml", ["[daemons.nats]", "run-nats.sh", "run-tail.sh"])
# funnel-map.sh: drop the nats-ws MAP line (another agent's), keep the rest.
filter_file("projects/yote/ops/funnel-map.sh", ['+"/nats-ws'])

# Stage whole files that are entirely mine.
others = [
    "projects/mesh/browserless/browser-router.sh",
    "projects/mesh/browserless/keeper/README.md",
    "projects/mesh/browserless/keeper/pitchfork.fragment.toml",
    "projects/mesh/browserless/viewer/",
]
p = subprocess.run(["git", "add"] + others, capture_output=True, text=True,
                   cwd=REPO)
if p.returncode != 0:
    print("git add FAILED:", p.stderr[:500])
    sys.exit(1)
print("staged whole files:", others)

# Show what's staged.
p = subprocess.run(["git", "status", "--porcelain"], capture_output=True,
                   text=True, cwd=REPO)
print("--- staged ---")
for ln in p.stdout.split("\n"):
    if ln[:1] in ("M", "A") and ln[1:2] != " ":
        pass
    if ln.startswith(("M ", "A ", "MM", "AM")):
        print(ln)
