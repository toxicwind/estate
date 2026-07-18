# Tailscale (sovereign)

Optional **Funnel** edge. There is **no Caddy** (removed: wrong ports, path conflicts with openfang `/api/*`, unused by `mise run up`).

## Surfaces (use directly)

| Service | Port | URL |
|---------|------|-----|
| llama-swap (LLM + chat UI) | 25100 | `http://127.0.0.1:25100/ui/` · `/v1` |
| rust-web (ops dashboard) | 25101 | `http://127.0.0.1:25101/` |
| yote | 25102 | … |
| openfang | 25103 | … |
| rest | see `config/ports.env` | 25xxx SSOT |

Over Tailscale: `http://<magicdns>:25100` etc. No reverse-proxy path soup.

## Funnel (optional)

`funnel.sh up` exposes **only rust-web** (`RUST_WEB_PORT`, default 25101) via Tailscale Funnel.  
It is **not** a multi-service gateway. For LLM remotely, use Tailscale + direct `:25100`.

```bash
bash /home/toxic/sovereign/tailscale/funnel.sh status
bash /home/toxic/sovereign/tailscale/funnel.sh down
```

## tailray

Tray applet module may still run; independent of Caddy.
