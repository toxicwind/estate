#!/usr/bin/env python3
"""Add nemotron-3-ultra-550b-a55b:free (verified by 14:29 probe) to the peer."""
P = "/home/toxic/sovereign/config/herd.yaml"
src = open(P).read()

OLD = """    # Ordered score desc, latency asc. The :free suffix is an unreliable
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

NEW = """    # Ordered score desc, latency asc. The :free suffix is an unreliable
    # narrator -- every ID here was verified LIVE, never trusted from /models.
    # Union of two 446-model abstract probes (14:25 + 14:29 MDT); availability
    # rotates, so the union is kept and the keypool fails over across keys.
    models:
      - nex-agi/nex-n2.5-mini:free
      - poolside/laguna-s-2.1:free
      - cohere/north-mini-code:free
      - nex-agi/nex-n2.5-pro:free
      - inclusionai/ling-3.0-flash-sante:free
      - nvidia/nemotron-3-ultra-550b-a55b:free
      - nvidia/nemotron-3-super-120b-a12b:free
      - nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free
      - nvidia/nemotron-3.5-lightning:free
      - google/gemma-4-31b-it:free
"""

assert src.count(OLD) == 1, "match count %d" % src.count(OLD)
open(P, "w").write(src.replace(OLD, NEW))
print("peer updated with union ranking")
