# pitchfork.toml modularization — paper-finder + pattern-borrow + hyper-race

**Lane:** pitchfork-mise-modularization/paper-finder+pattern-borrow+hyper-race
**Date:** 2026-09-30 · **Worker:** Bram (Ember's crew)
**Parent stays:** `/home/toxic/sovereign/pitchfork.toml` — the parent entrypoint does not move.
Modularization changes how it is *produced*, never where it *lives*.

## TL;DR

**Winner: Design B — one manifest per daemon (`pitchfork.d/<name>.toml`), composed
in-place into the parent by `bin/pf`.** It won the hyper-race on every discriminating
metric, it is the shape the literature blesses (additive fragments, conflicts as
errors), and it borrows runsvdir's directory-of-services model + supervisord's
two-phase reload. The tool is built, tested against the real 82-daemon config, and
ready to ship: `pf migrate` (byte-identical split) → `pf build` (guarded atomic
compose) → `pf diff` (restart list).

## 1. Paper findings (Wren, with real citations)

10 papers + 5 verified doc pages. Full text in `research/phase1-papers.md`.

- **[1] Dolstra & Löh, "NixOS: A Purely Functional Linux Distribution," ICFP '08.**
  DOI `10.1145/1411204.1411255`. Generate system config from typed modules; conflicting
  definitions merge via per-option merge functions with explicit priorities. The formal
  precedent for generated-config designs — and the answer to "last-wins vs deep-merge":
  neither; typed merge with declared precedence.
- **[2] Dolstra, "The Purely Functional Software Deployment Model," PhD thesis,
  Utrecht 2006.** https://edolstra.github.io/pubs/phd-thesis.pdf — atomic upgrades,
  never mutate in place; a half-written supervisor config is the exact failure class
  this eliminates. Our composer writes tmp+rename, never patches live.
- **[3] Xu et al., "Hey, You Have Given Me Too Many Knobs!", FSE '15.**
  DOI `10.1145/2786805.2786852` — only 6.1–16.7% of config knobs are used; keep the
  manifest schema small with good defaults.
- **[4] Hicks & Nettles, "Dynamic Software Updating," TOPLAS 27(6).**
  https://mhicks.me/papers/HicksNettles03.html — updates at programmer-determined
  points with verifiable transitions. Our analog: diff old vs new per-daemon, restart
  only changed daemons.
- **[5] Armstrong, "Making Reliable Distributed Systems…", PhD thesis, KTH 2003.**
  https://erlang.org/download/armstrong_thesis_2003.pdf — Erlang/OTP supervision trees:
  per-component upgrade without tearing down the supervisor. The oldest production
  proof of the granularity we ship.
- **[6] Shapiro et al., "Conflict-free Replicated Data Types," INRIA RR-7687, 2011.**
  https://inria.hal.science/inria-00609399 — if fragments are *additive* (each file owns
  disjoint daemon-name keys), the composed config is a grow-only map: multi-writer
  edits converge by construction. **This is the formal justification for one-manifest-
  per-daemon with duplicate definitions as hard errors.**
- **[7] Mens, "A State-of-the-Art Survey on Software Merging," IEEE TSE 28(5), 2002.**
  DOI `10.1109/TSE.2002.1000449` — three-way merge needs a common ancestor; without
  ancestor tracking, prefer designs where conflicts are *structurally impossible*.
  Our `pitchfork.d/.hashes` is the ancestor record that makes hand-edit detection work.
- **[8] Kleppmann et al., "Local-First Software," Onward! 2019.**
  DOI `10.1145/3359591.3359737` — conflicts must be *surfaced*, never silently
  resolved. Our `pf explain <daemon>` is the config analog of their conflict UI.
- **[9] Semenov & Aksenov, "Semantic Conflict Model…", 2026.**
  https://arxiv.org/html/2602.19231 — newest in set; reinforces [8]: any same-key
  override must be explicit and inspectable, never magic.
- **[10] Xu et al., "Do Not Blame Users for Misconfigurations," SOSP '13** —
  ship validation in the same commit as the module system. Our `pf check`.

