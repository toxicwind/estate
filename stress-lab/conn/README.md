# stress-lab/conn — improbable-failure connection optimizer

Goal: keep the estate<->kite-cell tunnel alive-close-free.

Proven failure (2026-10-22, tailscaled + `open-conn-track` evidence):
- tailscaled idle-closes the derp-1 (nyc) DERP link after ~2m15s of no traffic
  (`magicsock: closing connection to derp-1 (idle), age 2m15s`).
- That close = the recurring "remote end closed without response" bridge flap;
  re-handshake brings it back ~5min later, so kite sees down/healthy cycling.
- Separately, the cell sshd/kite connector is down (`:22` RST, ping timeout) —
  the END-TO-END tunnel won't carry traffic until that listener is restored.

Owner + semantics:
- `keepalive-tailscale.ts` — estate-side, removes the flapping cause: sub-idle
  pings keep the relay warm so tailscaled never idle-closes. Supervised by
  `pitchfork.d/tailscale-keepalive.toml`.
- TODO (cell-side, owner = cell admin): bring up `sshd` + kite connector on
  muse-1; then this keepalive keeps the now-live tunnel persistent.
- Paper-informed (paper-poller/arxiv): WireGuard real-world evaluation
  (arXiv 2512.10135) + Tailscale multi-node reliability (arXiv 2608.07226).

Run: `bun keepalive-tailscale.ts` (or supervised via pitchfork, 90s interval).
