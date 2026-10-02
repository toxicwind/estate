import tomllib
p = '/home/toxic/sovereign/pitchfork.toml'
old = '''[daemons.tau]
run = "exec /home/toxic/sovereign/projects/tau/engine/packages/coding-agent/dist/omp acp"
dir = "/home/toxic"
mise = true
retry = true
ready_cmd = "pgrep -f coding-agent/dist/omp > /dev/null"
depends = ["shep"]'''
new = '''[daemons.tau]
port = 25111
# P4 headless-TUI policy (2026-09-20): dist/omp acp is stdio-only (no --acp-port
# TCP flag on this binary). The TCP->stdio bridge makes it an observable daemon
# with a real TCP readiness probe instead of the pgrep liveness lie.
run = "exec node /home/toxic/sovereign/bin/acp-tcp-bridge.mjs 25111 /home/toxic/sovereign/projects/tau/engine/packages/coding-agent/dist/omp acp"
dir = "/home/toxic"
mise = true
retry = true
ready_cmd = "/home/toxic/sovereign/bin/tcp-probe 25111"
depends = ["shep"]'''
src = open(p).read()
assert src.count(old) == 1, 'anchor count=%d' % src.count(old)
open(p, 'w').write(src.replace(old, new))
with open(p, 'rb') as f:
    data = tomllib.load(f)
tau = data['daemons']['tau']
print('TOML-VALID')
print('run =', tau['run'])
print('port =', tau['port'])
print('ready_cmd =', tau['ready_cmd'])
assert 'PI_CONFIG_DIR' in tau['env'] and 'PI_OPENAI_STREAM_IDLE_TIMEOUT_MS' in tau['env'], 'env block damaged'
print('ENV-PRESERVED keys:', sorted(tau['env'].keys()))