Verified docs: **[D1]** systemd.unit(5) drop-ins (ordered files, later wins);
**[D2]** `systemctl daemon-reload` (reload definitions globally, restart nothing
implicitly — the exact granularity `pf diff` + targeted restart implements);
**[D3]** supervisord `[include]` (reread + update two-phase); **[D4]** Docker Compose
merge (per-field strategy table; relative-path footgun warning); **[D5]** CUE value
lattice (conflicting values are *errors*, not silent wins — our duplicate rule).

**Paper verdict:** additive per-daemon fragments with conflicts-as-errors is the
best-supported shape ([6] + [D5] + [8]); generated configs must be atomic ([2]) and
validated ([10]); reload = diff + restart-only-changed ([4] + [D2]).

## 2. Pattern borrowing (Magpie, ranked)

Full text in `research/phase2-patterns.md`. Ranked by recency + relevance; every
mechanism read in its implementation.

1. **systemd drop-ins** — <https://github.com/systemd/systemd> (`conf-parser.c`,
   `config_parse_many_files()`): main file first, then `*.d/*.conf` in sorted order;
   atomic writes; no in-config locking. Borrowed: lexical order + atomic discipline.
2. **supervisord `[include]`** — <https://github.com/Supervisor/supervisor>
   (`options.py:582-611`): `files` = globs, sorted, later wins; `reread` (validate)
   + `update` (restart only changed) two-phase. Borrowed: the two-phase apply.
3. **docker compose multi-file merge** — <https://github.com/docker/compose>,
   <https://github.com/compose-spec/compose-go> (`override/merge.go`): per-path
   merge-strategy registry. Borrowed: the idea that merge rules must be explicit.
4. **k3s `config.yaml.d`** — <https://github.com/k3s-io/k3s>
   (`pkg/configfilearg/parser.go`): lexical `NN-name` precedence. Borrowed: naming.
5. **runsvdir directory-of-services** — <https://github.com/g-pape/runit>: one
   directory entry per service, no merging, no conflicts by construction; new entry
   = service starts. Borrowed: **the core of design B**.

Negative results (verified): overmind = single Procfile, no include; pm2 = single
ecosystem file, no include. Among supervisors, supervisord's `[include]` is the
exception — conf.d is a systemd/k3s idiom.

## 3. Pitchfork upstream / include verdict (Magpie, verified three ways)

- Upstream: <https://github.com/jdx/pitchfork>. Latest **v2.29.0** (2026-09-29);
  we run **2.25.0**.
- **No include / drop-in / conf.d / extends mechanism exists in any version through
  2.29.0.** Verified: (a) the 1595-line config reference contains zero occurrences
  of "include"/"drop-in"/"extends"; (b) CHANGELOG 2.25.0→2.29.0 adds nothing
  composition-shaped; (c) zero open/closed issues for include/conf.d/drop-in.
- What natively exists: a **directory-hierarchy** merge
  (`/etc/pitchfork/config.toml` → `~/.config/pitchfork/config.toml` →
  per-directory `.config/pitchfork.toml` → `pitchfork.local.toml`, later wins) —
  per-directory, not per-file. And 2.25.0+ **external config attachments**
  (`pitchfork config add [--dir] [--namespace] <FILE>`): generated files registered
  per project without copying — the natural sink for a generated config, though the
  supervisor's main `start` path merge semantics for attachments are unverified.
- Upgrading 2.25.0→2.29.0 changes none of this.
- **Conclusion: a conf.d mechanism must be built on top (compose before pitchfork
  reads). We built it: `bin/pf`.**

## 4. Hyper-race results

Three designs prototyped against the **real** `/home/toxic/sovereign/pitchfork.toml`
(995 lines, 82 daemons), raced on: compose latency (20 concurrent runs),
single-daemon change propagation, git merge conflicts (edit-edit + concurrent add),
rollback triage cost, and a validity gate (TOML parses — Bun.TOML **and** Python
tomllib — daemon set equal, every stanza identical). Raw JSON: `race-results.json`.

