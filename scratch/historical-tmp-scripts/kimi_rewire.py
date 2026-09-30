#!/usr/bin/env python3
"""Rewire kimi-code-setup default route: herd/qwen-flash -> sovereign/free (:25104).
Proven by router-proof 2026-09-21: 56.7% exact / 63.3% code vs 16.7% / 0% pinned.
Idempotent, asserts each anchor exactly once, never touches api_key lines."""
import sys

P = "/home/toxic/sovereign/bin/kimi-code-setup"
src = open(P).read()

def rep(old, new):
    global src
    n = src.count(old)
    assert n == 1, f"anchor found {n}x (expected 1): {old[:70]!r}"
    src = src.replace(old, new)

# 1. Add SOVEREIGN_API next to HERD_API
rep('HERD_API="http://127.0.0.1:25100/v1"\n',
    'HERD_API="http://127.0.0.1:25100/v1"\n'
    'SOVEREIGN_API="http://127.0.0.1:25104/v1"  # proven route: router-proof 2026-09-21\n')

# 2. Header comment: what the script does
rep("""#   1. Ensures ~/.kimi-code/config.toml exists with the herd provider
#      (local router :25100, no key needed) and Moonshot direct provider
#      (key read at RUNTIME from ~/.secrets \u2014 never written to the repo).
#   2. Sets the default model to the verified working route.
#   3. Runs `kimi doctor` to validate the config.
#   4. Probes the default model end-to-end through herd (:25100).""",
"""#   1. Ensures ~/.kimi-code/config.toml exists with the sovereign router
#      (:25104, proven default \u2014 router-proof 2026-09-21), the herd provider
#      (local router :25100, no key needed) and Moonshot direct provider
#      (key read at RUNTIME from ~/.secrets \u2014 never written to the repo).
#   2. Sets the default model to the proven route (sovereign/free).
#   3. Runs `kimi doctor` to validate the config.
#   4. Probes the default model end-to-end through the sovereign router (:25104).""")

# 3. Config heredoc: providers comment
rep("# Providers: herd router (local, key-free) + Moonshot direct (serves on top-up)",
    "# Providers: sovereign router (proven default) + herd router (local, key-free) + Moonshot direct (serves on top-up)")

# 4. Config heredoc: default model
rep('default_model = "herd/qwen-flash"',
    'default_model = "sovereign/free"')

# 5. Config heredoc: sovereign provider block before [providers.kimi]
rep("\n[providers.kimi]",
    '\n[providers.sovereign]\ntype = "openai"\nbase_url = "$SOVEREIGN_API"\napi_key = "none"\n\n[providers.kimi]')

# 6. Config heredoc: sovereign/free model entry before herd/qwen-flash
rep('[models."herd/qwen-flash"]',
    '[models."sovereign/free"]\nprovider = "sovereign"\nmodel = "sovereign/free"\n'
    'max_context_size = 131072\ncapabilities = ["tool_use"]\n'
    'display_name = "Sovereign Router (proven: router-proof 2026-09-21)"\n\n[models."herd/qwen-flash"]')

# 7. Live probe -> sovereign router
rep("""log "probing default model herd/qwen-flash via herd :25100 ..."
RESP=$(curl -s --max-time 120 "$HERD_API/chat/completions" \\
  -H "Content-Type: application/json" \\
  -d '{"model":"beellama/qwen-flash-128k","messages":[{"role":"user","content":"Reply with exactly: KIMI_HERD_OK and nothing else. No thinking, just output the string."}],"max_tokens":300}')
if echo "$RESP" | grep -q "KIMI_HERD_OK"; then
  log "LIVE OK: default route returned KIMI_HERD_OK"
else
  log "LIVE FAIL: default route did not return KIMI_HERD_OK\"""",
"""log "probing default model sovereign/free via sovereign router :25104 ..."
RESP=$(curl -s --max-time 120 "$SOVEREIGN_API/chat/completions" \\
  -H "Content-Type: application/json" \\
  -d '{"model":"sovereign/free","messages":[{"role":"user","content":"Reply with exactly: SOVEREIGN_ROUTER_OK and nothing else. No thinking, just output the string."}],"max_tokens":300}')
if echo "$RESP" | grep -q "SOVEREIGN_ROUTER_OK"; then
  log "LIVE OK: default route returned SOVEREIGN_ROUTER_OK"
else
  log "LIVE FAIL: default route did not return SOVEREIGN_ROUTER_OK\"""")

open(P, "w").write(src)
print("edits applied OK")
