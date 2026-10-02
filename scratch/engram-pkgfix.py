import json

p = 'packages/engram/package.json'
d = json.load(open(p))
d['repository'] = {
    'type': 'git',
    'url': 'git+https://github.com/toxicwind/tau-extensions.git',
}
d['bugs'] = {'url': 'https://github.com/toxicwind/tau-extensions/issues'}
d['homepage'] = 'https://github.com/toxicwind/tau-extensions#readme'
with open(p, 'w') as f:
    json.dump(d, f, indent=2)
    f.write('\n')
print('package.json urls repointed:', d['repository']['url'])
