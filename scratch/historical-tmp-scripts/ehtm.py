#!/usr/bin/env python3
"""Apply ember-kimi-route herd.yaml changes to origin/main version."""
import re, sys

P = "/tmp/kimi-route-wt/config/herd.yaml"
src = open(P).read()

FREE_CHAIN = ("openrouter-free/moonshotai/kimi-k3:free",
              "openrouter-free/moonshotai/kimi-k2.6:free",
              "openrouter-free/moonshotai/kimi-k2.5:free",
              "openrouter-free/moonshotai/kimi-k2.7-code:free",
              "hf-free/moonshotai/Kimi-K3")
ADV = "--advance-on 5xx,conn,429,402,404"

def chain_cmd(primary_first=True):
    cands = list(FREE_CHAIN)
    target, standbys = cands[0], cands[1:]
    sb = " ".join("--standby %s" % s for s in standbys)
    return ("python3 /home/toxic/sovereign/config/herd.d/alias-shim.py "
            "--port ${PORT} --target %s %s %s --name %s")

# --- 1. kimi / kimi-k2 / kimi-code aliases -> free-Kimi chains ---
for alias in ("kimi", "kimi-k2", "kimi-code"):
    pat = re.compile(r"(?m)^  %s:\n    cmd: [^\n]+\n    description: \"[^\"]*\"\n    metadata:\n      alias_of: [^\n]+\n" % re.escape(alias))
    m = pat.search(src)
    assert m, "alias block not found: %s" % alias
    target, standbys = FREE_CHAIN[0], FREE_CHAIN[1:]
    sb = " ".join("--standby %s" % s for s in standbys)
    new = (
        "  # 2026-09-21 (ember-kimi-route): Kimi routes are NEVER defaults;\n"
        "  # their sole purpose is routing Kimi FREE models maximally.\n"
        "  # Ordered free-Kimi chain; shim advances on 5xx/conn/429/402/404;\n"
        "  # 401 never advances. Paid Kimi excluded (free only).\n"
        "  %s:\n"
        "    cmd: python3 /home/toxic/sovereign/config/herd.d/alias-shim.py "
        "--port ${PORT} --target %s %s %s --name %s\n"
        "    description: \"Kimi (alias -> maximal free-Kimi chain)\"\n"
        "    metadata:\n"
        "      alias_of: %s\n"
        "      chain: free-kimi-maximal\n"
        "      selection: router-config\n"
        % (alias, target, sb, ADV, alias, target)
    )
    src = src[:m.start()] + new + src[m.end():]
print("aliases rewritten")

# --- 2. openrouter-free peer: add kimi :free IDs ---
m = re.search(r"(?m)^(  openrouter-free:\n(?:.*\n)*?    models:\n)((?:      .*\n)+)", src)
assert m, "openrouter-free peer not found"
models_block = m.group(2)
for kid in ("moonshotai/kimi-k3:free", "moonshotai/kimi-k2.6:free",
            "moonshotai/kimi-k2.5:free", "moonshotai/kimi-k2.7-code:free"):
    if kid not in models_block:
        models_block += "      - %s  # free Kimi (ember-kimi-route 2026-09-21)\n" % kid
src = src[:m.start(2)] + models_block + src[m.end(2):]
print("openrouter-free kimi IDs added")

# --- 3. hf-free peer: ensure present with Kimi-K3 ---
if "hf-free:" not in src:
    anchor = "peers:\n"
    idx = src.find(anchor)
    assert idx > 0
    hffree = (
        "  # --- hf-free: free Kimi via HuggingFace Inference Providers ---\n"
        "  # 2026-09-21 (ember-kimi-route): maximal free-Kimi routing. Live-probed\n"
        "  # 2026-09-21: moonshotai/Kimi-K3 -> HTTP 402 (monthly included credits\n"
        "  # depleted). Peer stays configured; serves automatically on credit\n"
        "  # refresh. No API key needed beyond HF_TOKEN in .secrets.\n"
        "  hf-free:\n"
        "    baseUrl: https://router.huggingface.co/v1\n"
        "    keyEnv: HF_TOKEN\n"
        "    models:\n"
        "      - moonshotai/Kimi-K3\n"
    )
    src = src[:idx+len(anchor)] + hffree + src[idx+len(anchor):]
    print("hf-free peer added")
else:
    print("hf-free peer already present")

open(P, "w").write(src)
print("herd.yaml updated OK")
