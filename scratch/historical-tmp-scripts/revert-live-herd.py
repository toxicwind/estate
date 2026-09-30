import yaml
p = "/home/toxic/sovereign/config/herd.yaml"
s = open(p).read()
# REVERT 2026-09-21: bare peer model IDs do NOT reliably route.
# Live probe proved: moonshot/kimi-k2.6 -> 429 (routes), kimi-k2.6 -> 429,
# moonshot/kimi-k2.7-code -> 429 (routes), kimi-k2.7-code -> 404 (BROKEN).
# The prefixed peer/model form is what's advertised in /v1/models and routes
# directly to the peer. Bare IDs hit the dedup'd global map unreliably.
old_block = """  kimi:
    cmd: python3 /home/toxic/sovereign/config/herd.d/alias-shim.py --port ${PORT} --target kimi-k2.6
    description: "Kimi (alias -> kimi-k2.6)"
    metadata:
      alias_of: kimi-k2.6
  kimi-k2:
    cmd: python3 /home/toxic/sovereign/config/herd.d/alias-shim.py --port ${PORT} --target kimi-k2.6
    description: "Kimi K2 (alias -> kimi-k2.6)"
    metadata:
      alias_of: kimi-k2.6
  kimi-code:
    cmd: python3 /home/toxic/sovereign/config/herd.d/alias-shim.py --port ${PORT} --target kimi-k2.7-code
    description: "Kimi code specialist (alias -> kimi-k2.7-code)"
    metadata:
      alias_of: kimi-k2.7-code"""
new_block = """  kimi:
    cmd: python3 /home/toxic/sovereign/config/herd.d/alias-shim.py --port ${PORT} --target moonshot/kimi-k2.6
    description: "Kimi (alias -> moonshot/kimi-k2.6)"
    metadata:
      alias_of: moonshot/kimi-k2.6
  kimi-k2:
    cmd: python3 /home/toxic/sovereign/config/herd.d/alias-shim.py --port ${PORT} --target moonshot/kimi-k2.6
    description: "Kimi K2 (alias -> moonshot/kimi-k2.6)"
    metadata:
      alias_of: moonshot/kimi-k2.6
  kimi-code:
    cmd: python3 /home/toxic/sovereign/config/herd.d/alias-shim.py --port ${PORT} --target moonshot/kimi-k2.7-code
    description: "Kimi code specialist (alias -> moonshot/kimi-k2.7-code)"
    metadata:
      alias_of: moonshot/kimi-k2.7-code"""
assert old_block in s, "kimi block not found"
s = s.replace(old_block, new_block, 1)
# Fix the annotation comment I added.
s = s.replace(
  "  # 2026-09-21 modelmap: targets were `moonshot/<id>` -- peer.go does\n"
  "  # EXACT-match lookups, no `peer/` prefix stripping, so those 404'd.\n"
  "  # Targets are the bare upstream IDs the moonshot peer claims.",
  "  # 2026-09-21 modelmap: live-probed -- the `peer/<id>` prefixed form is\n"
  "  # what /v1/models advertises and it routes directly to the peer\n"
  "  # (moonshot/kimi-k2.6 -> 429, moonshot/kimi-k2.7-code -> 429). Bare IDs\n"
  "  # hit the dedup'd global map and are unreliable (kimi-k2.7-code -> 404).")
open(p, "w").write(s)
yaml.safe_load(open(p))
print("live herd.yaml: kimi targets reverted to moonshot/<id>, YAML valid")
