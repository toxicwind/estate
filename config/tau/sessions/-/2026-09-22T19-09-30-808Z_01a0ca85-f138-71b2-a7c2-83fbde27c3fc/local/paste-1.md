AUTONOMOUS PLAN — range/ranch reconstitution.

Working directory: ~/sovereign/projects/range/
(Currently ~/sovereign/projects/mesh/ — renamed in phase 4.)

Execute end to end. Do not stop after any phase. Do not produce a
summary. Do not treat any checkpoint as completion. After phase 9,
loop phase 9 until a full pass produces no new findings. Report one
line per phase transition:
  [phase N] <one sentence what just changed>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HARD FACTS — stated by the user, do not re-derive
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

herd == llama-swap == sovereign-swap. One codebase. Three names.
Canonical: herd. Retired aliases eliminated from every path, symlink,
service name, task name. Binary may keep the filename llama-swap only
if an external consumer requires that exact filename (check the
Makefile, deploy scripts, systemd units, /proc/<pid>/cmdline). If
nothing external requires it, rename the binary to herd.

Merging divergent copies of herd/llama-swap/sovereign-swap into one is
a MAIN merge. Full rigor: per-file, by hand, MERGE-DECISIONS.md, no
-X, no --theirs, no --ours, no union, no conflict markers.

mesh == range. mesh is the outer federation. Renamed to range in phase
4. Path changes from ~/sovereign/projects/mesh/ to
~/sovereign/projects/range/.

ranch is a monorepo inside range: holds the UI for everything plus
backend components.

Children of ranch after this plan's renames:
  stockyard/   (was routers/) — sorts/dispatches model traffic
  barn/        (was mcp/) — compartment for every tool, ours + bought
  corral/      role from code
  paddock/     role from code
  ui/          UI for everything

Children of stockyard: herd (router), flock (free-pool provider).
Child of barn: shep.
Sibling of ranch under range: squawk.

super-ralph is NOT ranch. Read code to determine what it actually is.

Folder renames:
  mesh    → range
  routers → stockyard
  mcp     → barn

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOOLSET — USE THESE, DO NOT INVENT WORKAROUNDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Every phase below names the tools to use. If a tool is missing,
install it before the phase runs. If install fails, use the listed
fallback. Never write a bash loop that forks a tool once per item when
a listed tool does the whole job.

SEARCH AND READ
  ffs               file search + read. Replaces find/grep/cat for
                    agent use. `ffs find`, `ffs grep`, `ffs read`,
                    `ffs map`, `ffs refs`. Used in phases 1, 2, 6, 7, 9.
  fd                fast find. Bounded scans. Used in phases 1, 7, 9.
  rg (ripgrep)      content search. Used in phases 6, 9 for retired-name
                    sweeps.
  ast-grep          AST structural search. Binary is `ast-grep`, not `sg`.
                    Used in phase 2 for import-graph extraction and in
                    phase 9 for stale doc-comment detection.
  tilth             tree-sitter code reader. Used in phase 2 to extract
                    entrypoints, exports, imports per language.
  bat               file preview with syntax highlighting. Used in
                    phase 3 when reading :1:/:2:/:3: blobs.

SEMANTIC UNDERSTANDING
  semble            local semantic code search. Used in phase 2 to find
                    related code across components.
  sia-code          hybrid semantic search. Used in phase 2 fallback.
  cocosearch        semantic search CLI + MCP. Used in phase 9 to find
                    stale references not caught by rg.

GIT
  git-snitch        multi-repo scan and comparative reports. Used in
                    phase 1 for the initial inventory across every
                    nested repo.
  git-scout         multi-repo management. Used in phase 1 and 9.
  gitgalaxy         risk scores + architecture map. Used in phase 2 to
                    corroborate the dependency graph.
  gitundo           safety-net snapshots. Install and enable BEFORE
                    phase 3 so reset --hard and clean -fdx are
                    recoverable. Used in phases 3, 4, 5, 9.
  easegit-cli       auto checkpoints before dangerous ops. Enable in
                    phase 3.
  gitpanic/git-panic  interactive recovery. Used in phase 9 if a merge
                    goes wrong.
  gitfix            broken-git-state recovery. Phase 9 fallback.

