# Connection optimization — improbable-failure notes (main-released 5fc9af2362)

## The failure we eliminated (estate-side)
tailscaled idle-closes the derp-1 (nyc) DERP relay at ~2m15s of no traffic
(`magicsock: closing connection to derp-1 (idle), age 2m15s`). This close is the
recurring "remote end closed without response" bridge flap. `keepalive-tailscale.ts`
pokes the cell every 90s so the relay stays warm and never idle-closes.

## Paper-informed design (race: paper-poller/arXiv + OpenAlex + GitHub)
- arXiv 2512.10135 — Real-World Evaluation of WireGuard (vs IPsec, industrial). Confirms
  WireGuard data/keepalive under load; validates keeping the WG path warm.
- arXiv 2608.07226 — Dual-Node Tailscale testbed (distributed training). Confirms Tailscale
  mesh stability across nodes + the value of a persistent admin path.
- github tailscale/tailscale `wgengine/magicsock/endpoint.go` — authoritative source for
  magicsock relay/keepalive timing; informed the 90s (<135s) sub-idle interval.

## Remaining (cell-side, owner = cell admin)
The END-TO-END tunnel still needs muse-1 `sshd` (:22) + kite connector UP. This estate-side
keepalive removes the *flapping* cause so the tunnel is persistent the moment that listener
returns. Current state: keepalive reports cell `unreachable` (listener still absent).

## Run / supervise
- Interactive: `bun keepalive-tailscale.ts`
- Supervised: `pitchfork.d/tailscale-keepalive.toml` (retry+boot_start, 90s)
- State: `/tmp/keepalive-tailscale.json`
