import re, hashlib, os, subprocess

CANON = '/home/toxic/sovereign/pitchfork.toml'
pat = re.compile(r'^\[daemons\.([^\]]+)\]', re.M)

def daemons(path):
    try:
        return set(pat.findall(open(path).read()))
    except Exception:
        return set()

def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()[:12]

out = subprocess.run(['find', '/home/toxic', '-name', 'pitchfork.toml',
                      '-not', '-path', '*/node_modules/*',
                      '-not', '-path', '*/.git/*'],
                     capture_output=True, text=True).stdout.splitlines()

canon_d = daemons(CANON)
canon_sha = sha(CANON)
print('canonical: ' + CANON + ' sha=' + canon_sha + ' daemons=' + str(len(canon_d)))

for f in sorted(out):
    if os.path.islink(f):
        print('SYMLINK ' + f + ' -> ' + os.readlink(f))
        continue
    h = sha(f)
    if h == canon_sha:
        continue
    d = daemons(f)
    only_here = sorted(d - canon_d)
    only_canon = sorted(canon_d - d)
    print('== ' + f)
    print('   sha=' + h + ' daemons=' + str(len(d)) + ' +only_here=' + str(len(only_here)) + ' -missing=' + str(len(only_canon)))
    if only_here:
        print('   + ' + str(only_here[:20]))
    if 0 < len(only_canon) <= 12:
        print('   - ' + str(only_canon))
