# QED — AI-Native Editor Workspace

`qed/` holds the editor layer of the stack: the **zed** fork and **zedra**, the remote/mobile substrate.

## Layout

```text
qed/
├── zed/     # toxicwind/zed fork — 241 Rust crates, GPUI rendering
│            # custom providers: NVIDIA NIM (direct), MCP-proxy-hardened
│            # OpenAI-compatible providers, tool-schema normalizers
└── zedra/   # remote substrate — mobile editor + desktop daemon with
             # P2P connectivity (see qed/zedra/README.md for its own docs)
```

## Verify

```bash
# Zed fork builds (241 crates, GPUI)
cargo check --manifest-path qed/zed/Cargo.toml --package zed

# Zedra TypeScript checks (biome lint + format, 30 files)
bun --cwd qed/zedra run check

# Zedra Rust workspace (7 crates: zedra, zedra-osc, zedra-rpc,
# zedra-session, zedra-telemetry, zedra-terminal, zedra-host)
cargo check --manifest-path qed/zedra/Cargo.toml --workspace
```

## Notes

- The zed fork carries the sovereign provider set (llama-swap on :25100, sovereign-router on :25104, NVIDIA NIM direct) — editor settings live in `~/.config/zed/settings.json`, not here.
- zedra is the upstream zedra project (mobile + daemon); this tree vendors it for the remote-editing path.
- zed sync:  — strategy for the embedded zed snapshot <->  fork (subtree graft, not yet executed).
- zedra's Rust workspace resolves against the canonical `qed/zed` tree (no `vendor/` copy): mobile-only gpui crates (`gpui_android`, `gpui_wgpu`, `gpui_ios`) exist in no local zed tree and are commented out in `zedra/crates/zedra/Cargo.toml` — host (linux/macos) builds check clean; re-enable with a mobile-capable zed vendor checkout for Android/iOS builds.
