p = '/home/toxic/mesh-bruteforce-20260914/tau/engine/crates/pi-vcs/src/jj/ops.rs'
s = open(p).read()
old = '\t\t\t\trender_numstat(repo.as_ref(), &before, &after, changes).await\n'
new = '\t\t\t\trender_numstat(repo.as_ref(), changes).await\n'
assert s.count(old) == 1, 'numstat public call'
s = s.replace(old, new)
open(p, 'w').write(s)
print('numstat call fixed')
