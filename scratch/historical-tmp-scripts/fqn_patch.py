import sys
p = '/home/toxic/sovereign/config/herd.yaml'
s = open(p).read()
anchor = '      alias_of: moonshot/kimi-k2.7-code\n'
assert s.count(anchor) == 1, "anchor count %d" % s.count(anchor)
addition = '''      alias_of: moonshot/kimi-k2.7-code
  # --- FQN aliases for openfang (added 2026-09-20) ---
  # openfang's llama-swap driver addresses herd models as <peer>/<model>
  # (fully-qualified). The 2026-09-20 17:04 herd binary regressed peer-FQN
  # routing: every <peer>/<model> 404s "no router for requested model"
  # while bare names still route. These fixed-target forwarders restore the
  # FQN paths openfang's agents need until the binary's FQN routing is fixed.
  # Retire when peer FQN routing works again (then these become redundant).
  "openrouter-free/nex-agi/nex-n2.5-mini:free":
    cmd: python3 /home/toxic/sovereign/config/herd.d/alias-shim.py --port ${PORT} --target nex-agi/nex-n2.5-mini:free
    description: "FQN alias -> nex-agi/nex-n2.5-mini:free (openfang coyote/kimiclaw)"
    metadata:
      alias_of: nex-agi/nex-n2.5-mini:free
      role: fqn-alias
  "toolcall-local/qwen3.5-9b-tool":
    cmd: python3 /home/toxic/sovereign/config/herd.d/alias-shim.py --port ${PORT} --target qwen3.5-9b-tool
    description: "FQN alias -> qwen3.5-9b-tool (openfang rig-toolcall)"
    metadata:
      alias_of: qwen3.5-9b-tool
      role: fqn-alias
'''
s = s.replace(anchor, addition)
open(p, 'w').write(s)
print("patched OK")
