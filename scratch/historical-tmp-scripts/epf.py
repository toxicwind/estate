#!/usr/bin/env python3
P = "/home/toxic/sovereign/pitchfork.toml"
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
assert old in src, "anchor missing"
open(P, "w").write(src.replace(old, new))
print("pitchfork.toml kimi-auto-shim run line updated")
