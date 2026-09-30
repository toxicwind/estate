#!/usr/bin/env python3
"""Apply ember-kimi-route pitchfork/coyote/agent.toml changes to origin/main."""
import re

# --- pitchfork.toml ---
P = "/tmp/kimi-route-wt/pitchfork.toml"
src = open(P).read()
old = '''# Router-configured alias forwarder: same routing as the herd
# kimi-auto entry (--config-dir fragment). --target/--standby MUST match
# /home/toxic/kimi-auto/herd.d/kimi-auto.yaml. Selection lives in router
# config; this shim never selects models.
# 2026-09-21 modelmap: was --target ministral-14b-latest (paid Mistral) --
# a kimi-named alias serving a non-Kimi model. Doctrine (AGENTS.md):
# "kimi-auto is Kimi-only. Honest 503 when no Kimi route is healthy;
# never a silent fallback." Retargeted to the moonshot peer's Kimi IDs
# in peer/<id> form (live-probed: prefixed routes directly, bare IDs
# are unreliable -- kimi-k2.7-code bare -> 404).
run = "exec python3 /home/toxic/sovereign/config/herd.d/alias-shim.py --port ${KIMI_AUTO_SHIM_PORT} --target moonshot/kimi-k2.6 --standby moonshot/kimi-k2.7-code --name kimi-auto"'''
new = '''# Router-configured alias forwarder: same routing as the herd
# kimi-auto entry (--config-dir fragment). --target/--standby/--advance-on
# MUST match /home/toxic/kimi-auto/herd.d/kimi-auto.yaml. Selection lives
# in router config; this shim never selects models.
# 2026-09-21 (ember-kimi-route): maximal free-Kimi chain per Chris doctrine
# -- Kimi routes are never defaults; they route Kimi FREE models maximally.
# Chain: openrouter-free kimi :free IDs -> hf-free Kimi-K3; advance on
# 5xx/conn/429/402/404; 401 never advances. Paid Kimi excluded (free only).
run = "exec python3 /home/toxic/sovereign/config/herd.d/alias-shim.py --port ${KIMI_AUTO_SHIM_PORT} --target openrouter-free/moonshotai/kimi-k3:free --standby openrouter-free/moonshotai/kimi-k2.6:free --standby openrouter-free/moonshotai/kimi-k2.5:free --standby openrouter-free/moonshotai/kimi-k2.7-code:free --standby hf-free/moonshotai/Kimi-K3 --advance-on 5xx,conn,429,402,404 --name kimi-auto"'''
assert old in src, "pitchfork anchor missing"
open(P, "w").write(src.replace(old, new))
print("pitchfork.toml updated")

# --- coyote-loop.py ---
P = "/tmp/kimi-route-wt/src/coyote/coyote-loop.py"
src = open(P).read()
old = '    model: str = "kimi-auto"'
new = '    model: str = field(default_factory=lambda: os.getenv("COYOTE_MODEL", "gpt-oss"))'
assert old in src, "coyote model anchor missing"
src = src.replace(old, new)
old2 = '    base_url: str = "http://localhost:8080"'
new2 = ('    # Model selection is owned by router/service config (COYOTE_MODEL env,\n'
        '    # set in stack/services/coyote.sh). Tooling never hardcodes model IDs.\n'
        '    base_url: str = "http://localhost:8080"')
assert old2 in src, "coyote base_url anchor missing"
src = src.replace(old2, new2)
open(P, "w").write(src)
print("coyote-loop.py updated")

# --- agents/coyote/agent.toml ---
P = "/tmp/kimi-route-wt/agents/coyote/agent.toml"
src = open(P).read()
old = "- The AST Matrix (llama-swap :25100) with 14 providers (kimi primary, 7 free-tier fallbacks)"
new = ("- The herd router (llama-swap :25100). Routing doctrine: RANKING > FREE-ON-PROVIDER > PAY. "
       "Kimi routes are never defaults -- they exist only for maximal free-Kimi routing.")
assert old in src, "agent.toml anchor missing"
open(P, "w").write(src.replace(old, new))
print("agents/coyote/agent.toml updated")
