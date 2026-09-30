#!/usr/bin/env python3
P = "/home/toxic/sovereign/src/coyote/coyote-loop.py"
src = open(P).read()
old = '    model: str = "kimi-auto"'
new = '    model: str = field(default_factory=lambda: os.getenv("COYOTE_MODEL", "gpt-oss"))'
assert old in src, "coyote model anchor missing"
src = src.replace(old, new)
# Document the router-ownership rule at the declaration site.
old2 = "    base_url: str = \"http://localhost:8080\""
new2 = ("    # Model selection is owned by router/service config (COYOTE_MODEL env,\n"
        "    # set in stack/services/coyote.sh). Tooling never hardcodes model IDs.\n"
        "    base_url: str = \"http://localhost:8080\"")
assert old2 in src, "base_url anchor missing"
src = src.replace(old2, new2)
open(P, "w").write(src)
print("coyote-loop.py model default now env-driven")

P2 = "/home/toxic/sovereign/agents/coyote/agent.toml"
s2 = open(P2).read()
old3 = "- The AST Matrix (llama-swap :25100) with 14 providers (kimi primary, 7 free-tier fallbacks)"
new3 = ("- The herd router (llama-swap :25100). Routing doctrine: RANKING > FREE-ON-PROVIDER > PAY. "
        "Kimi routes are never defaults -- they exist only for maximal free-Kimi routing.")
assert old3 in s2, "agent.toml anchor missing"
open(P2, "w").write(s2.replace(old3, new3))
print("agents/coyote/agent.toml doc fixed")
