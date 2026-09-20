#!/usr/bin/env python3
"""Resolve the three stash@{0} apply conflicts per maximal-merge policy."""
import re

ROOT = "/home/toxic/sovereign"

def resolve(path, chooser):
    full = f"{ROOT}/{path}"
    lines = open(full).read().split("\n")
    out, i, n_resolved = [], 0, 0
    while i < len(lines):
        if lines[i].startswith("<<<<<<< "):
            j = lines.index("=======", i)
            k = lines.index(">>>>>>> Stashed changes", j)
            upstream = lines[i+1:j]
            stashed = lines[j+1:k]
            out.extend(chooser(upstream, stashed, path))
            n_resolved += 1
            i = k + 1
        else:
            out.append(lines[i])
            i += 1
    open(full, "w").write("\n".join(out))
    print(f"{path}: resolved {n_resolved} conflict(s)")

def herd_sh(upstream, stashed, path):
    # modify-vs-delete: keep the MODIFIED version (stash@{0}'s refined block)
    return stashed

def herd_yaml(upstream, stashed, path):
    # modified-vs-deleted: keep the MODIFIED version (upstream's modelMap)
    return upstream

def pitchfork(upstream, stashed, path):
    # Upstream block is the live config (matches running process:
    # /home/toxic/squawk-ws/squawk_ws_server.py on :25147). Keep it whole,
    # preserve the stashed variant's data as a comment (no duplicate TOML keys).
    note = [
        "# NOTE (merged 2026-09-14, stash wip-kimi-audit): superseded squawk-ws",
        "# variant kept for reference — old path /home/toxic/squawk/relay/squawk_ws_server.py,",
        "# old dir /home/toxic/squawk, old ready_http http://127.0.0.1:25147/ping.",
        "# Live process runs the /home/toxic/squawk-ws/ path on :25147; this block reflects that.",
    ]
    return upstream + note

resolve("stack/services/herd.sh", herd_sh)
resolve("config/herd.yaml", herd_yaml)
resolve("pitchfork.toml", pitchfork)
