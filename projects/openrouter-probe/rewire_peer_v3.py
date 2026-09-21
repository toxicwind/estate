#!/usr/bin/env python3
"""Rewire herd.yaml openrouter-free peer: comment block + models list -> v3 ordering.
Replaces lines 796..848 (1-based, inclusive) of /home/toxic/sovereign/config/herd.yaml.
Idempotent guard: refuses to run if the v3 marker is already present.
"""
import sys

PATH = "/home/toxic/sovereign/config/herd.yaml"
START, END = 796, 848  # 1-based inclusive

NEW_BLOCK = '''\
  # --- openrouter-free: probed-working OpenRouter :free models (added 2026-09-20) ---
  # Only models that returned real completions in the 2026-09-20 probes are listed.
  openrouter-free:
    proxy: http://127.0.0.1:25109/openrouter-free
    # apiKey intentionally OMITTED (2026-09-20, herd-deployer): auth is
    # injected per-call by the key-pool sidecar from its health-checked
    # OPENROUTER_* key rotation. Do NOT re-add a hardcoded key -- a
    # 401/402/429 is a routing signal, not a config rewrite.
    # ORDERING DOCTRINE (v3, 2026-09-20 ~14:55 MDT) --
    #   primary:   v3 abstract-probe reliability: 3 full passes x 446 /models
    #              IDs, prompt "Output exactly: ABSTRACT-7X3Q. No other text.",
    #              exact-match rate desc, p50 latency asc
    #              (projects/openrouter-probe/RANKING.md,
    #              reliability-20260920-144532.json). Explicitly SPECULATIVE:
    #              measures instruction-following on a trivial task, not quality.
    #   secondary: census LLM-judge quality 0-10 (var/or-free-ranking.md) as
    #              corroboration where it exists.
    #   The :free suffix is an unreliable narrator -- every ID here was verified
    #   LIVE, never trusted from /models. Availability rotates; the keypool
    #   fails over across keys and respects down_until/cooldown, so throttled
    #   models are safe as fallback tiers.
    models:
      # TIER 1 -- v3 3/3 exact, p50 ascending
      - cohere/north-mini-code:free  # v3 3/3 exact, p50 557ms -- fastest AND most reliable
      - nex-agi/nex-n2.5-pro:free  # v3 3/3 exact, p50 583ms
      - nex-agi/nex-n2.5-mini:free  # v3 3/3 exact, p50 609ms (census 7/10: fast but sloppy on prose)
      - inclusionai/ling-3.0-flash-sante:free  # v3 3/3 exact, p50 941ms
      - nvidia/nemotron-3-super-120b-a12b:free  # v3 3/3 exact, p50 1349ms
      - nvidia/nemotron-3-ultra-550b-a55b:free  # v3 3/3 exact, p50 6088ms; WILD variance (min 1352/max 75324) -- capacity-constrained
      # TIER 2 -- partial (2/3 exact): usable with failover; keypool cooldown absorbs misses
      - nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free  # v3 2/3 exact, 1x 200-empty
      - poolside/laguna-s-2.1:free  # v3 2/3 exact, 1x http-529
      # TIER 3 -- marginal: auto-router, exact 1/3, throttled 1/3
      - openrouter/free  # v3 1/3 exact (p50 600ms when it answers), 1x 429, 1x contains-only
      # TIER 4 (throttled-elite) -- 429 on ALL v3 passes; fallback only.
      # Keypool respects down_until/cooldown and auto-recovers, so these engage
      # only when cooldowns clear. Re-probe before promoting.
      - google/gemma-4-31b-it:free  # v3: 429 x3
      - google/gemma-4-26b-a4b-it:free  # v3: 429 x3
      - qwen/qwen3.8-27b:free  # v3: 429 x3
      - z-ai/glm-5.2:free  # v3: 429 x3
      # EXCLUDED (v3-observed -- re-probe before re-adding):
      # - inclusionai/ling-3.0-flash-fin:free, ling-3.0-flash-vl:free:
      #   200-EMPTY x3 (census ranked them #2/#4; v3 says they don't follow the
      #   instruction). Demoted from tier 1.
      # - dots-studio/dots-3-note-preview:free: 200-empty x3.
      # - poolside/laguna-xs-2.1:free: 200-empty x2, 429 x1.
      # - liquid/lfm-2.5-2.6b:free: responds without error but never emitted the
      #   token in 3 trials -- fails instruction-following, not availability.
      # - nvidia/nemotron-3.5-lightning:free: 0/3 exact, 3/3 contains-only
      #   (emits thinking). Unusable for exact-output tasks.
      # - nvidia/nemotron-3.5-content-safety:free: refuses by design (safety
      #   classifier, not a general LLM).
'''

def main():
    lines = open(PATH).read().split("\n")
    cur = "\n".join(lines[START - 1:END])
    if "ORDERING DOCTRINE (v3" in cur:
        print("already v3 -- no-op")
        return 0
    assert lines[START - 1].strip().startswith("# --- openrouter-free:"), lines[START - 1]
    assert lines[END - 1].strip() == "#   sibling empty bodies. Ungradeable.", lines[END - 1]
    assert lines[END].strip() == "timeouts:", lines[END]
    new_lines = lines[:START - 1] + NEW_BLOCK.rstrip("\n").split("\n") + lines[END:]
    open(PATH, "w").write("\n".join(new_lines))
    print("rewired lines %d..%d" % (START, END))

if __name__ == "__main__":
    sys.exit(main())
