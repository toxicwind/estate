#!/usr/bin/env python3
"""One-shot config patches for the nim-kimi wiring (runs on yote)."""

def patch(path, anchor, block, marker):
    s = open(path).read()
    if marker in s:
        print("%s: already patched, skipping" % path)
        return
    assert anchor in s, "anchor missing in %s" % path
    s = s.replace(anchor, block + anchor, 1)
    open(path, "w").write(s)
    print("%s: patched" % path)

# 1. pitchfork.toml: nim-kimi-sidecar daemon
pt_block = (
    "# --- nim-kimi-sidecar 2026-09-21: cold-aware NVIDIA NIM proxy for moonshotai/kimi-k3.\n"
    "# Listens 127.0.0.1:25163; proxies integrate.api.nvidia.com with the K3\n"
    "# contract built in (top_p strip, 300s upstream timeout, warmup on start,\n"
    "# identity enforcement, 404/429 classification). Event-driven only: no\n"
    "# periodic re-warm (hosted NIM exposes no keep-warm to trial keys).\n"
    "[daemons.nim-kimi-sidecar]\n"
    'health_http = { url = "http://127.0.0.1:25163/health", interval = "30s", timeout = "5s", retries = 3 }\n'
    "port = 25163\n"
    'run = "exec python3 /home/toxic/sovereign/bin/nim-kimi-sidecar.py"\n'
    'dir = "/home/toxic/sovereign"\n'
    "mise = false\n"
    "retry = true\n"
    "boot_start = true\n"
    'ready_http = "http://127.0.0.1:25163/health"\n'
    'auto = ["start"]\n'
    "\n"
)
patch("pitchfork.toml", "[daemons.node-exporter]", pt_block, "[daemons.nim-kimi-sidecar]")

# 2. herd.yaml: nim-kimi peer (replaces the stale DELETED verdict)
old_note = """  # nim-kimi peer DELETED 2026-09-20 (herd-deployer). Debate verdict:
  # NIM is DELETED, not demoted \u2014 24h 429 soft-locks poison fail-fast
  # routing, so NIM never returns as primary. Kimi K3 serves via the
  # OpenRouter key-pool (openrouter-pool peer). K3 card contract
  # preserved in config/model_constraints.yaml.
"""
new_peer = """  # --- nim-kimi: NVIDIA NIM Kimi-K3 via cold-aware sidecar (2026-09-21) ---
  # CORRECTION 2026-09-21: the 2026-09-20 "NIM is DELETED" verdict was built
  # on a false premise (front-door 404/410s from WRONG model IDs like
  # moonshotai/kimi-k2-instruct, which EOL'd 2026-05-12). Live-verified
  # 2026-09-21: moonshotai/kimi-k3 returns genuine K3 (identity-checked)
  # via integrate.api.nvidia.com with the K3 contract (top_p omitted,
  # ~120s cold-load tolerance). Direct NVCF-plane invocation is NOT
  # available to this key (203 functions listed are NVIDIA-internal
  # dynamo benchmark/shadow rigs; POST /v2/nvcf/queues/{id} 404s) -- the
  # front door IS the NVCF plane's public face. The sidecar on
  # 127.0.0.1:25163 bakes the contract in: warmup on start, 300s upstream
  # timeout, top_p strip, identity enforcement, 404/429 classification.
  # No silent fallback to another model, ever.
  nim-kimi:
    proxy: http://127.0.0.1:25163
    models:
      - moonshotai/kimi-k3
    timeouts:
      connect: 30
      keepalive: 30
      responseHeader: 300
      tlsHandshake: 10
      idleConn: 90
"""
s = open("config/herd.yaml").read()
if "proxy: http://127.0.0.1:25163" in s:
    print("config/herd.yaml: peer already present, skipping")
else:
    assert old_note in s, "stale nim-kimi note not found"
    s = s.replace(old_note, new_peer, 1)
    open("config/herd.yaml", "w").write(s)
    print("config/herd.yaml: nim-kimi peer restored")

# 3. herd.yaml: repair kimi-k3-nim as fixed-target alias -> genuine K3
s = open("config/herd.yaml").read()
if "alias_of: nim-kimi/moonshotai/kimi-k3" in s:
    print("config/herd.yaml: kimi-k3-nim already repaired, skipping")
else:
    kimi_anchor = "  kimi-code:\n"
    assert kimi_anchor in s, "kimi-code anchor missing"
    idx = s.index(kimi_anchor)
    rest = s[idx:]
    lines = rest.split("\n")
    end = 1
    for i in range(1, len(lines)):
        ln = lines[i]
        if ln and not ln.startswith(" ") and not ln.startswith("#") and ln.strip():
            break
        end = i + 1
    insert_at = idx + sum(len(l) + 1 for l in lines[:end])
    kimi_alias = (
        "  # kimi-k3-nim REPAIRED 2026-09-21: fixed-target alias to nim-kimi /\n"
        "  # moonshotai/kimi-k3 (genuine K3 via NVIDIA NIM, identity-enforced by\n"
        "  # the sidecar). Single target, no standby: failures surface loud and\n"
        "  # verbatim. NEVER repointed at another model to hide a provider failure.\n"
        "  kimi-k3-nim:\n"
        "    cmd: python3 /home/toxic/sovereign/config/herd.d/alias-shim.py --port ${PORT} --target nim-kimi/moonshotai/kimi-k3 --name kimi-k3-nim\n"
        '    description: "Kimi K3 via NVIDIA NIM (genuine moonshotai/kimi-k3, cold-aware). Fails loudly; no fallback."\n'
        "    metadata:\n"
        "      alias_of: nim-kimi/moonshotai/kimi-k3\n"
        "      role: kimi-nim\n"
    )
    s = s[:insert_at] + kimi_alias + s[insert_at:]
    open("config/herd.yaml", "w").write(s)
    print("config/herd.yaml: kimi-k3-nim alias repaired")
print("ALL PATCHES DONE")
