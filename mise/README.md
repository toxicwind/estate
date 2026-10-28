# mise/ — estate mise configuration (yote)

Global mise config for this box. Wired in via symlink:

    /home/toxic/.config/mise/conf.d -> /home/toxic/estate/mise/conf.d

(The symlink is the wiring. Without it, `conf.d/` is dead config —
caught 2026-10-03: the directory existed but was empty, so no
estate settings loaded.)

## conf.d/ (loads alphabetically)

- `00-toolchain.toml` — pins python/node/bun/rust/go/pitchfork versions
- `10-env.toml` — environment (currently empty)
- `15-remote-cache.toml` — **mbx is the default remote task cache**:
  `task.cache.remote_url = http://127.0.0.1:25148`, namespace `estate`,
  mode `read-write`, `[task_config.cache] enabled = true`.
  Server: `ops/mbx-cache` (pitchfork service `estate/mbx-cache`).
- `20-stack.toml`, `30-dev.toml` — estate task definitions

## Scoping rule (verified 2026-10-03, mise 2026.10.0)

`[settings]` (remote_url, namespace, experimental) cascade globally from
this directory. **`[task_config.cache]` does NOT cascade** — neither from
the global scope nor from a parent directory, with or without
`task_config.cascade = true`. Each project that wants cached tasks must
declare `[task_config.cache] enabled = true` in its own `mise.toml`
(or `cache = { enabled = true }` per task). Eligible tasks need declared
`sources` + `outputs`. Verified end-to-end: cold run executes, warm run
restores from mbx-cache in ~0.06s (3s task).
