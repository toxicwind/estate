#!/usr/bin/env python3
"""forge: canonical commit prep - manifest herd entry + pollinations-free peer.

Run with WT=/tmp/manifest-wt env. Content-anchored, no line numbers.
"""
import os

WT = os.environ["WT"]

# ---------- 1. deploy/manifest.yaml: declare the new herd binary ----------
p = WT + "/deploy/manifest.yaml"
L = open(p).readlines()
i = next(i for i, l in enumerate(L) if l.rstrip("\n") == "  herd:")
assert 'sha256: "9305f95663dbf7a8c0e07e6c46a5549cbc173075fc2bf77cbd7e98ee3b81b519"' in L[i + 2], L[i + 2]
L[i + 2] = '    sha256: "98978a2612445ff59b07abb51797d453368bb494f9c4fb28ed57c6092d2281f6"\n'
assert "llama-swap.20260920-223545" in L[i + 3], L[i + 3]
L[i + 3] = "    immutable_copy: /home/toxic/projects/sovereign-projects/sovereign-swap/build/llama-swap.20260921-124036\n"
assert "commit: 61e497ee88f36b176b7e74bace697f142ef99aa2" in L[i + 5], L[i + 5]
L[i + 5] = "    commit: 7fc25280816fa7f98764ac46d1435d55ac9dc3c3\n"
assert 'built_at: "2026-09-21T04:34:33Z"' in L[i + 7], L[i + 7]
L[i + 7] = '    built_at: "2026-09-21T12:40:37Z"\n'
open(p, "w").writelines(L)
print("OK manifest.yaml herd entry")

# ---------- 2. config/herd.yaml: re-enable pollinations-free peer ----------
p = WT + "/config/herd.yaml"
L = open(p).readlines()
start = next(i for i, l in enumerate(L) if l.rstrip("\n") == "  #pollinations-free:")
i = start
while i < len(L) and L[i].startswith("  #"):
    if L[i].strip() == "#":
        break
    if L[i][3:].lstrip().startswith("---"):
        break  # section divider of the next peer block; leave commented
    L[i] = "  " + L[i][3:]
    i += 1
for j in range(start, i):
    if "router injects pollinations-free-workaround" in L[j]:
        L[j] = "    # apiKey omitted -> anonymous: no auth headers sent (sovereign-swap rebuild 2026-09-21, commit 7fc2528)\n"
hdr = next(k for k in range(start - 14, start) if "DISABLED 2026-09-20 ~02:35" in L[k])
end = next(k for k in range(hdr, start) if "stays parked" in L[k])
L[hdr:end + 1] = [
    "  # RE-ENABLED 2026-09-21 (forge): herd rebuilt from sovereign-swap branch\n",
    "  # herd-fqn-fix commit 7fc25280816f -- the Sep-18 dummy-Bearer workaround is gone:\n",
    "  # empty apiKey now sends NO auth headers (peer.go strips client auth too).\n",
    "  # Direct no-auth probe 2026-09-21 returned HTTP 200 on openai; through-herd\n",
    "  # verification after restart below. Re-park if 401s return.\n",
]
open(p, "w").writelines(L)

import yaml
d = yaml.safe_load(open(p))
assert "pollinations-free" in d["peers"], "peer not active"
print("OK herd.yaml peer re-enabled, YAML valid")
