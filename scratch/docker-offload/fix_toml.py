import subprocess, tomllib

pf = '/home/toxic/sovereign/pitchfork.toml'
s = open(pf).read()
old = 'env = {\n  BROWSERLESS_PORT = "25130",\n}'
new = 'env = { BROWSERLESS_PORT = "25130", }'
assert old in s, 'multi-line env not found'
s = s.replace(old, new)
open(pf, 'w').write(s)

# Validate
d = tomllib.load(open(pf, 'rb'))
print('valid TOML,', len(d.get('daemons', {})), 'daemons')
assert 'itvx-browserless' in d['daemons']
assert 'matter-server' in d['daemons']
assert 'nim-proxy' in d['daemons']
print('all three native daemons present')

def git(*args):
    return subprocess.run(['git'] + list(args), cwd='/home/toxic/sovereign',
                          capture_output=True, text=True)
print(git('add', 'pitchfork.toml').returncode, 'add')
r = git('-c', 'user.name=toxicwind', '-c', 'user.email=toxicwind@gmail.com',
        'commit', '-m', 'fix(pitchfork): single-line env for browserless (TOML 1.0)\n\nMulti-line inline tables are invalid in TOML 1.0; the parse failure\nwas preventing the supervisor from reloading config (stale docker\ndefinitions kept respawning).')
print(r.returncode, 'commit')
r = git('push', 'origin', 'kimi-collab-transport')
print(r.returncode, 'push')
