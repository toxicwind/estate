#!/usr/bin/env python3
p = "/home/toxic/sovereign/pitchfork.toml"
s = open(p).read()
old = '"search-ui", "axiom", "rust-web"'
new = '"search-ui", "openfang-front", "rust-web"'
assert s.count(old) == 2, f"expected 2 group lists, found {s.count(old)}"
open(p, "w").write(s.replace(old, new))
print("groups.mesh + groups.all: axiom -> openfang-front")
