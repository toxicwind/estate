import sys
p = '/home/toxic/sovereign/pitchfork.toml'
s = open(p).read()
old = 'env = { BUILDSRV_ROOT = "/home/toxic/buildsrv", BUILDSRV_PORT = "25148", BUILDSRV_WORKERS = "2" }'
new = ('env = { BUILDSRV_ROOT = "/home/toxic/buildsrv", BUILDSRV_PORT = "25148", BUILDSRV_WORKERS = "2", '
       'RUSTC_WRAPPER = "sccache", SCCACHE_DIR = "/home/toxic/.cache/sccache", '
       'CC = "ccache gcc", CXX = "ccache g++", CCACHE_DIR = "/home/toxic/.cache/ccache", '
       'UV_CACHE_DIR = "/home/toxic/.cache/uv", CARGO_INCREMENTAL = "1" }')
assert s.count(old) == 1, 'match count=%d' % s.count(old)
open(p, 'w').write(s.replace(old, new))
print('EDITED-OK')
