# Docker Inventory & Lane Policy — 2026-10-16

**Doctrine (decided 2026-10-16, in `$HOME/AGENTS.md` + `estate/AGENTS.md`):**
Two lanes. **Lane A** — estate control-plane services run native under
pitchfork+mise; **docker forbidden** (a container duplicating a pitchfork daemon
steals its ports and strands stale NAT rules). **Lane B** — ops/websites
deployables run docker compose in their own repo, ports pinned in
`config/ports.env`, bound to 127.0.0.1/tailnet unless intentionally public.
**Tie-breaker: one supervisor per service** — check `docker ps -a` before adding
a pitchfork daemon, and vice versa.

## Incident record — rustdesk outage (fixed 2026-10-16)

- Old docker-compose rustdesk containers (`hbbs`/`hbbr`, host-network, root) owned
  ports 25220–25224 and shadowed the pitchfork-native daemons.
- Stale PREROUTING REDIRECT rules remapped inbound `25221 ⇄ 21116` (container's
  internal port) — remote tailnet clients got kernel RST →
  "Failed to connect / Please try later". Local connections bypass PREROUTING,
  masking the failure.
- `rustdesk-hbbr` was disabled in pitchfork state from the port-conflict era.
- Fix: removed 4 REDIRECT rules, `docker rm`'d both containers, `pf enable` +
  start hbbr, restarted hbbs. Verified TCP 25221/25222 from a remote tailnet node
  (almalinux-server): both OK.

## Container inventory (post-cleanup)

| Container | Image | State | Lane | Class | Verdict |
|---|---|---|---|---|---|
| effusion-web | effusion-web:1c60a70 | Up 4d (healthy) | B | effusionlabs.com + arlockworks nginx (:43000→80) | **keep** — bind 0.0.0.0 → should be 127.0.0.1 (findings TODO) |
| effusion-postgres | postgres:16 | Created | B | effusion stack DB | keep (stack member, not started) |
| nim-proxy | ghcr.io/miztertea/nim-proxy | Up 15h (healthy) | B | NIM completion proxy (:8000, loopback) | keep |
| hindsight | ghcr.io/vectorize-io/hindsight | Up 2d | ? | memory/embedding service, no published ports | keep, **owner/origin undocumented — investigate** |
| dagger-engine-v0.21.9 | registry.dagger.io/engine | Up 4d | tool | Dagger CI engine (how dagger runs) | keep |
| omniroute-gateway | omniroute-gateway:layer | Up 2d (healthy) | A? | routing gateway (:20130→20128, loopback) | **borderline** — Lane A service in docker; serving traffic, do not kill; migrate to pitchfork when touched next |
| ~~7 removed~~ | — | — | — | omniroute-gateway-held20128 (dead dup), hr-nginx-54688, exciting_cori, hr-debug, hr-nginx-54585, recursing_snyder, browserless (dead 2w) | **removed 2026-10-16** |

Reclaimed: 12.13 GB build cache. Remaining images: 30 total / 9 in use.

## Process rules going forward

1. New estate service → `pitchfork.toml` + mise, never docker.
2. New website/ops stack → compose in the owning repo, port pinned in
   `config/ports.env`, loopback/tailnet bind unless intentionally public.
3. Before `pitchfork add`: `docker ps -a` must not already serve the role.
   Before dockerizing: pitchfork must not already serve the role.
4. Stale NAT rules that intercept SSOT ports = drift; remove on sight and
   record here.
