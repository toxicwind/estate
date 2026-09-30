#!/usr/bin/env python3
"""Remove the re-entrant oracle-judge-local shim; add native alias. Run on yote."""
import sys

p = sys.argv[1] if len(sys.argv) > 1 else '/home/toxic/sovereign/config/herd.yaml'
s = open(p).read()

old_block = '''  oracle-judge-local:
    cmd: python3 /home/toxic/sovereign/config/herd.d/alias-shim.py --port ${PORT} --target beellama/gemma-96k
    description: "Oracle judge fallback (alias -> beellama/gemma-96k) -- local last-resort slot filler"
    metadata:
      alias_of: beellama/gemma-96k
      role: oracle-judge-fallback
'''
assert old_block in s, 'shim block not found'
new_block = '''  # oracle-judge-local: native llama-swap alias of beellama/gemma-96k (2026-09-21).
  # Was an alias-shim.py cmd entry; REMOVED because a shim hosted INSIDE
  # llama-swap cannot forward to another llama-swap cmd model -- the swapper
  # cannot swap to the target while the shim holds the active slot for the
  # in-flight outer request (re-entrant deadlock: health 200, completions
  # hang -> 502). Native aliasing routes the swap directly, no re-entrancy.
  # Router config still owns selection: edit the aliases list below.
'''
s = s.replace(old_block, new_block, 1)

old_alias = '''  beellama/gemma-96k:
    cmd: ${BEELLAMA_BIN} --model ${GEMMA_12B_BASE_Q4KM} ${SRV_BASE} ${FORK_BEELLAMA} ${CTX_96K} ${KV_Q8} ${REASONING_OFF} ${SPEC_NONE}
    aliases:
      - gemma-96k
'''
assert old_alias in s, 'gemma-96k entry not found'
new_alias = '''  beellama/gemma-96k:
    cmd: ${BEELLAMA_BIN} --model ${GEMMA_12B_BASE_Q4KM} ${SRV_BASE} ${FORK_BEELLAMA} ${CTX_96K} ${KV_Q8} ${REASONING_OFF} ${SPEC_NONE}
    aliases:
      - gemma-96k
      - oracle-judge-local
'''
s = s.replace(old_alias, new_alias, 1)
open(p, 'w').write(s)
print('herd.yaml updated: shim removed, native alias added')
