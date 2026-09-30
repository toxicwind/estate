import re, sys
B = '/tmp/browserless-rename'
def sub(path, pairs):
    p = B + '/' + path
    s = open(p).read()
    for old, new in pairs:
        assert old in s, f'MISSING in {path}: {old[:60]}'
        s = s.replace(old, new)
    open(p, 'w').write(s)
    print('ok', path)

G = [('itvx-browserless', 'browserless')]
sub('projects/mesh/browserless/server/pitchfork.fragment.toml', G + [
    ('merged into the [daemons.browserless] section', 'merged into the [daemons.browserless] section'),
    ('dir = "/home/toxic/sovereign/projects/mesh/browserless/server"', 'dir = "."'),
])
sub('projects/mesh/browserless/server/run.sh', [
    ('# browserless native launcher (sovereign mesh) \u2014 itvx deployment pattern.', '# browserless native launcher (sovereign mesh).'),
    ('itvx-browserless', 'browserless'),
])
sub('projects/mesh/browserless/package.json', [
    ('(sovereign mesh edition: itvx native-launcher deployment on 127.0.0.1:25130)', '(sovereign mesh edition: native-launcher deployment on 127.0.0.1:25130)'),
])
sub('projects/mesh/browserless/docker-compose.yml', [
    ('# itvx launcher at server/run.sh via pitchfork daemon browserless (:25130).', '# launcher at server/run.sh via pitchfork daemon browserless (:25130).'),
])
sub('projects/mesh/browserless/config.json', G)
sub('projects/mesh/browserless/TEST_RESULTS.md', G)
sub('projects/mesh/browserless/README.md', G + [
    ('**itvx native-launcher deployment**', '**native-launcher deployment**'),
    ('## What the itvx additions were', '## Deployment: native launcher'),
    ('Everything itvx added\nwas the ops layer, now carried in this project:', 'The ops layer, carried in this project (first built for the ITVX use case \u2014 see ):'),
    ('# itvx native launcher (pitchfork runs this)', '# native launcher (pitchfork runs this)'),
])
sub('projects/mesh/README.md', [
    ('# browserless.io MCP server + itvx native launcher (:25130)', '# browserless.io MCP server + native launcher (:25130)'),
])
sub('pitchfork.toml', G)
sub('src/services/peripheral.ts', [
    ('"itvx-browserless"', '"browserless"'),
    ('exec /home/toxic/.browserless/run.sh', 'exec /home/toxic/sovereign/projects/mesh/browserless/server/run.sh'),
])
print('ALL EDITS APPLIED')
