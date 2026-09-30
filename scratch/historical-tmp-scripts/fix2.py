#!/usr/bin/env python3
"""Fix shim timeouts for the cold NIM path (runs on yote)."""

# 1. herd.yaml: kimi-k3-nim alias gets SHIM_CONNECT_TIMEOUT=240.
#    The shim's getresponse() covers connect+send+wait-for-headers; the
#    NIM cold path needs ~136s before upstream headers arrive.
p = "config/herd.yaml"
s = open(p).read()
old = """  kimi-k3-nim:
    cmd: python3 /home/toxic/sovereign/config/herd.d/alias-shim.py --port ${PORT} --target nim-kimi/moonshotai/kimi-k3 --name kimi-k3-nim
"""
new = """  kimi-k3-nim:
    cmd: python3 /home/toxic/sovereign/config/herd.d/alias-shim.py --port ${PORT} --target nim-kimi/moonshotai/kimi-k3 --name kimi-k3-nim
    env:
      - SHIM_CONNECT_TIMEOUT=240
"""
assert old in s, "kimi-k3-nim cmd anchor missing"
assert "SHIM_CONNECT_TIMEOUT=240" not in s, "already patched"
s = s.replace(old, new, 1)
open(p, "w").write(s)
print("herd.yaml: kimi-k3-nim SHIM_CONNECT_TIMEOUT=240")

# 2. pitchfork.toml: kimi-auto-shim run line gains the nim-kimi standby
#    (must match herd.d/kimi-auto.yaml) + SHIM_CONNECT_TIMEOUT.
p = "pitchfork.toml"
s = open(p).read()
old_run = 'run = "exec python3 /home/toxic/sovereign/config/herd.d/alias-shim.py --port ${KIMI_AUTO_SHIM_PORT} --target openrouter-free/moonshotai/kimi-k3:free --standby openrouter-free/moonshotai/kimi-k2.6:free --standby openrouter-free/moonshotai/kimi-k2.5:free --standby openrouter-free/moonshotai/kimi-k2.7-code:free --standby hf-free/moonshotai/Kimi-K3 --advance-on 5xx,conn,429,402,404 --name kimi-auto"'
new_run = 'run = "exec python3 /home/toxic/sovereign/config/herd.d/alias-shim.py --port ${KIMI_AUTO_SHIM_PORT} --target openrouter-free/moonshotai/kimi-k3:free --standby openrouter-free/moonshotai/kimi-k2.6:free --standby openrouter-free/moonshotai/kimi-k2.5:free --standby openrouter-free/moonshotai/kimi-k2.7-code:free --standby hf-free/moonshotai/Kimi-K3 --standby nim-kimi/moonshotai/kimi-k3 --advance-on 5xx,conn,429,402,404 --name kimi-auto"'
assert old_run in s, "kimi-auto-shim run anchor missing"
assert "nim-kimi/moonshotai/kimi-k3 --advance-on" not in s, "already patched"
s = s.replace(old_run, new_run, 1)
old_env = 'env = { KIMI_AUTO_SHIM_PORT = "25153" }'
new_env = 'env = { KIMI_AUTO_SHIM_PORT = "25153", SHIM_CONNECT_TIMEOUT = "240" }'
assert old_env in s, "kimi-auto-shim env anchor missing"
s = s.replace(old_env, new_env, 1)
open(p, "w").write(s)
print("pitchfork.toml: kimi-auto-shim nim-kimi standby + SHIM_CONNECT_TIMEOUT=240")
print("PATCHES DONE")