| Metric | MONO (baseline) | A (8 grouped drop-ins) | **B (82 manifests)** | C (19 project fragments) |
|---|---|---|---|---|
| M1 compose median / p95 (ms) | — | 104.8 / 247.0 | 125.7 / 318.7 | 111.2 / 287.1 |
| M2 single-daemon edit: recompose / changed lines / others identical | — | 94.9ms / 1 / ✓ | 119.5ms / 1 / ✓ | 62.1ms / 1 / ✓ |
| M3 edit-edit merge conflicts (far / adjacent) | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| **M3b concurrent ADD: conflict? (files/hunks)** | **yes (1/1)** | no (0/0) | **no (0/0)** | **yes (1/1)** |
| **M4 rollback of 1 bad daemon from a 6-daemon commit: stanzas in file / foreign / over-reverted good / cmds** | **6 / 5 / 5 / 7** | 3 / 2 / 2 / 4 | **1 / 0 / 0 / 2** | **1 / 0 / 0 / 2** |
| M5 validity (parses, 82 daemons, stanzas identical) | — | ✓ | ✓ | ✓ |

Reading the table:

- **M1/M2**: all designs compose in ~100–300ms; a single-daemon edit touches
  exactly 1 line and leaves all other daemons byte-identical. Composition cost is
  not the differentiator — anyone claiming "generation is slow" is wrong by 3
  orders of magnitude.
- **M3**: disjoint line-edits merge cleanly even in the monolith. The monolith's
  merge pain was never edit-edit — it was committed conflict markers (the flock
  incident) and add-add collisions.
- **M3b is the money metric**: the fleet's most common change is *adding* a daemon.
  Two writers appending to the monolith collide (1 file, 1 hunk). Design B never
  collides (new file per daemon). Design A avoids it (hash-distributed). Design C
  collides when the new daemon's project is unknown (both default to misc).
- **M4 is the rollback story**: reverting one bad daemon out of a mixed 6-daemon
  commit. Monolith: the file-level revert clobbers 5 good daemons (or 7 commands of
  hunk surgery). Design B: 2 commands, zero collateral.
- **All three designs produce byte-identical composed output** (validity gate) —
  the race measured source layout, not merge semantics, which is the honest
  comparison.

## 5. Recommended design and rationale

**Ship design B: `pitchfork.d/<name>.toml` — one manifest per daemon — composed
in-place into `/home/toxic/sovereign/pitchfork.toml` by `bin/pf`.**

Rationale, in order of weight:

1. **Rollback isolation (M4).** The only design where reverting one daemon's bad
   change is 2 commands with zero collateral. Chris: "a fallback is not a
   rollback" — B is the only design with a true per-daemon rollback.
2. **Add-add convergence (M3b + [6]).** New daemon = new file = no merge conflict
   by construction (the runsvdir property). The fleet adds daemons constantly.
3. **Conflicts as errors ([D5], [8], [9]).** Duplicate `[daemons.<name>]` across
   fragments is a hard error naming both files — never silent last-wins.
4. **Atomic, byte-stable generation ([2]).** tmp+rename; mtime preserved when
   bytes are unchanged (no spurious pitchfork reloads); first `pf build` after
   `pf migrate` is a verified no-op.
5. **Hand-edit guard ([7] ancestor tracking).** `pitchfork.d/.hashes` records the
   last-built state per daemon; a hand-edit to `pitchfork.toml` is detected and
   `pf build` aborts with the exact fix ("move it into pitchfork.d/<name>.toml")
   instead of clobbering it. This is the "stop bypassing" mechanism.
6. **Reload granularity ([D2], [4]).** `pf diff` attributes git hunks to daemons
   and prints the exact `bin/pitchfork-restart sovereign/<name>…` list. Editing a
   running daemon's stanza never re-registers it (pitchfork 2.25.0 behavior,
   confirmed in the config's own header) — the tool tells you what to restart.

