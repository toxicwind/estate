# Zedra — Audit

> Cloned to `/home/toxic/projects/zedra` (depth-1, `tanlethanh/zedra`, v0.3.1).
> Audited with `ast-grep-xray:explore_repo` + `ghas:ghas_get_file_contents` on the
> daemon (`crates/zedra-host`) and protocol (`crates/zedra-rpc/src/proto.rs`).

## Verdict: YES — this is the tool for phone → Zed-agent remote control

Zedra is a mobile remote client (iOS App Store / Android Play) for a **desktop
daemon** that exposes your workspace terminal, filesystem, git, and AI agents over a
secure P2P tunnel. The phone app drives a `zedra` CLI daemon running on your desktop;
the daemon speaks a typed RPC protocol to the app and can launch/attach AI agents
(Claude Code, Codex, etc.) in terminals. That is exactly "drive the Zed agent from my
phone." It is **not** a Zed extension — it is a standalone GPUI app + daemon — but it
achieves the goal (external, phone-based control of your coding agent).

## What it is

- **Desktop daemon** (`zedra` binary, `crates/zedra-host`): iroh P2P endpoint, auth,
  session/PTY management, fs/git, managed-agent registry, localhost REST API.
- **Mobile app** (`crates/zedra`): GPUI UI (iOS `gpui_ios`+Metal primary, Android
  `gpui_android`+Vulkan secondary), platform bridge, remote terminal renderer.
- **Transport**: iroh (QUIC/UDP) P2P with relay fallback; e2e TLS 1.3, no creds leave
  device. Direct connect when possible, relay when behind Symmetric NAT / CGNAT.

## Repo map (crates)

| Crate | Role |
|-------|------|
| `zedra` | Mobile app: GPUI UI, workspace orchestration, platform bridge |
| `zedra-host` | Desktop daemon + `zedra` CLI: iroh endpoint, auth, sessions, PTY, fs/git, managed agents |
| `zedra-session` | Client connect/reconnect, auth, session events, remote terminal attach |
| `zedra-terminal` | Reusable terminal emulator + GPUI renderer (alacritty model, OSC) |
| `zedra-rpc` | irpc protocol types + QR pairing between client and host |
| `zedra-osc` | Packet-safe OSC scanner for PTY byte streams |
| `zedra-telemetry` | Typed telemetry events, per-runtime backend injection |

Per-crate `AGENTS.md` exists for `zedra`, `zedra-host`, `zedra-session`, `zedra-terminal`
— read the owning crate's file before working there. `docs/` has 30+ deep-dive docs
(ARCHITECTURE, NETWORK_TRANSPORT, PROTOCOL_SPECS, MANAGED_AGENTS, DELTA_INTEGRATION…).

## Security model (from `proto.rs` + `main.rs`)

- **Pairing**: phone scans a QR containing `endpoint_id` + `handshake_secret` +
  `session_id`. First pairing = `Register` with `HMAC-SHA256(handshake_key,
  client_pubkey || timestamp)`; host rejects if |now−ts| > 60s (replay guard).
- **Per-connection auth**: Ed25519 challenge/response. Host signs a fresh nonce with
  its iroh `SecretKey`; client MUST verify `host_signature` before proving identity.
  Client proves with its own app-key signature. Separate key from the iroh transport
  key.
- **Resume**: in-memory `session_token` enables fast reconnect without QR; falls back
  to PKI challenge.
- **Protocol**: `ZEDRA_ALPN = b"zedra/rpc/4"`. Postcard (binary) over iroh QUIC.
  Enum is **append-only** (ordinal encoding) — never reorder/insert mid-enum.
- **Workspace lock**: one daemon per workdir; `start --detach` refuses a second.
- **Local REST API**: bound to 127.0.0.1, random port, 32-byte bearer token written
  to config dir (mode `0600`). Tools like `/zedra-start` discover via `api-addr` +
  `api-token`.
- **Web tunnel**: only ever forwards **loopback** targets (`is_loopback_host`);
  both app and host reject non-loopback early (shared trust boundary).
- **Telemetry**: anonymous GA4 on by default; disable via `--no-telemetry` or
  `ZEDRA_TELEMETRY=0`.

## RPC surface (high level)

Auth (`Register`/`Authenticate`/`AuthProve`/`Connect`) → Health (`Ping`) → Session
(`GetSessionInfo`/`List`/`Switch`) → FS (`FsList`/`FsRead`/`FsWrite`/`FsStat`/
`FsWatch`/`FsSearch`/`FsUpload`/`FsDocsTree`) → Terminal (`TermCreate`/`TermAttach`/
`TermResize`/`TermClose`/`TermList`/`TermReorder`) → Git (`GitStatus`/`Diff`/`Log`/
`Commit`/`Stage`/`Unstage`/`Branches`/`Checkout`) → AI (`AiPrompt`) → LSP
(`LspDiagnostics`/`LspHover`) → Managed agents (`AgentList`/`AgentSessions`/
`AgentResume`/`AgentInstalledList`/`AgentFiles`) → Web (`WebConnect`). Host pushes
`HostEvent`s (terminal created, git changed, agent hook, agent state) over a
subscribe channel.

## Build / run / setup

```shell
# Prereqs: Rust toolchain, GPUI deps; submodules for vendored GPUI (vendor/zed)
# Full setup: see docs/GET_STARTED.md

# Host CLI (binary is `zedra`)
cargo run -p zedra-host -- start --detach      # daemon for this workdir
zedra qr                                      # show pairing QR
zedra status                                  # sessions/terminals
zedra setup                 # configure hooks for detected agents (claude/codex)
zedra setup claude          # configure for one agent
zedra agent <subcommand>    # inspect managed AI-agent integrations
zedra stop                  # stop daemon

# Phone: install Zedra from App Store / Play, scan the QR. That's it.
```

CI-parity checks (from repo AGENTS.md):
```shell
cargo fmt --check
cargo check -p zedra-rpc -p zedra-session -p zedra-terminal -p zedra-host
cargo test  -p zedra-rpc -p zedra-session -p zedra-terminal -p zedra-host \
            -p zedra-osc -p zedra-telemetry
```

## Gotchas / notes

- `vendor/zed` is a **git submodule** (fork `tanlethanh/zed`, branch `feat/gpui-mobile`).
  Touching GPUI/platform code means inspecting it too; root workspace excludes `vendor`.
- iOS is the primary dev path; Android secondary. `cargo check -p zedra` (host target)
  silently excludes iOS-only deps — use `cargo check -p zedra --features ios-platform
  --target aarch64-apple-ios` for app-crate changes.
- Managed agents resolve through a registry (`ACTORS` array in `agent/mod.rs`); never
  add per-agent `match` arms to REST/CLI/hooks — everything goes through the registry.
- `zedra` CLI is the desktop side; the phone app is a separate native build (Xcode/
  Gradle). To change *phone* UX you build the app, not just the daemon.

## Why not a Zed extension?

Zedra does not plug into Zed's editor; it is its own editor (GPUI) + a daemon that
*hosts* your existing agents (Claude/Codex) in terminals. If you specifically need an
in-Zed agent bridge, that is a different project — but for "control my coding agent
from my phone," Zedra is the right, working, actively-developed answer.
