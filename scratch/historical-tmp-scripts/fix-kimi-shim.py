#!/usr/bin/env python3
"""Fix kimi-auto-shim pitchfork run line to match the router fragment. Run on yote."""
import sys

p = '/home/toxic/sovereign/pitchfork.toml'
s = open(p).read()

old = 'run = "exec python3 /home/toxic/sovereign/config/herd.d/alias-shim.py --port ${KIMI_AUTO_SHIM_PORT} --target kimi-k2.6 --standby kimi-k2.7-code --name kimi-auto"'
assert old in s, 'stale run line not found'
new = ('run = "exec python3 /home/toxic/sovereign/config/herd.d/alias-shim.py '
       '--port ${KIMI_AUTO_SHIM_PORT} '
       '--target openrouter-free/moonshotai/kimi-k3:free '
       '--standby openrouter-free/moonshotai/kimi-k2.6:free '
       '--standby openrouter-free/moonshotai/kimi-k2.5:free '
       '--standby openrouter-free/moonshotai/kimi-k2.7-code:free '
       '--standby hf-free/moonshotai/Kimi-K3 '
       '--advance-on 5xx,conn,429,402,404 --name kimi-auto"')
s = s.replace(old, new, 1)
open(p, 'w').write(s)

# sanity: valid TOML
try:
    import tomllib
    tomllib.load(open(p, 'rb'))
    print('pitchfork.toml valid TOML, kimi-auto-shim run line updated')
except ImportError:
    import tomli
    tomli.load(open(p, 'rb'))
    print('pitchfork.toml valid TOML (tomli), kimi-auto-shim run line updated')
