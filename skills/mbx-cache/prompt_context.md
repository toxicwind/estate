# mbx-cache

- `mbx-cache` is the direct Rust, loopback-only remote cache for mise task artifacts.
- Port: `MBX_CACHE_PORT` in `config/ports.env` (`25148`).
- Lifecycle: `pitchfork` daemon `mbx-cache` through `ops/mbx-cache/run.sh`.
- Source: `vendored/mr-boxington-cache`, pinned v0.1.1; build with `mise exec -- cargo build --release`.
- No containers. Runtime data: `var/runtime/mbx-cache`.
- Cache clients: `mise/conf.d/15-remote-cache.toml`.
- It does not schedule work; `mise run <task>` executes work and the server restores/publishes immutable outputs.