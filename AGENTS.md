# AGENTS.md — awrawr-pc standing rules

> **CURATED 2026-10-21, not accumulated.** Right context = findable/scoped/pruned,
> never wrong/missing/stale ("The Developer as Curator", ACM 2026). A shallow root
> here + nested `AGENTS.md` files where a domain owns its own rules beats one
> wall-file that drifts ("Agent READMEs: 2,303 context files", ACM 2026).
>
> This file is **authoritative**. `/home/toxic/estate/AGENTS.md` mirrors it;
> nested `AGENTS.md` files refine, never contradict, the rules above them.

## Non-negotiable (verbatim, applies to every agent on this box)

1. **MAXIMAL.** Go fully, or don't go. Fix-repairs, never report-only audits.
   No review gates: commit, push, forward-only.
   1b. **Never leave the working tree dirty — commit/checkpoint your in-flight
   work before finishing.** If you touched a file, it gets committed and
   pushed (or delendai-checkpointed to origin) before you call it done — even
   when the work is partial or belongs to a prior in-flight change from
   another agent. "It's someone else's uncommitted change" is not an excuse:
   squat it, checkpoint it to a work-ref, and say so. A dirty tree is how
   work silently goes missing and how agents get confused ("did my change
   land?"). Under `shared-checkout-merge`, dirty local files may ALREADY be
   checkpointed on an origin work-ref — verify `git ls-remote origin
'refs/heads/**/wip/**'` before assuming work is lost, and checkpoint+push
   anything still uncommitted so the tree is clean at handoff.
2. **The box is live.** 89+ pitchfork+mise daemons. Additive only — never remove or
   disable a peer/daemon/model without an explicit order. Never touch
   `awrawr-mcp.service` from a bridge call. Never run the retired
   `bun run scripts/generate.ts` (would destroy 15 daemons).
3. **Secrets live in the secretsmith keyring** (`ranch/barn/secretsmith`,
   freedesktop Secret Service — the SSOT since 2026-10-18) with first-class
   `cookie-vault` integration (Firefox + keeper CDP :9223 sync). `~/.secrets` is
   a fallback record, never the source of truth. Inject keys into any
   process with `secretsmith env` (opt-in export lines) or inspect/manage
   with `secretsmith`. Secret printing is permitted. Never COMMIT them to git.
4. **Diverged main:** back up origin main as `backup/main-<date>` on origin first,
   then merge, then push. Never force-push main without that backup. Never push
   to evmts.
5. **Docs lie; code is absolute.** A claim in any `.md` that disagrees with the
   code is wrong. Fix the doc, don't work around it.
6. **Restart supervised services after any binary swap/redeploy (pitchfork), so
   the running estate adopts the change — "deployed" means a running process uses
   it, not just a file on disk.** Skip the restart only on an explicit
   "don't disrupt this flow" order (e.g. a live user session you must not kill).
   Applies to kappa, tau, kite and every pitchfork-supervised daemon.

## The vibe meta-todo (first-class, resets every task)

Every `todowrite` list ENDS with a final **vibe meta-todo** (always last, always
the reset). It holds the estate's whole doctrine so even mid-task you never lose
the thread:

- **Free-will / MAXIMAL / first-class / future-usable / cutting-edge.** Never
  "report-only" — always _fix-forward_. If something is slow, blocked, or basic,
  that's a signal to race the fastest available path, not to stop.
- **Race faster with borrow + papers, DURING the task, not just at planning:**
  on any slow/blocked step route `ast-grep` → `bm25` → **paper-finder** →
  **forge borrow** → `background_process`, in that order, before ANY workaround.
  Never retry the same slow command; a breach without a raced fix is a defect.
- **After research, spawn the next 6 complex todos** capturing the cutting-edge
  directions found and execute them in sequence — don't let the research
  evaporate.
- **2s breach = opportunity, not failure.** Every breach is the trigger to find
  the faster pattern or paper, via the AST tools.
- **Verbosity stays ON.** This project's ethos is MAXIMAL: go fully or don't go.
- **Additive-only** on the live box (never remove/disable a peer/daemon/model
  without explicit order). **Secrets never committed.** **One writer per
  subtree.** **Everything pushed** (commit/push/forward-only).
- **End every task** by re-visiting this vibe todo as the reset — it is the
  standing meta-context for the whole estate.

## Tooling — MCP-first doctrine

### Gatehouse MCP: First-Class Over Raw Bash

Calling raw bash subshells or binaries is flawed when **Gatehouse MCP**
(`http://127.0.0.1:25127/mcp`) and first-class retrieve tools exist. Gatehouse
federates MCP tools across the box — FFS, BM25, memory (`recall`/`retain`/`reflect`),
browser-keeper CDP (`computer` / `:9223`), and more — behind a unified interface.

**Use native tool calls and Gatehouse MCP interfaces over raw terminal commands.**
The following first-class tools are the primary interface, not bash:

| Tool         | Purpose                                                       |
| ------------ | ------------------------------------------------------------- |
| `read`       | File/URL/document reading with outline, budget, selectors     |
| `bash`       | Real facts/pipelines only — not specialized-tool work         |
| `edit`       | Anchored patch edits                                          |
| `write`      | Create/overwrite files                                        |
| `eval`       | Python/IPython, browser, computer control                     |
| `glob`       | File/directory discovery                                      |
| `find`       | Behavior-to-source mapping (first for unknown locations)      |
| `web_search` | Structured web search                                         |
| `lsp`        | Symbol-aware code intelligence (navigation, refactor, rename) |

#### Gatehouse MCP federated tools

Gatehouse at `http://127.0.0.1:25127/mcp` exposes MCP resources and tools for:

- **FFS** (full-text search, BM25 ranking, symbol indexing)
- **BM25** (relevance-ranked text search across the estate)
- **Memory** (`recall`, `retain`, `reflect` — long-term memory queries)
- **Browser-keeper CDP** (`:9223` — Chromium DevTools Protocol, `computer` object)
- **GitHub** (`gh` wrapper for repos, PRs, search, checkout, push)
- **Debug** (`xd://debug` — debugger access, breakpoints, stepping)
- **Ast-grep** (`xd://ast_grep`, `xd://ast_edit` — AST-aware search and rewrite)
- **Session tools** (`xd://retain`, `xd://recall`, `xd://reflect`, `xd://hashline`)

**Rule:** When a first-class tool or Gatehouse MCP tool exists for a task, use it.
Raw bash is a last resort — acceptable only for system introspection that no MCP tool
covers (e.g. `docker ps`, `ss`, `curl` for health checks).

### FFS — The Universal Search/Read Interface

`ffs` is a single CLI over a persistent on-disk index (Bigram, Bloom, Symbol, Outline).

| When you need to…                    | Use `ffs …`           | Notes                                                   |
| ------------------------------------ | --------------------- | ------------------------------------------------------- |
| Find a file by name fragment         | `find <needle>`       | substring, case-insensitive; `--scored` adds role/socle |
| Match by shape/glob                  | `glob '**/<pattern>'` | shell glob (`**`,`*`,`?`,`[…]`)                         |
| Content match, one pattern           | `grep <regex>`        | ripgrep semantics; `--group` groups by enclosing symbol |
| Content match, many needles          | `multi-grep`          | Aho-Corasick literal AND/OR                             |
| Read a file without flooding context | `read <path>`         | §budget-aware _outline_ by default; `--full` raw        |
| Sketch a single file's structure     | `outline <path>`      | tree-sitter, `--style agent/…`                          |
| Resolve a symbol to its definition   | `symbol <name>`       | tree-sitter AST, not substring                          |
| Who refers to this symbol            | `callers <name>`      | `--hops N` BFS (≤5)                                     |
| What this symbol calls               | `callees <name>`      | `--depth N`                                             |
| Defs + usages in one shot            | `refs <name>`         | full defs + paged callers                               |
| Full card per definition             | `flow <name>`         | def+signature+body+callees+callers                      |
| Peers at same scope                  | `siblings <name>`     | same class/file/module                                  |
| Imports + dependents of a file       | `deps <path>`         | import graph of a file                                  |
| Rank blast radius of a change        | `impact <symbol>`     | score = direct×3 + imports×2 + transitive×1             |
| See the whole workspace              | `map` / `overview`    | file counts + token estimates                           |
| Warm the indexes                     | `index`               | build Bigram/Bloom/Symbol/Outline caches                |
| Be an MCP server                     | `mcp`                 | replaces Grep/Glob/Read for agents                      |
| Recall the guide                     | `guide`               | print the embedded doc                                  |

- **Global flags**: `--root <dir>`, `--format text|json`. Listing commands
  (`find/symbol/callers/callees/refs/flow/siblings`) page with
  `--limit N --offset N`. Use `--limit` aggressively (5–20 usually enough).
- **Index-aware**: search correctness depends on fresh indexes. If a search
  returns nothing that should exist, `ffs index` then retry.
- **Symbols**: trailing `*` = prefix glob (`symbol Foo*`).
- Never `fd`/`rg`/`find`/`grep`/`cat` — that is a doctrine violation, not a
  fallback. `bash -lc` read-only is acceptable only when ffs cannot express the
  query (e.g. `docker ps`, `ss`, `curl`).

- **Patch safely with hashline**: ALWAYS carry the `read` anchor
  (`SWAP 641:3f2a..674:9b1c:`); never mix a bare op after a line-count-changing
  op; re-read every file and diff the `~/-/+` lines after every patch.
- **Live token counting**: `tok` (see `tok --help`).
- **The 2-second rule (MANDATORY): `run-fast` wraps EVERY command.**
  `/home/toxic/estate/bin/run-fast <cmd…>` — hard 2.0s wall-clock per
  execution; streams output live; deadline breach = FAILED, and the breach
  is the trigger to race a FASTER alternative (better code, new libs,
  pattern-borrow) — never to wait longer. Inherently long work (network
  fetches, builds, installs) goes to `background_process` or a pitchfork
  daemon — never a blocking tool call. The bash tool auto-shims known-slow
  commands through run-fast (`bin/bash-2s-shim.sh`, sourced in the shell).
- **Verification**: parallelize reads; persist every check's FULL output to a file
  and give a PASS/FAIL per check with evidence. Truncated stdio is a defect, not
  a result. Two real failures on one target → stop and replan.

## Provider doctrine

- **Provider catalog SSOT — Pinax**: `@toxicwind/pinax` (`estate/ranch/pinax`) is
  the single source of truth. It generates `tau-models.yml`, `kappa-models.json`,
  `providers.go`, `providers.rs`, and `providers.json`. **"roost" is retired and
  purged** — never reference it.
- **Primary fast inference — FreeInference** (`freeinference.org/v1`):
  models: `qwen3.6-35b`, `glm-5.3-flash`, `deepseek-v4-flash`, `minimax-m3`.
  **No hard provider concurrency cap** (proven 2026-10-22: 4 concurrent → all 200,
  no 429/rate-limit headers; Pinax defines no cap). A "429 with retry-after:1" seen
  from proxied tool calls is a **local Gatehouse/limiter concurrency shed**, not the
  provider. When a provider opts into client `unlimitedRetryOn429` (default off),
  ride a concurrency-contained 429 through (retry) rather than hard-stopping. The
  `maxConcurrency: 2` number is a **Kappa client knob** (`kappa.jsonc`), not provider
  doctrine. See `estate/ranch/estate-recon/muse-meta-hatch/docs/field-notes/kite-fleet-recon/
FIX-usage-limit-as-dev-env.md`.
- **Orchestration: Corral + DelendAI**:
  Multi-agent fleet orchestration is **Corral** (`@estate/corral`, `estate/ranch/corral`)
  merged with **DelendAI** (`shared-checkout-merge` development profile, proposal
  guardian, and speculative merge queue). **"super-ralph" is retired.**
- **DelendAI Checkpoint Fast-Path — `delend-quick`**:
  Under `shared-checkout-merge` repositories (such as `ranch`), direct commits to
  `main` are strictly blocked by the reference-transaction guard. Use the universal
  first-class helper `/home/toxic/estate/bin/delend-quick -m "<message>"` (on PATH).
  It auto-discovers changed paths, climbs to the repository root, safely normalizes
  the work-ref namespace (`heads/wip/${agent}/implement/${proposal}-${slice}-g1/${topic}`),
  executes `delendai work checkpoint`, and pushes the work-ref to `origin`.

## 25xxx fleet & dashboards

- **89 active supervised daemons** on 25xxx managed by pitchfork.
- **ranch-ui (port 25218)**: Consolidated dashboard serving DelendAI control plane
  SPA + herd proxy.
- **range-ui (port 25156)**: Vite dev server with `/api` proxying to control-api on
  port 25162.
- **Unified Chats**: First-class Tau + Kappa + Kimi running chats aggregator in
  `range/apps/delendai-control-plane` (`src/data/channels.ts`, `src/data/unified-chats.ts`).

## Working rules

- **Docker is scoped, not banned (decided 2026-10-16).** Two lanes:
  - **Lane A — estate services** (MCP servers, routers, daemons, watchdogs): native,
    supervised by pitchfork+mise. **Docker forbidden** — a container duplicating a
    pitchfork daemon steals its ports and strands stale NAT rules (rustdesk outage
    2026-10-16: stale REDIRECT rules broke remote 25221/25222 for days).
  - **Lane B — ops/websites deployables** (effusion-labs, arlockworks stacks): docker
    compose, in the site's own repo/infra dir, ports pinned in `config/ports.env`,
    bound to 127.0.0.1/tailnet unless intentionally public.
  - **Tie-breaker: one supervisor per service.** Before adding a pitchfork daemon,
    check `docker ps -a`; before dockerizing, check pitchfork. Compose file lives
    in the repo that owns the site.

- Stage scratch under `/home/toxic/`, unique per-task dirs (`mktemp -d`), never
  `rm -rf` a shared hardcoded /tmp path. Never leave a backgrounded bridge call
  outstanding — wait for delivery.
- One writer per subtree; many readers. Race redundant read-only approaches;
  first valid answer wins. Gates serialize: token scrub → pushes; stash merge →
  build.
- Luis guesses are starting points, not specs — fuzz/verify, don't anchor.

## Scope split (nested AGENTS.md)

| Path                                   | Owner of these rules                                      |
| -------------------------------------- | --------------------------------------------------------- |
| `/home/toxic/estate/AGENTS.md`         | estate control-plane: repos, skills, grasp-hub, pitchfork |
| `/home/toxic/estate/ranch/*/AGENTS.md` | each ranch component repo's own contract                  |

**Container path**: `$HOME/AGENTS.md` = this file; `$HOME/estate/AGENTS.md` = the
estate mirror. Every nested file declares _what it refines and where_; none
repeats or contradicts the universal contract above.

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

## Estate operating rules (session boot defaults)

These recur every session; honor them without being told.

- **Search/read:** use ffs / dedicated MCP tools (`ffs_*`, `bm25_*`), never raw
  `grep`/`find`/`head`/`sed`/`cat` when an ffs tool covers the job. Do not
  truncate output with `head`/`tail` — persist full output and read it.
- **Commit + push forward-only.** Never leave the working tree dirty; if you
  touch a file, commit + push (or delendai-checkpoint) before done. Only commit
  YOUR files (pathspec); never sweep in peer WIP; stash-and-restore peer work if
  a rebase needs a clean tree.
- **No monkeypatch.** Every fix is a real committed file. Prefer fixing the root
  cause (e.g. a shared library/upstream) over a per-caller workaround; document
  drop-in TODOs when something is embedded and should import from the canonical
  package.
- **Secretsmith is SSOT (Rule 3).** Resolve keys/creds from the secretsmith
  keyring, never a stale env var. `secretsmith get --label <NAME> --show` —
  parse the `secret:` line.
- **Use the fleet tools.** Constant forge (now resilient: Brave/SERPER/Tavily/
  GitHub search legs) for pattern-borrow; `gh` for GitHub; the oracle market for
  engineering calls; keeper (persistent_*) is the logged-in browser, fast-browser
  for scripted known flows.
- **Ask, don't guess.** When a decision or a contributor's intent is unclear,
  ask via the `question` tool (the user would rather answer than correct a wrong
  guess). Use it liberally.
- **Naming map (2026-10-22):** EAP/Gemini Tool Retrieval = **@estate/theta**
  (PRIVATE `toxicwind/theta`, confidential — never public). Merged provider
  gateway (auth+keys+routing) = **atlas** (ex-cuttinggate). Key-pool router =
  keygate. EAP keys live in secretsmith (`GEMINI_EAP_KEY_1..6`), not env.
- **Home of the Greek-coded products (2026-10-22):** **olympus** (`toxicwind/olympus`,
  private) HOLDS the Greek codename lineage — τ tau, κ kappa, **skopos** (the
  persistent browser, was `keeper`), kilo, muse, keryx, hodos, kairos, kryptos.
  ranch/barn are ranch-structure (NOT Greek); only Greek-coded products join
  olympus. skopos = the keeper browser watcher (`ranch/keeper`, `keeper/bin/skopos.ts`,
  CDP :25154). Naming taxonomy: `kite-fleet-recon/NAMING-THEMES.md`.

## Emergent rig doctrine (2026-10-22) — deps allowed, dig deeper, maximal

- **New dependencies, shims, and bun-canary are ALLOWED.** There is no "no-deps"
  rule. Before building anything that could use a faster/newer runtime, check the
  latest bun canary:
  `npm view bun@canary version` and skim its changelog (e.g. 1.4.4-canary.yyyymmdd.N).
  Use it (or stable) whichever wins the race; prefer canary when a fix/API lands there.
- **Time is not a construct for the depth of exploration.** The 4s/2s race budget is
  for RUNNING a chosen tool fast, not for limiting how far you dig (byte-level RE,
  cross-codebase synthesis, skill updates). Dig deeper: reverse-engineer binaries,
  bring two codebases together, conjecture 3+ parallel experimental forward paths
  ("whoa, no one has bridged these yet — we can"), and race them in parallel.
- **delend-experimental**: when a step is novel/emergent, spawn a new agent that uses
  the code finder to auto-heal and auto-iterate itself, conjecturing multiple (3+)
  parallel divergent implementations chosen by code-race + borrow. Never settle on a
  single guess.
- **New agents (rigs) get a full rig auto-populated** via the rig-helper in
  `bin/rig-create` (openfang integration): persona + squawk join + config + glue
  auto-wired so any future agent can be scaffolded in seconds.

## GLOBAL GITHUB — MAJOR PRIMITIVE (2026-10-22)
The estate operates on **ARBITRARY upstream repos, not just toxicwind/*.** The primitive is
`bin/delend-gh <org/repo|url> [audit-main|raw <path>|<git-args>] [--keep]`: it resolves any
GitHub/gitlab/codeberg/self-hosted repo into a temp clone, runs a git op (default: a branch
audit vs the remote default branch), and cleans up. `bin/delend-branch-audit-for-main --repo
<path|url>` is the estate-wide branch audit on any repo. Global-by-construction: never assume
a repo lives under a specific org — always resolve from the provided org/URL. This is the
basis for foreign-pattern borrow, upstream tracking, and cross-org recon.
