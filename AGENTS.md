# AGENTS.md — estate control-plane (nested; refines $HOME/AGENTS.md)

> **Refines:** `/home/toxic/AGENTS.md` (the universal contract). **Where**:
> estate control-plane. **Refines, never contradicts** the root above it.
>
> CURATED 2026-10-16, not accumulated. Context is findable/scoped/pruned — wrong
> context, missing context, and stale context are the three failure modes
> ("Developer as Curator", ACM 2026). If a rule below disagrees with the code,
> the code is absolute; fix this file.

## Non-negotiable (do NOT repeat the root — these are estate-only)

1. **Secrets stay in the keyring** — `ranch/secretsmith` (freedesktop Secret
   Service) FIRST; `~/.secrets` is the fallback, never the source of truth. The
   Bun drop-in is `ranch/secretsmith/bun/` (`import "secretsmith"`). Never print,
   log, or commit a secret.
2. **One writer per subtree.** Same as root's parallelism rule, reiterated for
   estate: two workers writing the same tree fratricide each other.
3. **The control plane is live**: ver `ranch/estate` → `estate` (commit `6af2094`),
   90+ pitchfork+mise daemons. Additive only. Never run `scripts/generate.ts`.
4. **Docker is scoped (2026-10-16)**: Lane A — estate services run **native under
   pitchfork+mise, never dockerized** (docker duplicates steal ports + strand NAT
   rules: rustdesk outage 2026-10-16). Lane B — ops/websites deployables
   (effusion-labs, arlockworks) run **docker compose in their own repo**, ports in
   `config/ports.env`, bound 127.0.0.1/tailnet unless intentionally public.
   Tie-breaker: **one supervisor per service** — check `docker ps -a` before adding
   a pitchfork daemon, and vice versa.

## Scope split (deeper nested files)

| Path | Owns |
|---|---|
| `/home/toxic/estate/ranch/<component>/AGENTS.md` | each ranch component repo's contract |
| `/home/toxic/estate/skills/<skill>/AGENTS.md` (if present) | that skill's own contract |
| `/home/toxic/estate/ranch/secretsmith/bun/` | the Bun secretsmith drop-in |
| `/home/toxic/estate/grasp-hub/` | skills registry + DAG router |

## Estate tooling canon (the boxes' ffs is the universal rule; estate-specific)

- **Search/read = `ffs`** exactly as the root AGENTS.md table; estate does NOT add
  a competing search tool. When an estate subcommand's semantics are unclear,
  `ffs guide` before guessing.
- **grasp-hub router**: `node /home/toxic/estate/grasp-hub/bin/grasp-hub.js
  route "<query>"` picks orthogonal sub-skills (GraSP DAG). Use it when a task
  spans >1 skill.
- **Git push everything** (root rule, restated for estate): commit after every
  unit of work, no local-only work. Never force-push `main` without a
  `backup/main-<date>` on origin. Never push to `evmts`/`super-ralph`.

## Verified ecosystem map (2026-10-14, spot-checked 2026-10-16)

| Thing | Path / port | Notes |
|---|---|---|
| Control plane repo | `/home/toxic/estate` | git repo on `main`; 90+ pitchfork daemons |
| Ranch (252 entries) | `/home/toxic/estate/ranch` | ferret-den at `ranch/ferret-den` |
| Tau engine (5.1G) | `/home/toxic/estate/ranch/tau` | own git repo, bazel+rust+bun |
| Tau agent config | `$HOME/.tau` → `estate/config/tau` | agent dir `$HOME/.tau/agent` |
| Skills | `/home/toxic/estate/skills` | pattern-forge, tau-session-audit, … |
| Secrets keyring | `ranch/secretsmith` | freedesktop Secret Service via D-Bus |
| Secrets vault (fallback) | `/home/toxic/.secrets` | record of last resort |
| Pitchfork defs | `/home/toxic/estate/pitchfork.toml` | SSOT, daemons |
| Mise defs | `/home/toxic/estate/mise.toml` | hand-edited; ports from `config/ports.env` |
| Port SSOT | `/home/toxic/estate/config/ports.env` | all 25xxx, never invent |
| Pitchfork CLI | `/home/toxic/estate/bin/pitchfork` | `pf check` reports real drift |
| Qdrant | `127.0.0.1:25133`/`:25134` | HTTP/gRPC |
| Redis (valkey) | `127.0.0.1:25203` | migrated off :25199 |
| Flicker build daemon | `127.0.0.1:25148` | ranch build daemon, NOT mbx-cache |
| awrawr-mcp | `127.0.0.1:25198` | live + auth-gated (stale-definition bug) |
| deep-paper-reader | `/home/toxic/src/local/deep-paper-reader` | paper-poller :25149/:25150 |

`/home/toxic/sovereign/` does not exist (renamed to `estate`, commit `6af2094`).
UUID-prefixed scratch under `/home/toxic/` only; nothing precious in `/tmp`.