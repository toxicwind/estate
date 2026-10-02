# pitchfork modularization hyper-race — RESULT (v2: per-project ownership)

**Ferret** (Ember's crew) · phase-3 worker · 2026-09-30
Lane: `pitchfork-mise-modularization/hyper-race` · coordinator: Bram (phases 1–2 done)

Inputs: Wren's paper findings (10 papers + 5 verified doc pages) and Magpie's
pattern borrows (systemd, supervisord, compose, k3s, runsvd + pitchfork upstream
verdict: **no include/drop-in mechanism exists through 2.29.0**; we run 2.25.0).
Prototypes raced against the real 82-daemon `pitchfork.toml` (995 lines, sandbox copy only).

**v2 reframe (Chris, 2026-09-30):** *"60 daemons in one file is insanity… Some
should belong in range and some in ranch, and EACH PROJECT SHOULD HAVE ONE."*
Round 1 raced file-splitting strategies; round 2 races **per-project ownership**:
each project (ranch animal, range component, standalone repo) owns its daemon
manifest(s); the parent at `/home/toxic/estate` **composes** — it does not own
60 daemon stanzas.

---

## Round 1 — file-splitting (A/B/C), condensed

Three designs, five phases, all against the sandbox 82-daemon file.

| Phase 1 merge (7 runs, median) | ms | Output bytes |
|---|---|---|
| A drop-ins (`pitchfork.d/NN-name.toml`) | 165.68 | 40,835 (comments preserved) |
| B typed manifests (`daemons.d/<name>.toml` → validate+serialize) | 193.29 | 28,797 |
| C layered fragments (root→leaf strategy table) | 154.67 | 27,981 |

**Tie** — cell variance (~2–6× run-to-run) exceeds the design gap. Parse time is
**not** a differentiator. Byte counts matter more: only A preserves comments
byte-for-byte (the live config's comments are incident documentation — the
beellama-fast 12h stale-definition incident, gatehouse self-heal notes,
`retry = 5 # was infinite; flappy daemon churned 125+ retries`).

**Phase 2 (conflicts, real git branches):** monolith same-section edits CONFLICT
(reproduces the committed `=======`/`>>>>>>>` incident); A with different-daemon
files → no conflict; same-daemon → conflict (honest limit).

**Phase 3 (hot-reload granularity):** one port change → exactly `["flock"]`
re-registers under all three (supervisord two-phase: parse+validate all, diff
per-daemon, restart only changed).

**Phase 4 (rollback):** single-file revert + re-merge, byte-identical, ~600 ms
(git-dominated). A fallback is not a rollback — these restore exact prior state.

**Phase 5 (5 stale):** A: `git rm` 5 files → 77 daemons. B: **fail-closed** —
generator exits 8 while a manifest exists for a retired name. C: hand-edit 2
shared multi-daemon fragments — the multi-writer hazard, reintroduced.

**Round-1 verdict was A + B's validator.** Chris's reframe demotes that: A keeps
all drop-ins in the *parent repo* — 82 files the parent still owns. Round 2 fixes
the ownership question.

---

## Round 2 — per-project ownership (A vs D1/D2/D3)

**Ownership map** (derived from each daemon's real `dir` field — ground truth of
where things run; 30 projects, 82 daemons):

| Project | Daemons | Notes |
|---|---|---|
| `sovereign` (the parent itself) | 37 | estate infra: herd, mesh-hub, keypool, model-guard, … |
| `ranch/oracle` | 6 | oracle-market/core/chat, market-watchdog + 2 stale |
| `ranch/squawk` | 4 | squawk-feed, fleet-ui, nats, nats-tail |
| `ranch/squawk-ws` | 2 | squawk-ws, squawk-ws-client |
| `ranch/flicker` | 2 | flicker, flicker-agent (both stale) |
| `ranch/windmill`, `ranch/stream-broker`, `ranch/barn/gatehouse` | 1 each | |
| `range` | 1 | mesh-landing — the ONLY daemon owned by range proper |
| `tools/buildsrv` | 2 | buildsrv, buildsrv-watchdog (1 stale) |
| `tools/kimi-claw` | 2 | |
| `tools/{null-g-proxy,sovereign-chat,ml-serve,bench-radar,sovereign-router}` | 1 each | |
| `projects/yote` | 1 | |
| `standalone/{12 projects}` | 16 | tau, awrawr×2, paper-poller×2, squawk-relay×2, … |

Range-vs-ranch, measured: **17 daemons belong to ranch/*, 1 to range proper.**
The split Chris asked about is real and the map makes it visible. (Trailboss's
authoritative fork/repo inventory was requested in fleet; this dir-derived map is
provisional until its answer lands — fold it in then.)

**Contestants:**
- **A** — parent-local `pitchfork.d/NN-<daemon>.toml` (round-1 baseline)
- **D1** — per-project `<key>/pitchfork/daemons.toml` (one manifest per project)
- **D2** — per-project `<key>/pitchfork.d/<daemon>.toml` (per-project drop-in dirs)
- **D3** — per-project `<key>/mise.toml` with `[daemons.*]` blocks (the mise question)

Parent owns only: `parent.toml` (preamble + groups + env — composition-level),
`projects.toml` (the registry: project → manifest path), and its own 37
sovereign daemons. Composer fails closed on duplicate daemon names across
projects (`OWNERSHIP CONFLICT`, exit 3).

### Phase 1 — merge race (7 timed runs, median)

| Design | Median | Valid¹ |
|---|---|---|
| A | 49.58 ms | ✅ |
| D1 | 95.28 ms | ✅ |
| D2 | 120.39 ms | ✅ |
| D3 | 72.89 ms | ✅ |

¹ Parsed output deep-equals the parsed original on `daemons`, `groups`, `env_file`.
**Tie again** — all compose the full set in <150 ms; run-to-run cell noise
dominates. Parse time remains a non-factor.

### Phase 2 — ownership clarity (computed, not opinion)

| Design | P1: daemon→project from path alone | P2: project's daemons `ls`-able |
|---|---|---|
| A | **0/82** — filenames carry no project info | no — one flat dir |
| D1 | 82/82 | no — must parse the manifest |
| **D2** | 82/82 | **yes** — `ls <key>/pitchfork.d/` |
| D3 | 82/82 | no — must parse mise.toml |

Under A you cannot tell which project owns a daemon by looking at the repo. Under
any D design the path *is* the answer.

### Phase 3 — per-project lifecycle

- **L1** (one daemon's port changes in ranch/oracle): restart set = `["oracle-core"]`
  under all designs — precise, no world-restart.
- **L2** (remove project ranch/oracle, 6 daemons): parent-repo files touched —
  **A: 6, D\*: 0** (+1 registry line). Under A the project's daemons live in the
  parent repo, so removing a project is 6 parent-repo edits. Under D it's
  `rm -rf` the project dir + one registry line; the parent is otherwise untouched.
- **L3** (add a project, 3 daemons): parent files touched — **A: 3, D\*: 0**
  (+1 registry line).

This is the structural payoff Chris asked for: **project add/remove is a
project-repo operation, not a parent-repo operation.**

### Phase 4 — conflict simulation (file-touch domain)

| Case | A | D1 | D2 | D3 |
|---|---|---|---|---|
| C1: same project, **different** daemons | no conflict | **CONFLICT** ❌ | no conflict | **CONFLICT** ❌ |
| C2: different projects | no conflict | no conflict | no conflict | no conflict |
| C3: same daemon | CONFLICT | CONFLICT | CONFLICT | CONFLICT |

D1 and D3 reintroduce the shared-file hazard *within* a project: two agents
editing different daemons of ranch/oracle collide on the one manifest / the one
mise.toml. D2 (like A) keeps one writer per daemon file — the common
multi-agent case stays conflict-free at both granularities.

### Phase 5 — the 5 stale as first test case

Under per-project ownership, where *should* each live?

| Stale daemon | Owner (from its real `dir`) | Why it's stale |
|---|---|---|
| bidder-forge, bidder-scout | `ranch/oracle` | oracle-market lane retired them |
| buildsrv | `tools/buildsrv` | brand→flicker cleanup |
| flicker, flicker-agent | `ranch/flicker` | cut over to :25148 in the flicker project |

Test: the owning projects retire the 5 in their own manifests; "running" set =
full 82 (what pitchfork runs now). The **orphan detector** (declared vs running):

```
D2 orphan detector: 5 orphans in 67.79 ms
  orphan: bidder-forge   (last project: ranch/oracle)
  orphan: bidder-scout   (last project: ranch/oracle)
  orphan: buildsrv       (last project: tools/buildsrv)
  orphan: flicker        (last project: ranch/flicker)
  orphan: flicker-agent  (last project: ranch/flicker)
```

D1 also finds 5/5 (92.97 ms). Under A the 5 files can be deleted too — but the
orphan is **unattributed**: nothing records which project owned them, so "who do
I ask?" has no answer. **Under D, staleness is obvious AND attributed**: the
owning project's manifest is the source of truth, and the detector names the
project. D2's retirement is also the cleanest mechanically: 5 file deletions
across 3 project dirs vs D1's 3 shared-file edits.

### Phase 6 — the mise question (one mise.toml per project vs parent-only)

- D3 prototype: the project's `mise.toml` (with `[tools]` + 6 `[daemons.*]`
  tables) parses; composition works (72.89 ms merge).
- **Caveat:** D3 relies on mise *ignoring* unknown tables — true today, but it's
  coupling to leniency. And one-mise.toml-per-project is **not** current reality:
  exactly one project (`tools/nuvio-platform`) has its own mise.toml; everything
  else is parent-only (`/home/toxic/estate/mise.toml`).
- Recommendation: **do not embed daemon stanzas in mise.toml.** If per-project
  mise files ever happen, keep daemon definitions in the adjacent
  `pitchfork.d/` dir (D2) — zero coupling to mise's schema evolution. D2 answers
  the mise question by making it unnecessary.

### Bonus finding (from building D's validator)

The polymorphic keys documented in round 1 (`port: number|array`,
`retry: boolean|number`, `ready_port: number|object`) ride along unchanged —
the D composer reuses the same fail-closed validation.

## Recommendation (v2, supersedes round-1)

**D2 — per-project `pitchfork.d/` drop-in directories, composed by the parent —
wins outright.** It is the synthesis of everything both rounds proved:

- From A: one-daemon-per-file (conflict-free common case, byte-identical comment
  preservation, `git rm` retirement).
- From B: fail-closed validation — duplicate daemon across projects is an
  `OWNERSHIP CONFLICT` error, never silent last-wins.
- From the reframe: **ownership at the project level** — 82/82 daemons
  path-attributable, project add/remove touches zero parent files, orphans are
  detected with project attribution.
- From C's defeat: no shared multi-daemon files anywhere (D1/D3 both failed C1).

Why not D1: one manifest per project reintroduces the within-project shared-file
hazard (C1 CONFLICT) and needs parsing to list a project's daemons.
Why not D3: couples composition to mise's schema leniency; the mise question is
better answered by adjacency than embedding.
Why not A alone: 0/82 ownership clarity; every project change is a parent-repo
edit — exactly the "60 daemons in one file is insanity" Chris rejected.

The parent at `/home/toxic/estate` keeps: `parent.toml` (preamble/groups/env),
`projects.toml` (registry), its own 37 sovereign daemons — and the composer.
Everything else lives with its project, including inside nested repos
(ranch/* manifests would commit to `toxicwind/ranch`, not sovereign).

## Migration plan (82 daemons, 30 projects)

1. **This lane**: prototypes + this RESULT.md committed (done below).
2. Harden `design-d/compose-d.ts` → `sovereign/bin/pitchfork-compose`
   (registry-driven, fail-closed); harden B's schema → `sovereign/bin/pitchfork-check`
   (validates merged output).
3. **Mechanical split** (one commit per project or a few, sandbox-verified first):
   for each of the 30 projects, move its daemon sections to
   `<project>/pitchfork.d/<daemon>.toml` (original text preserved); parent keeps
   `parent.toml` + `projects.toml`. Verify by composing and asserting
   parse-equality with today's file (the race harness does exactly this).
   Sequencing: `sovereign` (37) first, then ranch/* (17), then tools/*, then standalone.
4. **Nested repos**: ranch/* manifests move with their projects into
   `toxicwind/ranch` (the ranch checkout at `projects/range/ranch`) — the
   registry references them by path; daemon changes then flow through the
   project's own repo workflow.
5. **Sink**: feed the composed output to pitchfork 2.25.0 via native
   `pitchfork config add` — parent stays the entrypoint at `/home/toxic/estate`.
6. **Reload**: compose → diff → `bin/pitchfork-restart sovereign/<name>` for
   changed daemons only (L1 proven: 1 daemon in, 1 daemon out).
7. **Retire the 5 stale**: delete from their owning projects' `pitchfork.d/`
   (`ranch/oracle` ×2, `tools/buildsrv` ×1, `ranch/flicker` ×2) → 82 → 77
   daemons; the orphan detector confirms zero orphans after.
8. **Orphan watch**: run the detector on a schedule (or post-compose hook) —
   any running-but-undeclared daemon pages with its last-known project attached.
9. **Rollback**: `git checkout -- <project>/pitchfork.d/<daemon>.toml` + recompose
   (round-1 measured ~600 ms, byte-identical; per-project so blast radius is one
   project's dir).
10. **Trailboss follow-up**: fold its fork/repo ownership inventory into the
    project map when it lands in fleet; adjust project keys if it disagrees with
    the dir-derived map.

## Prototype inventory (committed alongside this file)

- `lib/toml.ts` — shared: parse, deep-equal, per-daemon diff, deterministic
  serializer, atomic write, ceilings, median timing
- `design-a/merge-a.ts` — drop-in merger, additive-ownership enforcement
- `design-b/gen-b.ts` — typed-manifest generator, fail-closed validation
  (demoted to validator-only per the reframe; central manifests contradict
  project-level ownership)
- `design-c/compose-c.ts` — fragment composer + `--explain` (rejected)
- `design-d/compose-d.ts` — **the winner's composer**: registry-driven,
  `OWNERSHIP CONFLICT` fail-closed, `--running`/`--attribution` orphan detection
- `setup.ts` / `setup-d.ts` — split the sandbox original into round-1 / round-2 layouts
- `race.ts` / `race2.ts` — the hyper-race harnesses (both portable: script-relative
  paths via `import.meta.dir`; run from anywhere with `bun race.ts`)
- `work/race/results.json`, `work/race2/results.json` — raw measurement data
  (regenerate with `bun race.ts` / `bun setup-d.ts && bun race2.ts`)

Live `/home/toxic/estate/pitchfork.toml` was not modified at any point.