Design A is a fine second choice (simpler file count) but retains co-location
collisions. Design C matches how Chris framed it ("per-project fragments composed
upward") and is the right *ownership* story, but the papers warn against layered
override debuggability ([D5]), and it needs a new-daemon project-assignment rule to
fix its M3b collision. **Recommendation: ship B now; add an optional
`pf build --group-by-project` view later if project ownership wants a physical
manifestation** (the fragments are per-daemon either way — grouping is a view).

## 6. What was built

`bin/pf` (Bun, ~600 lines) — the shipped tool:

- `pf migrate` — one-time split of `pitchfork.toml` → `pitchfork.d/*.toml`
  (82 manifests) + `pitchfork.d/.hashes`. Verifies the rebuild is byte-identical
  before reporting success.
- `pf build` — three-way compose (fragment / `.hashes` ancestor / current parent
  stanza) → in-place section rewrite preserving order, preamble bytes, and
  trailing-blank structure → atomic write → TOML validation → `.hashes` refresh →
  prints changed daemons + the exact restart command. `--force` lets fragments win.
- `pf diff` — git-hunk attribution → changed-daemon list → restart command.
- `pf check` — fragment validation (duplicates, TOML parse, parent/fragment set
  match) + drift reports. **Found live drift: `[groups.all]` lists 43 of 82
  daemons; 39 daemons are missing from it.**
- `pf explain <daemon>` — provenance + sync state per daemon (the [8] conflict UI).

Prototypes + harness that produced the measurements: `harness/compose.ts`,
`harness/split-fixtures.ts`, `harness/race.ts`, `proto-a/pf-merge.ts`,
`proto-b/pf-build.ts`, `proto-c/pf-collect.ts`. Research inputs:
`research/phase1-papers.md` (Wren), `research/phase2-patterns.md` (Magpie).

## 7. Migration plan (82 daemons)

The parent stays `/home/toxic/sovereign/pitchfork.toml`. Nothing moves.

1. **Land the tool** (this change): `bin/pf` + `RESULT.md` → `toxicwind/sovereign-projects`
   `main`. Zero effect on the running fleet: no fragments exist yet, `pf` is inert.
2. **Split (one-time, safe):** on yote, in `/home/toxic/sovereign`:
   `bin/pf migrate` → creates `pitchfork.d/` (82 manifests + `.hashes`).
   It self-verifies byte-identical rebuild; `pitchfork.toml` is untouched and every
   daemon keeps running.
3. **Verify:** `bin/pf build` → must report `changed:false`. `bin/pf check` → ok.
   `git status` → only new files under `pitchfork.d/`. Commit them.
4. **Cut over (per-daemon, reversible):** from here, all daemon edits go in
   `pitchfork.d/<name>.toml`; `pf build` regenerates the parent; `pf diff` gives
   the restart list. The 5 stopped daemons from the parent audit (`bidder-forge`,
   `bidder-scout`, `buildsrv`, `flicker`, `flicker-agent`) are the natural first
   candidates for fragment deletion once their retirement is confirmed.
5. **Fix the `groups.all` drift** (follow-up): regenerate `[groups.all]` from the
   fragment set (39 daemons are currently missing from it). `pf check` reports the
   drift continuously until fixed.
6. **Optional:** `pitchfork 2.25.0 → 2.29.0` upgrade (native behavior unchanged for
   our purposes — verified — so this is independent).

## 8. Rollback / fix-forward

- **Per-daemon rollback:** `git log -- pitchfork.d/<name>.toml` → `git revert`
  (2 commands, zero collateral — measured in M4). This is the design's core win.
- **Bad build:** `pf build` is atomic (tmp+rename) and mtime-preserving; a bad
  fragment edit produces a bad parent, but `git checkout HEAD -- pitchfork.toml
  pitchfork.d/<name>.toml` restores both, then `pf build` + targeted restart.
- **Hand-edit bypass:** `pf build` refuses and names the fix; `--force` is the
  explicit override (auditable in shell history).
- **Full retreat:** delete `pitchfork.d/` and keep editing `pitchfork.toml` as
  today — the parent file is never in a state `pf` can't reproduce, and every
  migration step is a normal git commit.
- **Fix-forward:** edit the fragment, `pf build`, `pf diff`, restart only the
  listed daemons. The blast radius of any change is exactly its daemon list.

## 9. Hot-reload semantics (verified, not assumed)

- pitchfork 2.25.0 notices **new/deleted** daemons via mtime (observed: a new
  daemon was picked up within ~1 min, no restart). `pf build` preserves mtime when
  bytes are unchanged → no spurious reloads.
- **Editing a running daemon's stanza does NOT re-register it** (config header,
  2026-09-20 incident note). After any daemon edit: `pf diff` → 
...[truncated 1453 chars]