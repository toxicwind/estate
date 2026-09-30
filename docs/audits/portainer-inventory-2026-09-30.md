# Portainer Estate Inventory — 2026-09-30

Auditor: Kestrel (portainer-audit/replacement-hunt lane). Verified live on yote unless noted.

## Verdict

**Portainer is a ghost.** No live Portainer instance exists anywhere on the estate.
It manages zero stacks, zero containers, zero volumes. Every deploy path that
referenced it is dead or was never live. The replacement does not need to
migrate anything — it replaces the *idea* of dashboard-driven container
management with agent-driven infrastructure.

## Instance hunt (all negative)

| Check | Result |
|---|---|
| `ps aux \| grep -i portainer` on yote | no process |
| `docker ps -a` on yote | hindsight, nim-proxy, browserless (exited), dagger-engine — no portainer |
| `docker images \| grep -i portainer` | none |
| `docker volume ls \| grep -i portainer` | none |
| Ports :9000 / :9443 / :9001 on yote | nothing listening (`:8000` is dockerd's userland proxy, not Portainer) |
| Ports :9000 / :9443 / :8000 on tailnet almalinux-server (100.86.83.77) | connection refused / timeout |
| `http://mildlyawesome.com:9000` (URL baked into dedi-ops tooling) | domain resolves to Cloudflare IPv6 only — :9000 unroutable through CF; unreachable |
| Portainer references in sovereign (152k files, md/toml/yml/yaml/json) | zero matches |
| `which portainer`, /opt/portainer*, /var/lib/docker/volumes/*portainer* | none |

## Remaining references (all dead or manual-only)

1. **effusion-labs** (`toxicwind/effusion-labs`, `/home/toxic/projects/effusion-labs`):
   `.github/workflows/deploy.yml` builds on GH Actions → pushes GHCR →
   POSTs `PORTAINER_WEBHOOK_EFFUSION` secret. Last 5 runs **all failed**,
   most recent 2026-03-15 — broken 6+ months. (Owned by Burrow's deploy lane;
   not duplicated here.)
2. **dedi-ops** (`/home/toxic/projects/dedi-ops/vector/ops/portainer.py`):
   builds images and exports **tarballs for manual Portainer import** —
   tooling only, no API automation, no live instance behind it.
3. **dayz-discord-ops / dayz-toolkit** (`tools/gen_portainer_stack.py`):
   generates Portainer-ready Swarm stack YAML for manual use.
4. **effusion-labs docs** (`docs/ARTIFACT_SYNC.md`): describes "Portainer on
   dedicated hardware" as an aspiration; the dedicated hardware was never
   found.

## What Portainer managed, when, health

| Stack / use | Manager | Last known state |
|---|---|---|
| effusion-labs web + markdown-gateway | Portainer webhook (URL in GH secret, host unknown) | dead since ≤2026-03-15; every deploy run failing |
| dayz-discord-ops stacks | manual import (never automated) | tooling only |
| dedi-ops images | manual tarball import | tooling only |

Nothing is healthy. Nothing is orphaned-and-running. There is nothing to
decommission — only references to delete (Burrow's lane owns the effusion
webhook removal).

## Implication for the replacement

No migration of live Portainer state is required. The replacement must cover
the *capability* Portainer promised: build images, deploy stacks, read logs,
roll back — but as **MCP tools + completions an OpenFang agent drives**,
not a dashboard. See the switchboard (master skill router) design doc.
