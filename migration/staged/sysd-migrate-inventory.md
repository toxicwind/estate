# sysd-migrate re-landing inventory (worker b747b511 → mise-native)

Owner: d8b4b3b5. Status: STAGED — apply at tau-ledger cutover, not before.
Staged native definitions: `sysd-migrate-daemons.toml` (same directory).

## What b747b511 landed in generator sources

| # | Service | Port | Source commit | Generator location | autoStart | Group |
|---|---------|------|---------------|--------------------|-----------|-------|
| 1 | nginx | 62200 (NGINX_PORT) | db044f9a2d | `src/services/peripheral.ts` (`id: "nginx"`) + `config/ports.env` | true | aux |
| 2 | nim-proxy | 8000 (NIM_PROXY_PORT) | 5abe88d8b | `src/services/peripheral.ts` (`id: "nim-proxy"`) + `config/ports.env` | true | aux |
| 3 | matter-server | 5580 (MATTER_SERVER_PORT) | 5abe88d8b | `src/services/peripheral.ts` (`id: "matter-server"`) + `config/ports.env` | true | aux |

All three are TS-validated ServiceDefs with `mise: false`, `retry` semantics,
and `readyCmd` via `ss -ltn 'sport = :PORT'`.

## Current live state per def

- **nginx**: ALSO hand-appended as `[daemons.nginx]` in live `pitchfork.toml`
  (before the "don't hand-edit" correction; byte-consistent with generator
  output). Systemd unit stopped + disabled. **:62200 is dark until the
  supervisor restart** (only static `/crypto/` was live; both proxy upstreams
  were already dead — tau owns the upstream question).
- **nim-proxy**: raw docker container still running, verified healthy
  (`:8000` → 401, correct for keyed mode). In generator sources only.
- **matter-server**: raw docker container still running, Up (healthy) after
  the `/home/toxic/.matter_data` chown fix. In generator sources only.

## Native re-landing map (in sysd-migrate-daemons.toml)

| Generator field | Native `[daemons.*]` key |
|---|---|
| `run` | `run` (ports templated via `{{ vars.* }}`) |
| `readyCmd` | `ready_cmd` (port templated) |
| `dir: "."` | `dir = "/home/toxic/sovereign"` (absolute; generator's "." was ambiguous) |
| `mise: false` | `mise = false` (unchanged) |
| `autoStart: true` | `auto = ["start"]` (matches live `[daemons.nginx]` convention) |
| `group: "aux"` | no native equivalent → mise task with explicit daemon list at cutover |
| `portKey` | `[vars]` entry, referenced through Tera templates |
| (generator-added) | `retry = true` on all three (matches live nginx section) |

## Cutover checklist (post tau-ledger)

1. `docker stop nim-proxy matter-server` (before/at restart — name+port conflicts).
2. Merge staged `[vars]` + `[daemons.*]` into `/home/toxic/sovereign/mise.toml`.
3. Delete the three ServiceDefs from `src/services/peripheral.ts`; remove the
   hand-appended `[daemons.nginx]` when `pitchfork.toml` is retired.
4. Represent group `aux` as a mise task (`mise run aux-up/down/...`).
5. Restart supervisor on pitchfork 2.25.0, verify all three: ports, ready_cmd,
   retry, logs.

## Explicitly NOT in this re-landing (carve-outs, other owners)

- kafka / dnsmasq → tau worker (carve-outs).
- ralph-dashboard.service, awrawr-mcp.service → carve-outs, untouched.
- postgresql → left under systemd; needs Chris's call (data-dir ownership).
- itvx-browserless → compose-managed, left; squats on 25130 = ZEDRA_HOST_PORT (needs Chris's call).
- hw-audit.service/timer → oneshot timer, pitchfork has no timer concept.
- nvidia-clamp / fan-curve / mps, bubbleupnpserver, nanocoder-daemon → left/cleared per report.

Full report: worker b747b511's final report (completed 2026-09-14).
