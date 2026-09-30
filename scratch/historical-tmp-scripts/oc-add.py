from pathlib import Path
p = Path('/home/toxic/sovereign/pitchfork.toml')
t = p.read_text()
anchor = '[daemons.oracle-core]'
assert anchor in t, 'anchor not found'
assert 'daemons.oracle-chat' not in t, 'already present'
block = '''
[daemons.oracle-chat]
run = "exec /home/toxic/sovereign/agents/oracle-market/bin/oracle_chat.py"
dir = "/home/toxic/sovereign/agents/oracle-market"
mise = false
retry = true
env = { ORACLE_CHANNEL = "/home/toxic/.shingle/squawk-root/bid-market" }
auto = ["start"]
'''
# insert before the next [daemons. section after oracle-core
idx = t.index(anchor)
nxt = t.find('\n[daemons.', idx + len(anchor))
assert nxt > 0, 'no following section'
p.write_text(t[:nxt] + block + t[nxt:])
print('inserted ok')
