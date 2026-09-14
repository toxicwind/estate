# QED — AI-Native Editor (Zed Fork) + Remote Substrate

**qed/** is the editor layer of the Sovereign stack: the **Zed fork** (`qed/zed`)
and **Zedra** (`qed/zedra`), the remote/mobile P2P substrate.

- **zed/** — AI-native code editor engine (toxicwind Zed fork: `.ignore` for agent grep, sccache+mold builds)
- **zedra/** — remote daemon & mobile client substrate: P2P tunnel over QUIC/UDP (Iroh), mobile agent hooks, end-to-end encryption, remote headless daemon

## Ports

`:25130` belongs to **itvx-browserless** (headless browser for scraping). An
earlier version of this README claimed `:25130` for QED — that collision was
resolved 2026-09-14: **zedra-host moved to `:25146`** (`ZEDRA_HOST_PORT` in
`config/ports.env`). No zedra daemon is currently running.

## Layout

```text
qed/
├── zed/     ← Zed editor engine (toxicwind fork)
└── zedra/   ← Remote daemon & mobile client substrate (Zedra host)
```

## Quick verification

```bash
# Verify Zed workspace builds
cargo check --manifest-path qed/zed/Cargo.toml --package zed

# Verify Zedra daemon builds
bun --cwd qed/zedra test
```
