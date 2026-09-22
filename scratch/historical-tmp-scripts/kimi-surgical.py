import shutil
WT = '/tmp/kimi-push-wt'

# 1. sidecar (new file, with BrokenPipe fix) from the branch worktree
shutil.copy('/home/toxic/sovereign/bin/nim-kimi-sidecar.py', WT + '/bin/nim-kimi-sidecar.py')
print("sidecar copied")

# 2. ports.env
p = WT + '/config/ports.env'
s = open(p).read()
assert 'NIM_KIMI_SIDECAR_PORT' not in s
open(p, 'a').write('NIM_KIMI_SIDECAR_PORT=25163  # daemon-local; [daemons.nim-kimi-sidecar] env; consumed by bin/nim-kimi-sidecar.py\n')
print("ports.env updated")

# 3a. herd.yaml: kimi-k3-nim alias after kimi-code
p = WT + '/config/herd.yaml'
s = open(p).read()
anchor = "  beellama/exaone-4-0-1-2b-iq4xs:\n"
assert s.count(anchor) == 1, s.count(anchor)
alias = """  # kimi-k3-nim: genuine Kimi K3 via NVIDIA NIM (2026-09-21).
  # Fixed-target alias to nim-kimi/moonshotai/kimi-k3; identity enforced by
  # the sidecar (response model must be moonshotai/kimi-k3). Single target,
  # no standby: failures surface loud and verbatim. NEVER repointed at
  # another model to hide a provider failure. Cold-aware: first request
  # after idle takes ~120-220s (serverless hot-load); SHIM_CONNECT_TIMEOUT
  # covers the header wait.
  kimi-k3-nim:
    cmd: python3 /home/toxic/sovereign/config/herd.d/alias-shim.py --port ${PORT} --target nim-kimi/moonshotai/kimi-k3 --name kimi-k3-nim
    env:
      - SHIM_CONNECT_TIMEOUT=240
    description: "Kimi K3 via NVIDIA NIM (genuine moonshotai/kimi-k3, cold-aware). Fails loudly; no fallback."
    metadata:
      alias_of: nim-kimi/moonshotai/kimi-k3
      role: kimi-nim
"""
open(p, 'w').write(s.replace(anchor, alias + anchor))
print("herd.yaml alias added")

# 3b. herd.yaml: nim-kimi peer replaces the DELETED comment
s = open(p).read()
old = """  # nim-kimi peer DELETED 2026-09-20 (herd-deployer). Debate verdict:
  # NIM is DELETED, not demoted \u2014 24h 429 soft-locks poison fail-fast
  # routing, so NIM never returns as primary. Kimi K3 serves via the
  # OpenRouter key-pool (openrouter-pool peer). K3 card contract
  # preserved in config/model_constraints.yaml.
"""
assert s.count(old) == 1, "deleted-comment anchor: %d" % s.count(old)
peer = """  # --- nim-kimi: NVIDIA NIM Kimi-K3 via cold-aware sidecar (2026-09-21) ---
  # CORRECTION 2026-09-21 (Chris directive -- overrides the 2026-09-20
  # "NIM is DELETED" debate verdict): that verdict was built on a false
  # premise -- front-door 404/410s from WRONG model IDs (e.g.
  # moonshotai/kimi-k2-instruct, EOL'd 2026-05-12). Live-verified 2026-09-21:
  # moonshotai/kimi-k3 returns genuine K3 (identity-checked -- "I'm Kimi,
  # an AI assistant developed by Moonshot AI", Chinese reasoning trace)
  # via integrate.api.nvidia.com with the K3 contract (top_p stripped,
  # ~120-220s cold-load tolerance). Direct NVCF-plane invocation is NOT
  # available to this key (203 listed functions are NVIDIA-internal dynamo
  # benchmark/shadow rigs; the public serving deployment is not exposed
  # as an invocable function) -- the front door IS the NVCF plane's public
  # face. The sidecar on 127.0.0.1:25163 bakes the contract in: warmup on
  # start, 300s upstream timeout, top_p strip, identity enforcement,
  # 404/429 classification, no-retry on client disconnect. No silent
  # fallback to another model, ever.
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
open(p, 'w').write(s.replace(old, peer))
print("herd.yaml peer added")

# 4. pitchfork.toml: nim-kimi standby in kimi-auto-shim run line
p = WT + '/pitchfork.toml'
s = open(p).read()
old_run = "--standby hf-free/moonshotai/Kimi-K3 --advance-on"
assert s.count(old_run) == 1
s = s.replace(old_run, "--standby hf-free/moonshotai/Kimi-K3 --standby nim-kimi/moonshotai/kimi-k3 --advance-on")
# add the daemon section before [daemons.squawk-relay-sink]
anchor = "[daemons.squawk-relay-sink]\n"
assert s.count(anchor) == 1
daemon = """[daemons.nim-kimi-sidecar]
health_http = { url = "http://127.0.0.1:25163/health", interval = "30s", timeout = "5s", retries = 3 }
port = 25163
# Cold-aware NVIDIA NIM proxy for moonshotai/kimi-k3 (2026-09-21).
# Bakes the K3 contract in: warmup on start, 300s upstream timeout
# (serverless cold load ~120-220s is normal), top_p strip, identity
# enforcement, 404/429 classification. Fails loud; never substitutes.
run = "exec python3 /home/toxic/sovereign/bin/nim-kimi-sidecar.py"
dir = "/home/toxic/sovereign"
mise = false
retry = true
boot_start = true
ready_http = "http://127.0.0.1:25163/health"

"""
open(p, 'w').write(s.replace(anchor, daemon + anchor))
print("pitchfork.toml updated")
print("ALL SURGICAL EDITS DONE")
