#!/usr/bin/env python3
"""Rewrite the openrouter-free peer model list from the abstract-probe ranking."""
import sys

P = "/home/toxic/sovereign/config/herd.yaml"
src = open(P).read()

OLD = """  openrouter-free:
    proxy: http://127.0.0.1:25109/openrouter
    # apiKey intentionally OMITTED (2026-09-20, herd-deployer): auth is
    # injected per-call by the key-pool sidecar from its health-checked
    # OPENROUTER_* key rotation. Do NOT re-add a hardcoded key — a
    # 401/402/429 is a routing signal, not a config rewrite.
    models:
      - google/gemma-4-31b-it:free
      - nvidia/nemotron-3.5-lightning:free
      - nvidia/nemotron-3-super-120b-a12b:free
      - nex-agi/nex-n2.5-pro:free
"""

NEW = """  openrouter-free:
    proxy: http://127.0.0.1:25109/openrouter
    # apiKey intentionally OMITTED (2026-09-20, herd-deployer): auth is
    # injected per-call by the key-pool sidecar from its health-checked
    # OPENROUTER_* key rotation. Do NOT re-add a hardcoded key -- a
    # 401/402/429 is a routing signal, not a config rewrite.
    # Model list = speculative ranking from abstract probe 2026-09-20
    # (openrouter-probe/probe_abstract.py; prompt "Output exactly:
    # ABSTRACT-7X3Q. No other text."; score 2 = exact, 1 = contains).
    # Ordered score desc, latency asc. The :free suffix is an unreliable
    # narrator -- every ID here was verified LIVE, never trusted from /models.
    models:
      - nex-agi/nex-n2.5-mini:free
      - poolside/laguna-s-2.1:free
      - cohere/north-mini-code:free
      - nex-agi/nex-n2.5-pro:free
      - nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free
      - nvidia/nemotron-3-super-120b-a12b:free
      - nvidia/nemotron-3.5-lightning:free
      - google/gemma-4-31b-it:free
"""

assert src.count(OLD) == 1, "expected exactly 1 match, got %d" % src.count(OLD)
open(P, "w").write(src.replace(OLD, NEW))
print("openrouter-free peer rewritten from abstract-probe ranking")
