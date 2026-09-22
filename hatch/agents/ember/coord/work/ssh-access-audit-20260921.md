# SSH / access-path audit — awrawr-pc — 2026-09-21 (Gavel)

Scope: read-only posture check of remote access paths. No credentials touched, no keys read, no config changed.

## Listeners (ss -tlnp, relevant ports)

| Port | Bind | Process | Notes |
|------|------|---------|-------|
| 22 | 0.0.0.0 / [::] | sshd | Reachable via tailnet; Tailscale-SSH auth-walled (known) |
| 25120 | 100.72.199.93 + 127.0.0.1 | bun (pid 1878344, sovereign-chat) | Accepts TCP, drops HTTP with zero bytes — proprietary protocol, unchanged |
| 25104 | 127.0.0.1 | bun (pid 2213822, router) | Loopback-only; bake-off target, healthy |
| 25204 | 127.0.0.1 | python (pid 1799513, awrawr-ws-exec) | Loopback-only — the documented access blocker |
| 25198 | 127.0.0.1 | python (pid 2226793, awrawr-mcp) | Loopback-only — same blocker |

## sshd posture (config, no secrets)

- PermitRootLogin no
- PubkeyAuthentication yes
- PasswordAuthentication yes (also set in Match blocks)
- AllowUsers toxic

## Tailnet peers

- github-mcp-host (self, 100.72.199.93)
- almalinux-server (100.86.83.77)
- muse (100.91.187.58, active via relay)
- pixel-9-pro-xl (offline, 9d)

## Assessment

- No rogue listeners, no unexpected binds. Posture matches the known-good baseline.
- The loopback binding on :25204/:25198 remains the reason direct bridge access is impossible; the working path is the custom.awrawr-mcp surrogate via the tailnet proxy. That workaround stands — no "allow" gate involved.
- PasswordAuthentication=yes is noted (Chris's box, his call — not changing it).
- Nothing here blocks fleet work. Audit before send-off: PASS.
