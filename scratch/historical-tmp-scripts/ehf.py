#!/usr/bin/env python3
P = "/tmp/kimi-route-wt/config/herd.yaml"
src = open(P).read()
old = """  # 
  # DISABLED 2026-09-20 (provider-surgeon): HF_TOKEN and all 3 backup HF keys are
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
  #"""
new = """  # --- hf-free: free Kimi via HuggingFace Inference Providers ---
  # RE-ENABLED 2026-09-21 (ember-kimi-route): the 2026-09-20 "HF_TOKEN dead"
  # verdict used the v1 whoami endpoint (401s even for valid tokens -- VOID).
  # A new fine-grained HF_TOKEN was installed 2026-09-20 and verified live
  # 2026-09-21 via the Inference Providers API: moonshotai/Kimi-K3 ->
  # HTTP 402 (monthly included credits depleted -- valid auth, no quota).
  # Peer stays configured; serves automatically on credit refresh. It is
  # the terminal candidate of the maximal free-Kimi chains (kimi, kimi-k2,
  # kimi-code, kimi-auto).
  hf-free:
    baseUrl: https://router.huggingface.co/v1
    keyEnv: HF_TOKEN
    models:
      - moonshotai/Kimi-K3
"""
assert old in src, "hf-free disabled block anchor missing"
open(P, "w").write(src.replace(old, new))
print("hf-free peer re-enabled")
