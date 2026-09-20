p = '/home/toxic/mesh-bruteforce-20260914/tau/engine/crates/pi-vcs/src/git/mutate.rs'
s = open(p).read()
old = '\t\t\t"2020-01-02T03:04:05+00:00", // offset suffix unsupported\n'
assert s.count(old) == 1
s = s.replace(old, '')
open(p, 'w').write(s)
print('removed')
