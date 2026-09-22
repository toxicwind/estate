#!/usr/bin/env python3
old = '[daemons.axiom]\nport = 25103\nrun = "exec ./stack/services/openfang.sh"'
new = (
    "# OpenFang public front -- mesh-front proxy on :25103 -> :25196 kernel.\n"
    '# (Renamed from "axiom" 2026-09-21: the old service spawned a DUPLICATE kernel\n'
    "# on :25203 sharing the kernel's SQLite DB. Now proxy-only; the kernel is\n"
    "# daemons.openfang on :25196. See src/services/openfang.ts.)\n"
    '[daemons.openfang-front]\nport = 25103\nrun = "exec ./stack/services/openfang.sh"'
)
p = "/home/toxic/sovereign/pitchfork.toml"
s = open(p).read()
assert s.count(old) == 1, "axiom section not found exactly once"
open(p, "w").write(s.replace(old, new))
print("pitchfork.toml: renamed axiom -> openfang-front")
