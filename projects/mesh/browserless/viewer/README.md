# agent-viewer-gate

RETIRED 2026-09-21 (Forge) -- Chris: token gate was not wanted; the viewer is
tailscale/network/agent access only. `/agent-browser` is now served
tailnet-only via `tailscale serve` on `:8443`, straight from websockify
`:6080` (see `projects/yote/ops/funnel-map.sh` SERVE_MAP). This script is
kept as reference only; it is no longer a pitchfork daemon and `:6081`
no longer listens.

What it was: token-gated front door for the noVNC agent viewer (`:6080`,
loopback-only, interactive). Listened on `127.0.0.1:6081`, required
`?token=` (or the `aview` cookie), then proxied HTTP + websocket upgrades
to `:6080`. Funnel mounted it at `/agent-browser`.

The VNC password itself was never handled here -- noVNC still prompts for it.

Full lane docs: `../keeper/README.md` -> "Agent display + interactive viewer".
