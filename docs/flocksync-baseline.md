# flocksync baseline — 2026-10-09

Pre-consolidation fleet state. Every later step is measured against this file.
Raw artifacts: `var/backups/flocksync-baseline-20261009T094833Z/`
(`storage.sqlite`, `env.txt`, `models.json`, `models-flock.json`, `models-vans.json`, `models-herd.json`).

## Services

| Service | Port | Runtime | Supervision | Artifacts |
|---|---|---|---|---|
| OmniRoute | 20130 | Next.js 16.3.5, image `diegosouzapw/omniroute:latest` | docker `omniroute-gateway` | `models.json` (2999) |
| flock-proxy | 25193 | Rust, binary `~/flock` | pitchfork `flock` | `models-flock.json` (538) |
| VansRouter | 20128 | Node CLI, `/usr/lib/node_modules/vansrouter/app` | pitchfork `vansrouter` | `models-vans.json` (14) |
| herd / roost | 25100 | TS/Bun router | pitchfork `herd` | `models-herd.json` (52) |

## Model counts

```
omni   = 2999
flock  =  538      of which 535 absent from omni
vans   =   14      of which  11 absent from omni
herd   =   52
UNION  = 3597
```

The `442 flock-only` figure quoted before the baseline was measured on a partial
comparison; the verified number is **535**. Flock-only models include
`claude-haiku-4.5`, `z-ai/glm-5.3`, and the openrouter set (447 of 538).

## Database

`var/omniroute/data/storage.sqlite`, bind-mounted into the container (added
2026-10-09; before that the container had zero volumes and all state lived in
the writable layer).

```
bytes     = 6385664
integrity = ok
tables    = 138
provider_connections = 15
```

## Gateway access

- Management password: `estate` (bcrypt hash in `key_value` namespace `settings`).
- Gateway API key: `~/.config/omniroute/gateway-key`.
- Flock proxy API key: `FLOCK_API_KEY` in the **container** env only. The value in
  `~/.tau/.env` is 14 chars and returns 401; the container value is 55 chars and
  returns 200. Do not source flock's key from the tau env file.
- VansRouter key: `VANSROUTER_API_KEY` in `~/.tau/.env`. Absent from the container env.

## Container env

214 values, 0 duplicate keys, 0 carriage returns, 4 intentionally empty.
Record: `env.txt`.

## Known-broken at baseline (carried into the plan, not fixed by it)

- `kimi-auto` (`:25153`) answers `/v1/models` with 200 but every completion
  returns `no router for requested model`. Its six failover targets no longer
  exist in herd.
- Providers auto-disabled despite passing their credential test:
  `nvidia`, `cerebras`, `deepseek` show `test_status=active` with `is_active=0`.
  `groq` is genuinely dead (upstream 401).
- `cerebras/zai-glm-4.6` is a phantom id, absent from the 2999. It appears only
  in September session logs.

## Tailscale

`tailscale serve` route `https://estate.tailc9ac71.ts.net:8443` →
`http://127.0.0.1:20130`, tailnet-only. Route count 26 before this work. The
25-route Funnel table at `:443` is public and unrelated; use `serve`, never
`set-path`.
