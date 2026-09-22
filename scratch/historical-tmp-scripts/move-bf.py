#!/usr/bin/env python3
"""Move beellama-fast to end of aliases block (positional quirk test)."""
import sys, yaml

p = sys.argv[1] if len(sys.argv) > 1 else '/home/toxic/sovereign/config/herd.yaml'
lines = open(p).read().split('\n')
# find aliases block bounds
start = next(i for i, l in enumerate(lines) if l == 'aliases:')
# block ends at next top-level key (peers:)
end = next(i for i, l in enumerate(lines) if l == 'peers:')
block = lines[start:end]
# extract the beellama-fast entry (2 lines: key + cmd)
bf_idx = next(i for i, l in enumerate(block) if l.strip() == 'beellama-fast:')
entry = block[bf_idx:bf_idx+2]
rest = block[:bf_idx] + block[bf_idx+2:]
new_block = rest + entry
lines[start:end] = new_block
open(p, 'w').write('\n'.join(lines))
d = yaml.safe_load(open(p))
print('order now:', list(d['aliases']))
