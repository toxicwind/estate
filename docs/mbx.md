# mbx — the default build path

mbx ("mr-boxington") is the estate's build-cache system. **Every build on yote
goes through it by default.** Two components, one name:

## 1. `mbx` — Cargo compilation cache (CLI)

Shared compilation cache across checkouts: `Run mbx setup once, then keep
using Cargo normally.`

- **Installed:** via mise — `mbx = "latest"` in `/home/toxic/.config/mise/config.toml`
  (`[tools]`), currently 1.21.1 at
  `/home/toxic/.local/share/mise/installs/mbx/1.21.1/mbx`.
- **Default-path mechanism (primary):** mise command wrapper, set by
  `mbx setup --global` — one line in the global mise config:
  `wrappers = { cargo = { command = "mbx", env = { MBX_CARGO_SHIM_MODE = "1" } } }`.
  Every `cargo` resolved through mise shims (interactive shells, `mise exec`,
  yote-conn sessions) transparently runs through the mbx cache. No PATH tricks
  needed; it survives daemon restarts and fresh shells.
- **Fallback:** the cargo shim at `/home/toxic/.local/share/mbx/bin/cargo`
  (installed by `mbx setup`). Interactive shells also prepend that dir to PATH
  in `/home/toxic/.bashrc` (idempotent block) for tools that don't activate mise.
- **Cache:** `/home/toxic/.cache/mbx` (45 GiB budget, auto-gc), managed targets
  at `/home/toxic/.cache/mbx/targets`. `mbx stats` / `mbx cache` to inspect,
  `mbx gc` to collect.
- **Health:** `mbx doctor` — 0 failures, 0 warnings is the bar.

Just run `cargo build`. That's the whole interface.

## 2. `mbx-cache` — mise remote task cache (`:25148`)

Cache for `mise run` task artifacts: the first run executes, later runs
restore declared outputs instead of re-executing.

- **Server:** estate-built Rust binary from `vendored/mr-boxington-cache`
  (upstream `jdx/mr-boxington-cache` v0.1.1). Supervised by pitchfork as
  `estate/mbx-cache`, loopback-only `127.0.0.1:25148`
  (`MBX_CACHE_PORT` in `config/ports.env`). Launcher: `ops/mbx-cache/run.sh`;
  data: `var/runtime/mbx-cache`.
- **Client config:** `/home/toxic/.config/mise/conf.d/15-remote-cache.toml` —
  `task.cache.remote_url = "http://127.0.0.1:25148"`, namespace `"estate"`,
  mode `"read-write"`.
- **Use:** declare `sources`/`outputs` on a mise task, then `mise run <task>`.
  Deleting the outputs and re-running reports `restored outputs from cache`.
  If the daemon is unreachable, mise treats it as a cache miss and executes
  locally — fallback is built in, no separate path to maintain.
- **Health:** `curl -fsS http://127.0.0.1:25148/v1/status` → `{"protocol":1,"status":"ok"}`.

## Verify the default (yote)

```bash
command -v cargo        # /home/toxic/.local/share/mise/shims/cargo (wrapped → mbx)
mbx doctor              # 0 failures, 0 warnings
curl -fsS http://127.0.0.1:25148/v1/status
```

## Cell

The hatch cell has no Rust toolchain, so the cargo cache has nothing to
serve there — mbx is a yote default. (If a toolchain ever lands on the cell,
run `mbx setup` there too; the mise declaration is user-global already.)
