# AGENTS.md — estate control-plane (nested; refines $HOME/AGENTS.md)

> **Refines:** `/home/toxic/AGENTS.md` (the universal contract). **Where**:
> estate control-plane. **Refines, never contradicts** the root above it.
>
> CURATED 2026-10-16, not accumulated. Context is findable/scoped/pruned — wrong
> context, missing context, and stale context are the three failure modes
> ("Developer as Curator", ACM 2026). If a rule below disagrees with the code,
> the code is absolute; fix this file.

## Non-negotiable (do NOT repeat the root — these are estate-only)

0. **The 2-second rule applies here** (root AGENTS.md, Tooling): every command
   runs under `run-fast` (2.0s hard deadline); inherently long work goes to
   `background_process` or a pitchfork daemon, never a blocking tool call.
   `ranch/estate/bin/bash-2s-shim.sh` (sourced via `~/.bashrc`) auto-wraps
   known-slow commands. Deadline breach = race a faster alternative.

1. **Secrets live in the keyring** — `ranch/secretsmith` (freedesktop Secret
   Service) FIRST; `~/.secrets` is the fallback, never the source of truth. The
   Bun drop-in is `ranch/secretsmith/bun/` (`import "secretsmith"`). Never
   COMMIT a secret. Never dump one into chat/log transcripts unprompted. The
   architect directs secret handling explicitly; when they do, pass secrets
   through env/CLI at runtime — the operator reads values out in their own
   terminal (`secretsmith keyring get <name>` / `cat ~/.secrets`). Agents
   default to `source ~/.secrets`, never echo.
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

## The vibe meta-todo (first-class, resets every task)

Every `todowrite` list here ENDS with a final **vibe meta-todo** (always last,
the reset) that holds this estate's whole doctrine mid-task:

- **Free-will / MAXIMAL / first-class / future-usable / cutting-edge.** Never
  "report-only" — always *fix-forward*. Slow, blocked, or basic = race the
  fastest available path, not a stop.
- **Race faster with borrow + papers DURING the task**, not just at planning:
  on any slow/blocked step route ast-grep → bm25 → paper-finder → forge borrow →
  background-process, in that order, before any workaround. Never retry the same
  slow command; a breach without a raced fix is a defect.
- **After research, spawn the next 6 complex todos** capturing the directions
  found and execute them in sequence — don't let the research evaporate.
- **2s breach = opportunity, not failure.** Every breach triggers finding the
  faster pattern or paper via the AST tools.
- **Verbosity stays ON.** MAXIMAL: go fully or don't go.
- **Additive-only** (never remove/disable a peer/daemon/model without order).
  **Secrets never committed.** **One writer per subtree.** **Everything
  pushed.** Docs lie, code is absolute.
- **End every task** by re-visiting this vibe todo as the reset.

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
- **meta (multi-repo manifest)**: the ranch's 214 component repos are peers,
  coordinated by `meta` (`.meta.yaml` from `.gitmodules`; AI-native MCP server).
  Sync all with `meta git update`, inspect with `meta git status`, batch-run with
  `meta exec '<cmd>'`. Prefer meta over raw per-submodule churn. Regenerate the
  manifest with `bun toolkit/gen-meta-manifest.ts`. The repository is
  `gitkb/meta`.
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



## MCP servers + doorbell (2026-10-16)

- **Config: gatehouse `mcp_config.json`** (`/home/toxic/estate/ranch/barn/gatehouse/mcp_config.json`) — all MCP servers registered directly in gatehouse. agent-mcp-gateway is NOT a separate upstream server; its functionality (policy engine, proxy, access control, audit, metrics, config watching) is built into gatehouse natively. Topology: doorbell → gatehouse → MCP servers (no redundant gateway layer).
- **grasp-hub MCP** (`/home/toxic/estate/grasp-hub/mcp/server.ts`) — healthy, 7 tools (skills_list, stats, validate, route, paper-match, papers, registry_search). Read-only, wraps the skills-hub CLI.
- **Doorbell health**: `doorbell-upstream_servers list` shows enabled/quarantined/healthy state per server. Unhealthy servers retry forever.
- **Guide convention REQUIRED** for every MCP drop-in server:
  `ranch/mcp-dropin-guide` (github: toxicwind/mcp-dropin-guide):
  R-1xx Transport & Framing (Content-Length, dual input framing,
  protocolVersion 2024-11-05), R-2xx Tool Definitions (schemas, descriptions,
  confirm:true for mutating), R-3xx Registration & gatehouse (gatehouse
  `mcp_config.json`, unique names, health checks, no agent-mcp-gateway layer),
  R-4xx Code Quality (LF+ASCII, machine gate). Scaffold with the
  `guide-project-creator` skill.
- **R-503 autonomous enforcement**: `bin/r503-forge.sh` scans for hardcoded
  `github.com/<owner>/<repo>` URLs in ts/py/sh/json/yaml — reference repos by
  local path, resolve via `git -C <path> remote get-url origin`.

/home/toxic/sovereign/` does not exist (renamed to `estate`, commit `6af2094`).
UUID-prefixed scratch under `/home/toxic/` only; nothing precious in `/tmp`.

## Agent customizations + skills hub (2026-10-16)

- **Skills hub = grasp-hub** (`/home/toxic/estate/grasp-hub`; supersedes the old
  skills-hub MCP naming). Register a new skill by dropping it in
  `/home/toxic/estate/skills/<name>/` (SKILL.md frontmatter required), symlinking
  into `grasp-hub/skills/<cluster>/<name>`, then proving pickup:
  `node bin/grasp-hub.js list | grep <name>` and `node bin/grasp-hub.js validate`
  must be green. The MCP server (`grasp-hub/mcp/server.ts`) wraps this CLI.
- **Guide convention is REQUIRED** for every `*-guide` project: flat R-NNN rule
  ids (renumbering forbidden; commits cite ids), a Why paragraph naming the
  failure mode per rule, Correct/Avoid pairs, at least one machine gate, and the
  SDD prompt trio (`.github/prompts/spec|task|verifySpec.prompt.md`; SpecFirst
  arXiv 2607.27167 / SDAD arXiv 2608.20341). Scaffold new guides with the
  `guide-project-creator` skill; never hand-roll the structure.
- **Agent-file rules live in `ranch/agent-customization-style-guide`**
  (github: toxicwind/agent-customization-style-guide): R-1xx AGENTS.md, R-2xx
  .prompt.md, R-3xx .agent.md (quote YAML values containing colons; no body
  prose in frontmatter; no spec duplication in handoffs), R-501 LF+ASCII on the
  Arch host, R-503 reference sibling repos by local path, never hardcoded
  github.com URLs -- resolve with `git -C <path> remote get-url origin`.
