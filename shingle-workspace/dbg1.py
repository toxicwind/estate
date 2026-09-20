src = open('/tmp/fix_diff_hunks.py').read()
i = src.find('old = (')
j = src.find(')\nnew = (', i) + 1
ns = {}
exec(src[i:j], ns)
old = ns['old']
s = open('/home/toxic/mesh-bruteforce-20260914/tau/engine/crates/pi-vcs/src/git/diff.rs').read()
print('full match:', old in s)
for n, line in enumerate(old.split('\n')):
    if line and line not in s:
        print('MISSING line', n, repr(line))
