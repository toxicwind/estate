#!/usr/bin/env python3
"""Restore the local size-tier aliases (small/medium/code/long + beellama-fast)
as committed config. Run on yote. Idempotent: skips if aliases: already present."""
import sys

p = sys.argv[1] if len(sys.argv) > 1 else '/home/toxic/sovereign/config/herd.yaml'
s = open(p).read()
if '\naliases:\n' in s:
    print('aliases: section already present, nothing to do')
    sys.exit(0)

block = '''
# Local size-tier aliases (committed 2026-09-21 modelmap-r2): these were
# worktree-only WIP and were wiped by an unrelated config rewrite at
# 2026-09-21 06:26 MDT; restored here durably. Each entry is a full cmd
# model (distinct ctx/reasoning params per tier) -- the estate's
# sovereign-swap fork serves cmd blocks under top-level `aliases:`.
# Model files come from the macros: section (MODEL_DIR, QWEN35_9B_FLASH_IQ4XS,
# GEMMA_12B_BASE_Q4KM); both gguf files verified on disk 2026-09-21.
# Router config owns selection: retarget by editing the --model macros.
aliases:
  beellama-fast:
    cmd: ${BEELLAMA_BIN} --model ${QWEN35_9B_FLASH_IQ4XS} ${SRV_BASE} ${FORK_BEELLAMA} ${CTX_32K} ${KV_Q8} ${REASONING_ON} ${SPEC_NONE}
  small:
    cmd: ${BEELLAMA_BIN} --model ${QWEN35_9B_FLASH_IQ4XS} ${SRV_BASE} ${FORK_BEELLAMA} ${CTX_32K} ${KV_Q8} ${REASONING_ON} ${SPEC_NONE}
  medium:
    cmd: ${BEELLAMA_BIN} --model ${GEMMA_12B_BASE_Q4KM} ${SRV_BASE} ${FORK_BEELLAMA} ${CTX_32K} ${KV_Q8} ${REASONING_ON} ${SPEC_NONE}
  code:
    cmd: ${BEELLAMA_BIN} --model ${GEMMA_12B_BASE_Q4KM} ${SRV_BASE} ${FORK_BEELLAMA} ${CTX_32K} ${KV_Q8} ${REASONING_ON} ${SPEC_NONE}
  long:
    cmd: ${BEELLAMA_BIN} --model ${QWEN35_9B_FLASH_IQ4XS} ${SRV_BASE} ${FORK_BEELLAMA} ${CTX_256K} ${KV_Q8} ${REASONING_ON} ${SPEC_NONE}
'''

anchor = '\npeers:'
assert anchor in s, 'peers: anchor not found'
s = s.replace(anchor, block + '\npeers:', 1)
open(p, 'w').write(s)

import yaml
d = yaml.safe_load(open(p))
assert 'aliases' in d and set(d['aliases']) >= {'small', 'medium', 'code', 'long'}, 'aliases missing after edit'
print('aliases: section restored:', sorted(d['aliases']))
