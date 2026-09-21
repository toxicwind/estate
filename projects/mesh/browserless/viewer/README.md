# agent-viewer-gate

Token-gated front door for the noVNC agent viewer (`:6080`, loopback-only, interactive).

- Listens `127.0.0.1:6081`, requires `?token=` (`/home/toxic/.browserless/viewer-token`, 0600) or the `aview` cookie,
  then proxies HTTP + websocket upgrades to websockify on `:6080`.
- Funnel mounts this at `/agent-browser` (see `projects/yote/ops/funnel-map.sh`).
- `/healthz` → 200, no token (pitchfork `ready_cmd`).
- The VNC password itself is never handled here — noVNC still prompts for it.

Full lane docs: `../keeper/README.md` → "Agent display + interactive viewer".
