# Pens vs no-submodule multi-repo prior art (2026-10-29)

Search basis: npm registry, `-/v1/search`, three queries. Relevant hits:
`@microsoft/rush` (5.181.0, 2026-10-06), `@moonrepo/cli` (2.6.4, 2026-10-23),
`meta-git` (mateodelnorte, 2021). Everything else in results was noise.

## The tools that are actually "no submodule, many peer repos"

| Tool                                           | Model                         | Registry                    | Submodule | Placement               | Cross-repo task |
| ---------------------------------------------- | ----------------------------- | --------------------------- | --------- | ----------------------- | --------------- |
| **meta / meta-git** (mateodelnorte, dead 2021) | thin coord + sibling clones   | hand `.meta` file           | never     | flat                    | `meta exec`     |
| **Google AOSP repo**                           | manifest.xml + many checkouts | manifest                    | no        | path in manifest        | `repo forall`   |
| **@moonrepo/cli** (active)                     | project.graph + workspaces    | generated                   | no        | project-groups          | `moon run`      |
| **@microsoft/rush** (active)                   | packages/ inside ONE repo     | package.json                | no        | none (monorepo)         | `rushx`         |
| **pens (ours)**                                | thin coord + peer clones      | **generated** manifest.yaml | never     | **theme-by-name → pen** | — (gap)         |

## Why pens is the converged answer, not an also-ran

1. **Generated manifest, not hand registry.** meta died precisely because its
   `.meta` was hand-maintained and drifted (our own manifest was hand-built and
   drifted to 26 FAILs → we regenerated it the same way moonrepo does).
2. **Theme-as-placement.** No prior-art tool ties a repo's _home_ to its _name
   universe_. Our rule (Greek→olympus, mineral→geode, farm/ops→barn,
   herding→ranch, control-plane→estate) gives deterministic placement that
   checkout history can't corrupt.
3. **`~/.local/bin` symlink surface + FAIL-on-drift verify.** bin-verify.sh
   treats a broken link as FAIL — a stronger guarantee than any of these ship.
4. **Kitchen-sink `*` gitignore + submoduleless.** Same "no gitlinks, ever"
   doctrine as AOSP/meta, but with the parent repo staying textually clean.

## The one real gap: cross-repo task execution

Everyone else has `meta exec` / `moon run` / `repo forall`. Pens lacks a single
entrypoint to run one command across all products of a pen (or all pens).
That is the single capability worth borrowing. Everything else is already
superior in pens.

## Verdict

Do NOT adopt an external tool. Adopt moonrepo's _pattern_ of a generated
project-graph + cross-repo runner and encode it as `pens/<pen>/bin/exec.ts`
(native Bun). Keeps the theme placement + manifest verify that already make
pens stronger than any prior art.
