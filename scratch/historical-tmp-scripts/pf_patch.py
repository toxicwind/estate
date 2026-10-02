import sys
p = '/tmp/bsrv-wt/pitchfork.toml'
lines = open(p).read().splitlines(keepends=True)
assert lines[482].startswith('env = { BUILDSRV_ROOT'), lines[482][:40]
new_env = ('env = { BUILDSRV_ROOT = "/home/toxic/buildsrv", '
           'BUILDSRV_PORT = "25148", BUILDSRV_WORKERS = "2", '
           'RUSTC_WRAPPER = "sccache", '
           'SCCACHE_DIR = "/home/toxic/.cache/sccache", '
           'CCACHE_DIR = "/home/toxic/.cache/ccache", '
           'CMAKE_C_COMPILER_LAUNCHER = "ccache", '
           'CMAKE_CXX_COMPILER_LAUNCHER = "ccache", '
           'UV_CACHE_DIR = "/home/toxic/.cache/uv", '
           'CARGO_INCREMENTAL = "0" }\n')
comment = ('# Build-cache env (2026-09-21): every buildsrv job inherits these. '
           'sccache/ccache/uv caches live on NVMe.\n'
           '# CARGO_INCREMENTAL=0 because sccache refuses incremental '
           'compilation outright.\n'
           '# CC/CXX intentionally NOT set: BASH_ENV rewrites them to clang '
           'for bash -lc jobs,\n'
           '# so CMAKE compiler launchers are the robust ccache path for '
           'CMake builds.\n'
           '# BUILDSRV_WORKERS stays 2 (16 logical CPUs; two Cargo builds '
           'already oversubscribe).\n')
lines[482] = comment + new_env
open(p, 'w').write(''.join(lines))
print('PITCHFORK_PATCH_OK')