MERGE
  reconcile-ai      AI-assisted conflict resolution. Use ONLY as a
                    first-pass suggester — the merged file is still
                    written by hand after reading :1:/:2:/:3:. Never
                    accept its output unread. Phase 3.
  pygitwise         local/cloud merge assist, privacy-first. Phase 3
                    fallback if reconcile-ai fails to install.
  gitwand-mcp       MCP merge server. Phase 3 fallback.

CONFIG AND ENV
  direnv            per-directory env. Do NOT use for the retired-name
                    sweep.
  jq / yq           JSON and YAML edits. Used in phase 6 when editing
                    pitchfork.toml-adjacent configs (json) and yaml.
  sd                sed replacement done safely. Phase 6 for mechanical
                    string replacement after the mapping is decided.
  miller (mlr)      CSV/table manipulation. Phase 1 if inventory is
                    tabulated.

RUNNING SYSTEM
  systemctl --user  service state, unit files. Phases 6, 8, 9.
  ss                listening ports. Phases 1, 8, 9.
  procs / bottom    process inspection. Phases 1, 8, 9.
  lsof              open files per process. Phase 9 for stale cwd
                    detection.
  pueue             task queue. Optional — use to serialize long
                    build/test steps in phase 8 if the box is busy.

DOCS
  tldr              quick reference for any tool above. Use before
                    guessing flags.

