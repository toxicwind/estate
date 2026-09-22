#!/usr/bin/env python3
"""Drop the dead beellama-fast entry (404s; duplicate of small). Keep small/medium/code/long."""
import sys, yaml

p = sys.argv[1] if len(sys.argv) > 1 else '/home/toxic/sovereign/config/herd.yaml'
lines = open(p).read().split('\n')
start = next(i for i, l in enumerate(lines) if l == 'aliases:')
end = next(i for i, l in enumerate(lines) if l == 'peers:')
block = lines[start:end]
bf_idx = next(i for i, l in enumerate(block) if l.strip() == 'beellama-fast:')
del block[bf_idx:bf_idx+2]
lines[start:end] = block
open(p, 'w').write('\n'.join(lines))
d = yaml.safe_load(open(p))
print('aliases now:', sorted(d['aliases']))
assert 'beellama-fast' not in d['aliases']
