#!/usr/bin/env python3
"""ember-kimi-route: herd.yaml edits for maximal free-Kimi routing."""
import sys

P = "/home/toxic/sovereign/config/herd.yaml"
src = open(P).read()
orig = src

# --- Edit 1: Kimi short aliases -> maximal free-Kimi chains ---
old_aliases = '''  # --- Kimi short aliases (added 2026-09-20) ---
  # Fixed-target forwarders via config/herd.d/alias-shim.py. No fallback,
  # no substitution: each alias IS its target. Retargeted 2026-09-20
  # (moonshot-parked-audit) from openrouter-pool/* back to moonshot/* --
  # the direct peer is restored; openrouter-pool Kimi is 402
  # "Insufficient credits" until the account is topped up.
  # 2026-09-21 modelmap: live-probed -- the `peer/<id>` prefixed form is
  # what /v1/models advertises and it routes directly to the peer
  # (moonshot/kimi-k2.6 -> 429, moonshot/kimi-k2.7-code -> 429). Bare IDs
  # hit the dedup'd global map and are unreliable (kimi-k2.7-code -> 404).
  kimi:
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
      alias_of: moonshot/kimi-k2.7-code
'''

SHIM = "python3 /home/toxic/sovereign/config/herd.d/alias-shim.py --port ${PORT}"
CHAIN = ("--advance-on 5xx,conn,429,402,404")
K3 = "openrouter-free/moonshotai/kimi-k3:free"
K26 = "openrouter-free/moonshotai/kimi-k2.6:free"
K25 = "openrouter-free/moonshotai/kimi-k2.5:free"
K27 = "openrouter-free/moonshotai/kimi-k2.7-code:free"
HFK = "hf-free/moonshotai/Kimi-K3"

new_aliases = '''  # --- Kimi short aliases (added 2026-09-20) ---
  # Fixed-target forwarders via config/herd.d/alias-shim.py (v3: ordered
  # --standby chains + --advance-on). CHRIS DOCTRINE 2026-09-21: Kimi routes
  # are NEVER defaults; their sole purpose is routing Kimi FREE models
  # maximally. Each alias declares the full free-Kimi chain in priority
  # order; the shim walks it one-shot per candidate, advancing on
  # 5xx/conn/429/402/404 (free-tier rotation, throttle, and depleted-credit
  # states are expected transients, never misconfiguration). HTTP 401 never
  # advances: bad auth surfaces verbatim. Paid Kimi (moonshot direct, 429
  # billing-suspended; openrouter-pool, 402 insufficient-credits) is
  # deliberately NOT in these chains -- free only.
  kimi:
    cmd: %(shim)s --target %(k3)s --standby %(k26)s --standby %(k25)s --standby %(k27)s --standby %(hfk)s %(chain)s --name kimi
    description: "Kimi (maximal free-Kimi chain: openrouter-free :free IDs -> hf-free)"
    metadata:
      alias_of: %(k3)s
      chain: free-kimi-maximal
  kimi-k2:
    cmd: %(shim)s --target %(k3)s --standby %(k26)s --standby %(k25)s --standby %(k27)s --standby %(hfk)s %(chain)s --name kimi-k2
    description: "Kimi K2 (maximal free-Kimi chain: openrouter-free :free IDs -> hf-free)"
    metadata:
      alias_of: %(k3)s
      chain: free-kimi-maximal
  kimi-code:
    cmd: %(shim)s --target %(k27)s --standby %(k3)s --standby %(k26)s --standby %(k25)s --standby %(hfk)s %(chain)s --name kimi-code
    description: "Kimi code specialist (maximal free-Kimi chain, code-first -> hf-free)"
    metadata:
      alias_of: %(k27)s
      chain: free-kimi-maximal
''' % {"shim": SHIM, "k3": K3, "k26": K26, "k25": K25, "k27": K27,
       "hfk": HFK, "chain": CHAIN}

assert old_aliases in src, "alias block anchor missing"
src = src.replace(old_aliases, new_aliases)

# --- Edit 2: openrouter-free peer -- add Kimi free IDs as fallback tier ---
old_tier4_tail = "      - z-ai/glm-5.2:free  # v3: 429 x3\n"
new_tier5 = old_tier4_tail + """      # TIER 5 -- Kimi free variants (maximal free-Kimi routing, 2026-09-21,
      # ember-kimi-route): OpenRouter rotates free Kimi availability; all 404
      # "unavailable for free" as of 2026-09-21. Listed as fallback tier --
      # keypool cooldown + shim chain-advance (429/402/404) absorb misses, so
      # they serve automatically the moment OpenRouter re-enables them.
      # Re-probe before promoting.
      - moonshotai/kimi-k3:free
      - moonshotai/kimi-k2.6:free
      - moonshotai/kimi-k2.5:free
      - moonshotai/kimi-k2.7-code:free
"""
assert old_tier4_tail in src, "tier4 tail anchor missing"
src = src.replace(old_tier4_tail, new_tier5)

# --- Edit 3: re-enable hf-free peer (Kimi-K3 only, 402 fallback tier) ---
old_hf = '''  # DISABLED 2026-09-20 (provider-surgeon): HF_TOKEN and all 3 backup HF keys are
  # dead (HTTP 401); no working HuggingFace key exists. Remove entirely if a new
  # HF key never materializes. Original block below:
  #   # --- hf-free: free Kimi via HuggingFace Inference Providers (additive 2026-09-14) ---
  #   # Matrix-verified: moonshotai/Kimi-K3 -> HTTP 200 + real completion on our
  #   # HF_TOKEN (no billing attached; HF free-served set). Other Kimi IDs 402.
  #   # The kimi-auto resolver auto-discovers this ID from herd /v1/models.
  #   hf-free:
  #     proxy: https://router.huggingface.co
  #     apiKey: ${env.HF_TOKEN}
  #     models:
  #       - moonshotai/Kimi-K3
  #     options:
  #       validateModel: true
  #
  #
  #
  #
  #
  #
  #
'''
new_hf = '''  # --- hf-free: free Kimi via HuggingFace Inference Providers (additive 2026-09-14) ---
  # RE-ENABLED 2026-09-21 (ember-kimi-route): HF_TOKEN is valid again
  # (fine-grained token, auth verified live 2026-09-21 -- no more 401).
  # Monthly included credits are DEPLETED (HTTP 402 as of 2026-09-21), so
  # this peer is a fallback tier in the maximal free-Kimi chain: the shim
  # advances past 402 to the next candidate, and it serves automatically
  # when credits reset. moonshotai/Kimi-K3 is the only Kimi ID verified to
  # exist on HF Inference Providers (lowercase moonshotai/kimi-k3 -> 400
  # "does not exist"). Other Kimi IDs 402.
  hf-free:
    proxy: https://router.huggingface.co
    apiKey: ${env.HF_TOKEN}
    models:
      - moonshotai/Kimi-K3
    timeouts:
      connect: 30
      keepalive: 30
      responseHeader: 120
      tlsHandshake: 10
      idleConn: 90
'''
assert old_hf in src, "hf-free anchor missing"
src = src.replace(old_hf, new_hf)

assert src != orig
open(P, "w").write(src)
print("herd.yaml updated OK")