If any tool above is missing, install via the appropriate manager
(pacman, paru, cargo, go, pipx, uv, npm, bun). Record what installed
and what didn't in MERGE-DECISIONS.md. Never skip a phase because a
tool is missing — use the fallback.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCOPE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Everything under ~/sovereign/projects/mesh/ (soon range/) is in scope.
Also: any path elsewhere under ~/sovereign or ~/projects that references
a component inside mesh/range, or holds a duplicate. References in
~/.config/systemd/user/, ~/.config/environment.d/, ~/.local/bin/,
~/sovereign/pitchfork.toml, ~/sovereign/mise.toml,
~/sovereign/stack/services/*.sh, ~/sovereign/.gitmodules, and
~/sovereign/config/* are in scope.

Out of scope: ~/.bashrc. OS-managed symlinks under
/usr/lib/systemd/user/*.wants. Git internals under .git/.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 1 — INVENTORY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tools: git-snitch, git-scout, fd, ffs, miller (if tabulating).

cd ~/sovereign/projects/mesh/

Bounded scans only. Never glob ~/sovereign root.

  fd -t d -H . ~/sovereign/projects/mesh/ --max-depth 5
  fd -t d -H 'super-ralph|corral|paddock|shep|flock|herd|llama-swap|sovereign-swap' ~/sovereign ~/projects
  fd -t l -H . ~/sovereign/projects/mesh/ ~/sovereign ~/projects
  cat ~/sovereign/.gitmodules
  git-snitch scan ~/sovereign/projects/mesh/    # if installed

For every candidate, record:
  module identity
    go     grep '^module ' go.mod
    node   jq -r .name package.json
    rust   grep '^name = ' Cargo.toml
    py     grep '^name = ' pyproject.toml
    none   "no manifest"
  real path       readlink -f
  inode           stat -c %i
  HEAD            git rev-parse --short HEAD
  last commit     git log -1 --format=%ci
  remote          git remote get-url origin
  dirty count     git status --short | wc -l
  live?           pgrep -af <basename>; readlink -f /proc/<pid>/exe

Group by module identity. Same identity = same codebase. Confirm
herd/llama-swap/sovereign-swap share a module identity. If a copy
exists whose module identity differs, it is unrelated and does not
merge.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 2 — CLASSIFY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tools: ast-grep, tilth, semble, sia-code, gitgalaxy.

For each entry, exactly one label:
  monorepo            | child-component | retired-alias
  duplicate-checkout  | container-wrapper | symlink | unknown

For each component, answer from code:
  entrypoint      main.go / index.ts / server.go — use tilth
  exposes         HTTP routes / CLI verbs / MCP tools — use tilth
  depends-on      from go.mod / package.json / imports — ast-grep
  depended-on-by  rg its module path across siblings — ast-grep
  live            running process, config reference

ast-grep recipes:
  # Go entrypoints
  ast-grep run -p 'func main() { $$$ }' -l go
  # Go import graph for a module
  ast-grep run -p 'import "$$$"' -l go
  # TS entrypoints
  ast-grep run -p 'export function $$$($$$) { $$$ }' -l ts

tilth recipes:
  tilth outline <file>     # functions, types, exports
  tilth imports <file>     # import list
  tilth tree <dir>         # file tree with structural summary

Special reads:

  corral/       read go.mod, main.go, README. Distinct subsystem,
                duplicate of herd, duplicate of super-ralph, or
                something else? Name from code.

  paddock/      same treatment.

  super-ralph   find every copy. Read go.mod, main.go, README.
                Determine what it actually is. If it is an old name
                for an existing component, merge. If distinct, place
                it. Do not assume.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 3 — MERGE DUPLICATES BEFORE MOVING ANYTHING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tools: gitundo, easegit-cli, bat, reconcile-ai (suggester only),
pygitwise (fallback), gitwand-mcp (fallback).

Install and enable gitundo + easegit-cli BEFORE the first merge so any
reset is recoverable. Confirm with `gitundo status`.

For every module-identity group with 2+ members:

  1. git update-ref refs/recovery/pre-merge HEAD on every side.
  2. base = merge-base of the pair. If merge-base fails, unrelated — do
     not merge. Note, move on.
  3. Survivor: metaphor fit > most recent commit > live process >
     clean tree.
  4. git -C <survivor> worktree add --detach \
       ~/.recovery-worktrees/merge-<name> <older-HEAD>
     cd ~/.recovery-worktrees/merge-<name>
     git merge --no-commit --no-ff <newer-HEAD>
  5. For every conflicted file:
       git show :1:<file> > /tmp/base
       git show :2:<file> > /tmp/ours
       git show :3:<file> > /tmp/theirs
     Read all three with bat. Optionally ask reconcile-ai for a
     suggested resolution — then READ it against the three inputs and
     write the file that should exist. Never accept tool output unread.

     take-a      the other side was superseded, broken, or redundant
     take-b      this side was superseded, broken, or redundant
     merge       both sides added independent code; combine by hand
     hand-write  both sides edited the same logic; write the correct
                 version. Do not concatenate. Do not blend.

     Forbidden: -X ours, -X theirs, --ours, --theirs, --union,
     git merge-file, conflict markers in output.

  6. MERGE-DECISIONS.md at survivor root, one entry per non-trivial
     file: path / ours / theirs / decision / reason.
  7. Commit. Fast-forward survivor.
  8. Every loser:
       tar czf ~/.recovery-archive/<ts>/<basename>.tar.gz <loser>/
       rm -rf <loser>
       rg the tree for the loser path; update every hit to survivor.
       Symlinks pointing at the loser: delete after updating callers.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 4 — RENAME FOLDERS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tools: git mv, gitundo.

  git mv ~/sovereign/projects/mesh                ~/sovereign/projects/range
  git mv ~/sovereign/projects/range/ranch/routers ~/sovereign/projects/range/ranch/stockyard
  git mv ~/sovereign/projects/range/ranch/mcp     ~/sovereign/projects/range/ranch/barn

Reason for MERGE-DECISIONS.md:
  mesh names a network topology; range names the open territory where
  the operation lives. routers names the mechanism; stockyard names
  the role. mcp names the protocol; barn names the compartment.

Update .gitmodules and every config that references the old paths.
Note for phase 7: any symlink whose target was under mesh/ now
dangles. Repoint or remove.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 5 — MOVE CHILDREN INTO THEIR MONOREPOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tools: git mv, gitundo.

For every child-component whose parent is a monorepo:
  git mv inside the containing repo. Update .gitmodules.
  Update every config referencing the old path.

For every retired-alias still in a path:
  git mv to canonical, or archive if canonical module identity already
  exists.

Rename retired binary filenames only if nothing external depends on
the old name.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 6 — CONFIG REWRITE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tools: rg, sd, jq, yq, ffs grep.

Update every reference in:
  ~/sovereign/pitchfork.toml
  ~/sovereign/mise.toml
  ~/sovereign/stack/services/*.sh
  ~/sovereign/config/*
  ~/sovereign/.gitmodules
  ~/.config/systemd/user/*.service  *.path  *.socket
  ~/.config/environment.d/*
  ~/.local/bin/* launchers
  ~/.bashrc.env (symlink into tracked file — commit if edited)
  ~/.agent/*

Never edit ~/.bashrc.

For each retired string, rg across ~/sovereign, ~/projects, ~/.config,
~/.local/bin, ~/.agent:
  super-ralph
  llama-swap (as path or service name, not argv[0])
  sovereign-swap
  /mesh/
  ranch/routers
  ranch/mcp

Zero hits, or the remaining hit has an inline comment on the same line:
"# required by <external thing>, do not rename".

Use sd for mechanical replacements after the mapping is decided. Never
sd blindly — read every file first, then replace.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 7 — SYMLINK PURGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tools: fd, readlink, rg.

  fd -t l -H . ~/sovereign ~/projects

For each symlink:
  readlink -f it.
  If target is canonical and survives: rg the symlink path across
  ~/sovereign, ~/projects, ~/.config, ~/.local/bin. If nothing
  references it, delete. If something references it, update the
  reference to the canonical path directly, then delete.
  If target is archived: delete, update callers to survivor.
  Loop until fd -t l shows zero under ~/sovereign and ~/projects.

After mesh → range, symlinks pointing at mesh/ dangle. Repoint or
remove in this phase.

Exception: OS-managed symlinks under /usr/lib/systemd/user/*.wants.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 8 — BUILD, RUN, VERIFY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tools: go, cargo, bun, uv, curl, jq, systemctl, ss, procs, mise,
pueue (to serialize long steps if needed).

For every Go module touched:
  go build ./... && go test ./... && go vet ./...
For every other language module: its equivalent.

  ./<router-binary> --validate -config ~/sovereign/config/herd.yaml
  mise -C ~/sovereign run restart-herd
  curl -sf http://127.0.0.1:25100/health
  curl -sf http://127.0.0.1:25100/v1/models | jq '.data | length'

Assertions all zero:
  fd -t l -H . ~/sovereign ~/projects | wc -l
  rg -c 'super-ralph|llama-swap|sovereign-swap' ~/sovereign ~/projects 2>/dev/null | wc -l
  rg -c '/mesh/' ~/sovereign ~/projects 2>/dev/null | wc -l
  rg -c '^<<<<<<<|^=======|^>>>>>>>' ~/sovereign ~/projects 2>/dev/null | wc -l

If any assertion fails, fix and re-run.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 9 — CONTINUE IMPROVING UNTIL STABLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tools: git-scout, git-snitch, cocosearch, ast-grep, lsof, procs,
git fsck, gitpanic if needed, gitfix if needed.

Do not stop after phase 8. Run phases 1 through 8 again. Find what you
missed:

  configs referencing paths that moved
  services whose cwd no longer exists (lsof / procs / readlink
    /proc/<pid>/cwd)
  READMEs describing the old layout
  git remotes named with retired labels
  git submodule entries pointing at stale SHAs
  systemd units with dead WorkingDirectory
  launchers with hardcoded old paths
  doc comments in code naming retired folders (ast-grep)
  symlinks that reappeared
  duplicate checkouts that re-materialized
  references only findable by semantic search but not rg
    (cocosearch, semble)

Fix them. Loop until a full pass produces no new findings.

Check the running system: systemctl --user list-units, ss -tlnp,
pgrep -af, lsof for stale cwd. Anything referencing a path that no
longer exists is a finding. Fix. Loop.

Check git state in every repo under ~/sovereign/projects/range/:
git status --short, git log -1 --format='%ci %s',
git fsck --unreachable --no-reflogs. Reconcile orphaned commits by
pinning them as refs/recovery/orphan-<short>. Update
MERGE-DECISIONS.md.

If a git operation goes sideways, use gitpanic or git-panic to diagnose
before anything destructive. If the repo is broken at the object level,
gitfix.

Keep looping phase 9 until nothing new appears. When the tree, the
running system, and the git state all agree with the plan, the task
is done. Until then, keep going.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Use the tools listed in each phase. Do not invent bash loops that fork
a tool once per item when the tool does the whole job.

Read before naming. The code is truth; directory names are not.
Merge duplicates before moving anything.
No mechanical conflict resolution. Every file decided by reading.
No symlinks at the end. Every config path resolves without a hop.
No retired names left in paths or configs.
No conflict markers in committed files.
No progress reports beyond the one-line-per-phase format.
No asking which name is correct — read the code, decide, do it.
Never reset --hard. Never clean -fdx. Never rm -rf without archiving.
Never edit ~/.bashrc.

Begin with phase 1. Do not stop.