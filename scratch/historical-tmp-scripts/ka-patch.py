#!/usr/bin/env python3
"""Add genuine NVIDIA NIM K3 as the last standby in the kimi-auto free chain."""
p = "/home/toxic/kimi-auto/herd.d/kimi-auto.yaml"
s = open(p).read()
old = "--standby hf-free/moonshotai/Kimi-K3 --advance-on"
new = "--standby hf-free/moonshotai/Kimi-K3 --standby nim-kimi/moonshotai/kimi-k3 --advance-on"
assert "nim-kimi/moonshotai/kimi-k3" not in s, "already present"
assert old in s, "anchor missing"
s = s.replace(old, new, 1)
old_desc = 'description: "kimi-auto: maximal free-Kimi chain (openrouter-free :free IDs -> hf-free Kimi-K3)"'
new_desc = 'description: "kimi-auto: maximal free-Kimi chain (openrouter-free :free IDs -> hf-free Kimi-K3 -> nim-kimi genuine K3 via NVIDIA NIM, cold-aware ~120s)"'
assert old_desc in s, "desc anchor missing"
s = s.replace(old_desc, new_desc, 1)
open(p, "w").write(s)
print("kimi-auto.yaml: nim-kimi K3 appended as last standby")
