# Estate Stack — decision for October 2026

Authoritative stack-layer decision for the estate as of late Oct 2026. Every
layer was researched for its **mass replacement** (not incremental tweaks) and
the four stack planes are treated TOGETHER here — they must compose into one
stack, not four competing picks.

## Stack map

| Layer    | Current (2026-10-22)                      | Oct-2026 replacement candidate                                      | Verdict                                                 |
| -------- | ----------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------- |
| Registry | `.meta.yaml` peers + `pens` pointer repo  | **moon v2 `projects` manifest** (peer registry + `dependsOn` edges) | ✓ keep a dedicated registry, decoupled from build graph |
| VCS      | git (default) + jj (tau/ranch/doorbell)   | jj (Jujutsu) colocated/peers                                        | _(research pending)_                                    |
| Runtime  | mise + bun                                | _(research pending)_                                                | —                                                       |
| Build/CI | moon (partial) + forge (REAPI/woodpecker) | _(research pending)_                                                | —                                                       |
| Deploy   | pitchfork (woodpecker-CI)                 | _(research pending)_                                                | —                                                       |

---

## 1. Registry / whole-repo abstraction — DECIDED

**Verdict: keep a dedicated registry manifest decoupled from the build graph.**

- The 2026 mass-replacement of git-submodules is **moon v2's `projects` manifest
  (`.moon/workspace.yml`)**, NOT Bazel/Buck2/Pants.
- moon's `projects` accepts an explicit **map** (`admin: 'apps/admin'`) AND
  **globs** (`'crates/*/Cargo.toml'`) — a 1:1 upgrade of `.meta.yaml`, plus
  `extends:` for remote/peer inheritance (multi-repo peers without submodules).
- It decouples **registration** (the peer map) from **execution** (tasks wrap
  native toolchains) — so you never must re-author your whole graph in a build DSL.
- Bazel `bzlmod` / Buck2 external cells are **build-language registries** — wrong
  tool to merely list 169 peer repos.
- **Composes with the other layers:**
  - With jj-history: moon's `vcs.client` is git-only today, but moon's graph is
    **file-based not commit-based** — peer edges live in the moon manifest while
    jj owns history. Clean split.
  - With REAPI/forge: moon `remote.cache` speaks **REAPI gRPC**, so it sits
    beside nativelink (`:25100`) as a **scheduler over the REAPI cache** rather
    than replacing it.

**Migration:** `.meta.yaml` → moon `projects` map verbatim; add one `moon.yml`
per peer with `dependsOn`; leave task execution to existing toolchains.

---

## 2. VCS / history — DECIDED

**Verdict: jj (Jujutsu) is the coherent-layer winner, but NOT a 1.0 replacement —
adopt it COLOCATED on top of git, not in place of it.** jj v0.46.0 (2026-10-07,
~32.2k★) wins on the agent use-case (parallel `jj workspace add`, stable change
IDs that survive rebase, conflicts-as-commit-state), but opencode/claude-code
are git-first as of Oct-2026. Migration = `jj git init --colocate` (`.jj` beside
`.git`, gitoxide backend, change-ID header pins) per component; git stays the
interop/push layer. For 169 components this replaces the submodule graph with
bookmark-driven composition + rewrite-proof change-ID pins. Composes with moon
(file-based graph) and REAPI (content-addressed caches). Full section appended.

---
