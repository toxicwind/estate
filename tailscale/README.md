# Tailscale — the estate edge

<div align="right">

[![License: MIT](https://img.shields.io/badge/license-MIT%20%2B%20upstream-blue?style=for-the-badge)](https://github.com/toxicwind/estate-projects#license)
[![estate-projects](https://img.shields.io/badge/estate--projects-monorepo-blue?style=for-the-badge)](https://github.com/toxicwind/estate-projects)

</div>

Tailscale is how estate services leave the box safely. Every daemon binds
localhost/tailnet, and remote lanes reach them over MagicDNS — no open ports,
no reverse-proxy path soup, no Caddy.

## Why this layout

- **Direct over the tailnet** beats a multi-service gateway: one DNS name per
  service, zero path rewriting, and the LAN firewall posture stays closed.
- **Funnel is opt-in, single-backend**: `funnel.sh` exposes *only* the
  ranch dashboard (default port 25218) to the public internet. For LLM
  access remotely, use Tailscale + direct `:25100` — never funnel.

## Surfaces (use directly)

| Service                  | Port                      | Local URL                                | Over Tailscale            |
| ------------------------ | ------------------------- | ---------------------------------------- | ------------------------- |
| ranch dashboard          | `25218` (`RANCH_UI_PORT`) | `http://127.0.0.1:25218/`                | `https://<magicdns>:8444` |
| bornite (LLM API)           | `25100` (`HERD_PORT`)     | `http://127.0.0.1:25100/v1`              | `http://<magicdns>:25100` |
| model-guard (bornite proxy) | `25101` (`MODEL_GUARD_PORT`) | `http://127.0.0.1:25101/v1`           | `http://<magicdns>:25101` |
| yote                     | `25102` (`YOTE_PORT`)     | `http://127.0.0.1:25102/`                | `http://<magicdns>:25102` |
| openfang                 | `25103` (`OPENFANG_PORT`) | `http://127.0.0.1:25103/`                | `http://<magicdns>:25103` |
| everything else          | see `config/ports.env`    | 25xxx SSOT                               | same pattern              |

The ranch dashboard is the consolidated UI (ranch/range/ui), served by the
`ranch-ui` daemon: it fronts the built SPA and proxies the bornite API
same-origin, so the dashboard reaches bornite exactly as it did when it was
embedded. bornite's `/` redirects there (`BORNITE_DASHBOARD_URL`). See
`ranch/range/ui/CONSOLIDATION.md`.

```mermaid
flowchart LR
    you[laptop / phone] -->|tailscale| dns[<magicdns>]
    dns -->|:25100| bornite[bornite · LLM]
    dns -->|:25101| guard[model-guard · bornite proxy]
    dns -->|:25102| yote[yote]
    dns -->|:25103| fang[openfang]
    dns -->|:8444| dash[ranch dashboard]
    funnel[Tailscale Funnel] -.->|optional| dash
    note[public internet] -.->|funnel only| funnel
```

## Quick start

```bash
# check / bring up the optional public edge (rust-web only)
bash /home/toxic/pens/estate/tailscale/funnel.sh status
bash /home/toxic/pens/estate/tailscale/funnel.sh up
bash /home/toxic/pens/estate/tailscale/funnel.sh down
```

`funnel.sh up` sources `config/ports.env` for `RANCH_UI_PORT` (default 25218),
runs `tailscale funnel --bg`, and then parks (funnel dies with the process).
It is **not** a multi-service gateway: funnel exposes exactly one backend.

## Architecture

- **`funnel.sh`** — `up | down | status` wrapper around `tailscale funnel`.
  Single backend (no Caddy — removed: wrong ports, path conflicts with
  openfang `/api/*`, unused by `mise run up`). Logs under
  `/home/toxic/pens/estate/.state/logs`.
- **`tailray.service`** — systemd user unit for the Tailray tray applet
  (`/home/toxic/.cargo/bin/tailray`, `Restart=always`, needs `DISPLAY=:0`).
  Independent of Caddy and of funnel; purely a local tray UI. NOTE: the
  tailray binary is not currently built/installed (2026-10-14); the unit is
  inert until `cargo install tailray` is run.

## Config

| Knob | Source | Default |
| ---- | ------ | ------- |
| `RANCH_UI_PORT` | `config/ports.env` | `25218` |
| Funnel target | `funnel.sh up` | `$RANCH_UI_PORT` |

## Dev / contributing

Edits here are shell-only: `funnel.sh` and `tailray.service` ship as-is in
this directory. Keep funnel single-backend — multi-service reverse proxying
was deliberately removed.

## License & security

MIT — see [LICENSE](https://github.com/toxicwind/estate-projects#license).

- Tailscale's WireGuard identity is the auth boundary; no secrets live in
  this directory.
- Funnel is the only public-internet surface and it is opt-in. Nothing else
  here binds `0.0.0.0`.
