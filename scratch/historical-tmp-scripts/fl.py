#!/usr/bin/env python3
"""forge: update live-tree manifest herd entry to the fixed binary."""
p = "/home/toxic/sovereign/deploy/manifest.yaml"
L = open(p).readlines()
i = next(i for i, l in enumerate(L) if l.rstrip("\n") == "  herd:")
L[i + 2] = '    sha256: "98978a2612445ff59b07abb51797d453368bb494f9c4fb28ed57c6092d2281f6"\n'
L[i + 3] = "    immutable_copy: /home/toxic/projects/sovereign-projects/sovereign-swap/build/llama-swap.20260921-124036\n"
L[i + 5] = "    commit: 7fc25280816fa7f98764ac46d1435d55ac9dc3c3\n"
L[i + 7] = '    built_at: "2026-09-21T12:40:37Z"\n'
open(p, "w").writelines(L)
print("live manifest updated")
