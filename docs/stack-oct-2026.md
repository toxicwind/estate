# Estate Stack — decision for October 2026

Authoritative stack-layer decision for the estate as of late Oct 2026. Every
layer was researched for its **mass replacement** (not incremental tweaks) and
the four stack planes are treated TOGETHER here — they must compose into one
stack, not four competing picks.

## Stack map

| Layer    | Current (2026-10-22)                      | Oct-2026 replacement candidate                                      | Verdict                                                                                      |
| -------- | ----------------------------------------- | ------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Registry | `.meta.yaml` peers + `pens` pointer repo  | **moon v2 `projects` manifest** (peer registry + `dependsOn` edges) | ✓ keep a dedicated registry, decoupled from build graph                                      |
| VCS      | git (default) + jj (tau/ranch/doorbell)   | **jj colocated over git** (not a replacement)                       | ✓ `jj git init --colocate`; git stays interop/push                                           |
| Runtime  | mise + bun                                | **proto/mise** (bun is a participant, not a resolver)               | ✓ proto if moon-standard, else mise; uv if Python-dominant                                   |
| Build/CI | moon (partial) + forge (REAPI/woodpecker) | **Bazel (bzlmod) + Nativelink/REAPI**; moon only for JS-heavy       | ✓ Bazel-class durable polyglot; moon NOT an interop REAPI client (Jul-2026 ActionResult bug) |
| Deploy   | pitchfork (woodpecker-CI)                 | **pitchfork (woodpecker fork) + systemd**                           | ✓ over k8s/OKD/nixos-rebuild for single-operator                                             |

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

## 3. Runtime / toolchains — DECIDED

**Verdict: proto or mise is the polyglot resolver; bun is a participant, not a
resolver.** moon v2.6's toolchain is built around **proto** (moon's own
multi-language version manager, `~/.proto`); moon is a **Rust** binary that
manages node/bun/deno/python/rust via proto (not "bun-native"). bun (96k★)
cannot resolve Python/Rust toolchains. Repo sort: mise 35.3k★, uv 91k★, pixi
7.9k★, proto 1.4k★. **Recommendation:** proto if we standardize on moon, else
mise for everything; uv only if Python dominates. No single tool has won the
polyglot resolver slot.

## 4. Build / CI — DECIDED

**Verdict: stay on Bazel-class (bzlmod) + Nativelink/REAPI; moon is NOT the
replacement and is NOT an interop REAPI client.** Sourcegraph May-2026: polyglot
heavyweights = Bazel/Buck2/Pants; JS-only = Turborepo/Nx; moon is not a polyglot
contender (4.2k★ vs Bazel 26k★). The REAPI trend is real but is the _Bazel/Buck_
layer: Nativelink scopes itself to Bazel/Buck clients. moon's REAPI support is
**broken** — July-2026 closed bug: moon's HTTP remote-cache body is no longer a
Bazel ActionResult and gets 400-rejected by validating bazel-remote. So
"moon + nativelink" is aspirational + currently **incompatible**. For 169
polyglot repos: **stay Bazel (bzlmod) + Nativelink/REAPI**; adopt moon only for a
JS/TS-majority subset where the polyglot graph cost isn't justified.

## 5. Deploy — DECIDED

**Verdict: pitchfork (our woodpecker fork) + systemd**, over k8s/OKD (operator
heavy) and nixos-rebuild (steep); woodpecker v3.19.0 is active (Oct-2026) with
CLI/API/fan-out. flox/tilt fill niche dev-loop roles. Single-operator self-hosted
estates standardize on a woodpecker-class runner + systemd units.

---

## 6. The combined STACK (all four planes together)

The four planes compose coherently — this is the estate's Oct-2026 stack:

```
registry  moon .moon/workspace.yml (projects = peers)  ← peer registry, decoupled
vcs       jj colocated (--colocate) over git             ← history/parallel agents
runtime   proto OR mise per-repo (bun as a tool, not resolver)
build     Bazel (bzlmod) + Nativelink/REAPI (:25155 forge)  ← durable polyglot
deploy    pitchfork (woodpecker fork) + systemd          ← single-operator lanes
```

Key reconciliations:

- **Registry vs Build**: moon `projects` can be the _peer registry_ even though
  Bazel owns _build execution_ — the registry stays decoupled from the build
  graph (that's the point). If builds dominate, the registry can instead BE a
  Bazel(MODULE.bazel) workspace; we keep `.meta.yaml`-style peers in moon for the
  listing, Bazel for the graph.
- **moon ≠ a REAPI client**: do NOT point moon at nativelink; Bazel/Buck2 are the
  REAPI clients. moon stays a JS-heavy build only, with native toolchains.
- **jj + moon + Bazel**: moon's graph is file-based (not commit-based), jj owns
  history, Bazel owns the content-addressed build cache — no VCS coupling.

This is the target stack to converge toward as-of Oct-2026; it is the answer to
"what is our STACK", with each layer given its real mass-replacement verdict.
