# Estate conventions

> The rules the awrawr-pc estate actually follows. Written 2026-10-02 while the
> `sovereign → estate` restructure was landing. Every rule here was paid for
> with a real breakage; when one of them stops being true, delete the rule
> rather than leaving a lie in the docs.
>
> Companion: [`AGENTS.md`](../AGENTS.md) (standing directives),
> [`fleet-knowledgebase.md`](fleet-knowledgebase.md) (who owns what),
> [`estate-map.md`](estate-map.md) (generated topology — never hand-edit).

---

## 1. Where things live

```
/home/toxic/
├── estate/                  # control plane. Git repo: toxicwind/sovereign-projects
│   ├── ranch/               # project monorepo. Git repo: toxicwind/ranch
│   ├── vendored/            # third-party checkouts, own remotes, never indexed
│   ├── var/                 # runtime: archives, reconciliation, legacy, scratch
│   ├── manor/               # ranch-dashboard UI
│   ├── skills/              # canonical skills home (72 skills)
│   ├── config/              # SSOT config incl. ports.env
│   ├── ops/                 # control-plane tooling (gitignore-sync, audits)
│   ├── docs/                # this file, estate-map, knowledgebase
│   ├── hatch/               # agent workspaces. DOES NOT MOVE.
│   └── engines/ buildsrv/ forensics-srv/ grafana/ keypool/ assets/
├── projects -> estate/ranch # compat symlink
├── ranch    -> estate/ranch # compat symlink
└── sovereign -> estate      # compat symlink
```

**Rule 1.1 — Anything with its own git history gets its own tier.**
`ranch/` for our projects, `vendored/` for upstream. Never vendored source inside
`ranch/`, never our source inside `vendored/`.

**Rule 1.2 — `hatch/` does not move.** Agents assume these paths. Leave it.

**Rule 1.3 — Compat symlinks are load-bearing.** `/home/toxic/projects`,
`/home/toxic/ranch`, `/home/toxic/sovereign` resolve into the estate. Configs
still spell the old paths. Do not delete one without grepping for its uses.

**Rule 1.4 — Runtime state never sits at a tier root.** It goes in `var/`
(`var/runtime`, `var/archives`, `var/legacy`, `var/archive`, `var/reconciliation`).

## 2. Path resolution — never hardcode

```python
# Python skills
import sys; sys.path.insert(0, str(SKILLS_HOME / "lib"))
from estate_paths import ESTATE, RANCH, PORTS_ENV, KNOWLEDGEBASE
```

```bash
# shell skills
. "$SKILLS_HOME/lib/estate.sh"      # exports ESTATE RANCH VENDORED MANOR TAU PORTS_ENV
```

Both resolve in this order: **environment override → discovery from the script's
own location → `$HOME` default.** Every path comes back `resolve()`d, so a compat
symlink never leaks into a report or a string comparison.

**Rule 2.1 — No skill hardcodes an estate path.** If you catch
`/home/toxic/sovereign/...` or `~/workspace/skills/...` in a script, that is a bug.
The skills home moved to `estate/skills` on 2026-10-02; `~/workspace/skills` and
`~/.tau/skills` are symlinks to it.

**Rule 2.2 — Override names are fixed:** `ESTATE_HOME`, `RANCH_HOME`,
`VENDORED_HOME`, `MANOR_HOME`, `VAR_HOME`, `SKILLS_HOME`, `TAU_HOME`.

## 3. Shell configuration

`$HOME/.bashrc` is a **symlink** to `estate/ranch/shell/ii/dots/.bashrc`. Edit the
dots copy, never the home copy — that duplication is what let the two drift
(a dead `pitchfork-quiet` alias in one, a `starship init` in the other).

Machine-local fragments stay real files and are sourced by the shared file:

| File | Owns |
|---|---|
| `.bashrc` (symlink → dots) | everything shared |
| `$HOME/.bashrc.env` | universal env tier, loaded first |
| `$HOME/.bashrc.local` | machine-local overrides, loaded last |

**Rule 3.1 — `.bashrc` returns early when non-interactive.** Anything that must
run for tooling sources `lib/estate.sh` directly instead of relying on `.bashrc`.

## 4. XDG configuration

`~/.config` is a **symlink** to `estate/ranch/shell/ii/dots/.config`. The estate
owns the whole XDG tree; `dots` is its checkout. Declarative config is tracked
there; app state is gitignored.

> ⚠️ **Known debt.** `dots/.config` holds app state that should be ignored —
> `gcloud/` (104 MB), `mozilla-backup*`, `google-chrome-for-testing/`,
> `mcp-build-cache/`, libaccounts-glib databases, `systemd/user` run state.
> Until a `.gitignore` lands inside `dots/.config`, those land in the repo.

**Rule 4.1 — Move with `rsync -a --remove-source-files`, never `mv $(ls)`.**
Unquoted `$(ls)` word-splits and destroys names with spaces (`Code - Insiders`).
This actually happened.

**Rule 4.2 — Archive before adopting.** When merging a directory into dots,
move colliding files to `var/legacy/<what>-pre-adoption/` first.

## 5. Environment loading

**One loader: mise.** `estate/mise.toml` is the root config.

**Rule 5.1 — Ports come from `config/ports.env` and nowhere else.** It is
injected with `_.file`, and the path must resolve regardless of CWD.

**Rule 5.2 — `estate/.env` is tracked; `.env.local` is not.** `.env` is the
runtime config SSOT (identity, stream tuning, model names). Secrets live in
`.secrets` / `$HOME/.secrets`.

> ⚠️ **Known conflicts.** `.env` sets `SCOUT_BASE_URL=…:25104/v1` while
> `mise.toml` sets `:25100/v1`. `.env` §8 re-declares ports that `ports.env`
> owns. `estate/.envrc` still exports `SOVEREIGN_HOME=/home/toxic/sovereign`.
> `skills/git-mutator/types.ts` still points `SOVEREIGN_PORT_SSOT` at
> `sovereign/config/ports.env`. All four need resolution during the mise rebuild.

**Rule 5.3 — direnv is a bridge, not a source of truth.** `.envrc` activates mise
and loads `$HOME/.secrets`. It never carries config of its own.

## 6. Process supervision

Pitchfork. `estate/pitchfork.toml` is the daemon registry; `pitchfork.d/` holds
per-project overlays.

**Rule 6.1 — A daemon's `dir` and `run` must resolve inside the estate.**
Relative `dir` resolves against the estate root; `run` must not reference a path
that does not exist. Audit both before committing a pitchfork change.

**Rule 6.2 — No competing supervisors.** Never a systemd unit for something
pitchfork owns, and vice versa.

## 7. Virtual environments

**Rule 7.1 — A venv lives at `<project>/.venv`,** is gitignored, and is the only
venv for that project. No venv at the estate root. No venv in `$HOME`.

> ⚠️ **Open.** `$HOME` still holds ~7.1 GB of strays (`.venv-guidellm` 6.1 GB,
> `.awrawr-mcp-venv`, `.gemini-sdk-venv`, `.whatsapp-mcp-venv`, `.venv-ralph`,
> `ralph-venv`, `hft-venv`, `venvs/`). Inside the estate, twelve venvs use
> inconsistent names (`venv`, `e2e-venv`, `.venv`).
> `forensics-srv/venv/bin/pip` has a shebang pointing at the pre-restructure
> path and is broken.

**Rule 7.2 — Moving a venv is a recreate, not a rename.** `pyvenv.cfg` and every
`bin/*` shebang hardcode the absolute path.

## 8. Repositories and reconciliation

When the same project exists twice — a monorepo dir and a standalone repo with
real history — **`merge-base` is usually `NONE`.** There is no merge. It is
content-level reconciliation:

1. Bidirectional `rsync -ani --delete` to see what each side uniquely holds.
2. Copy the estate-only files into `var/reconciliation/<name>/` with a
   `.lost-files.list` manifest.
3. Make the real repo canonical.
4. Leave `var/reconciliation/` in place — it is the answer to "where did that go".

**Rule 8.1 — Track what you diff with, not what you assume.**
`rsync -ani` output is `>f+++++++++ path` — the path is field **2**, parsed with
`awk '{print $2}'`. A regex that silently matches nothing loses data with no
error. Verify the extracted count against the earlier count.

**Rule 8.2 — Verified content, not git-trackedness.** Whether a file is tracked
is not evidence it matters. Both sides of a diff can be legitimate; keep both.

## 9. Generated files

**Rule 9.1 — Generated files state how to regenerate themselves** in their header,
and the SSOT lives outside the generated file.

`estate/.gitignore` is generated from a pinned copy of `github/gitignore`:

```bash
bun ops/bin/gitignore-sync.ts          # render + write
bun ops/bin/gitignore-sync.ts --check  # exit 1 on drift
```

Composition order is load-bearing: `preLayers → templates → postLayers`. Estate
rules come **last** so they can override upstream — `Python.gitignore` ships
`.env`, and the estate tracks it.

## 10. Secrets

**Rule 10.1 — Never print, log, or commit a credential value.** Configuration
surveys report **presence**, never content. Secrets stay in the vault
(`.secrets`, `$HOME/.secrets`, `pitchfork-secrets`).

## 11. Tests

**Rule 11.1 — Test the consumer-visible contract, not the implementation.**
`gitignore-sync` is verified by asking `git check-ignore` what it ignores and by
asserting the `--check` exit code moves — not by string-matching its own output.

**Rule 11.2 — Never test wiring, forwarding, copies, or incidental defaults.**
A test that re-implements the code under test is worse than no test.

**Rule 11.3 — Scripts live in `ops/bin/` with a `.test.ts` sibling**, run with
`bun test`, typecheck with:

```bash
bunx tsc --noEmit --skipLibCheck --module esnext --target es2022 \
  --moduleResolution bundler --strict --types node,bun ops/bin/<file>.ts
```

Typecheck import extensions: use extensionless relative imports
(`./gitignore-sync`), not `./gitignore-sync.ts`, unless
`allowImportingTsExtensions` is enabled.

## 12. Symlinks

**Rule 12.1 — Moving a directory breaks every symlink into it.** A content
rewrite over files never touches link targets. Any bulk move is followed by a
symlink repair pass over the whole home directory.

```bash
find /home/toxic -maxdepth 7 -type d \( -name node_modules -o -name .git -o -name .cache \) \
  -prune -o -type l -print
```

**Rule 12.2 — `xargs` splits on whitespace.** Filenames with spaces
(`Crowd Deny/...`, `Code - Insiders`) become bogus paths. Use `find -print0` with
`xargs -0`, and never suppress stderr on a pass you intend to trust.

## 13. Git

**Rule 13.1 — Commit after every unit of work, push everything.** No local-only
work. Bruteforce repairs go straight to `main`.

**Rule 13.2 — Never force-push `main`.** If `main` has diverged: preserve origin
as `backup/main-<date>` first, merge maximally, then push.

**Rule 13.3 — A gitlink must have a `.git` file.** A gitlink entry pointing at a
directory containing a real `.git` is not a submodule; fresh clones break. `estate`
treats `ranch/` as a separate repo by simply not indexing it.

## 14. Identity

```bash
USER=toxic
REALNAME=Chris
HOSTNAME=awrawr-pc
```

Declared at the top of `estate/.env`.
## 15. Forked upstream code

We fork upstream projects. The fork lives **twice**, and the duplication is
deliberate — do not "deduplicate" it:

- the **standalone repo** carries the real history and the `upstream` remote;
  it is the only place a merge can happen
- the **in-tree copy** is committed as real tracked files in the monorepo, so a
  fresh clone gets a working tool with no submodule and no second checkout

**Rule 15.1 — Never rebase, squash, or force-push a fork's `main`.** Our
commits are the audit trail; audits cite them by hash and the citation must keep
resolving. When upstream takes our work, merge their changes back as a **merge
commit** so the histogram shows both sides happened.

**Rule 15.2 — Never nest a repo inside the monorepo copy.** If a sync creates
`.git` in the in-tree copy, the tree is silently a submodule again. Refuse the
sync and clean up.

**Rule 15.3 — Every merge gets a recorded decision.** Append the decision block
(processed / resulting commit / tag) to the fork's `MERGE-DECISIONS.md`. An
unrecorded merge is a merge we cannot explain later.

**Rule 15.4 — Opening upstream PRs is Chris's call, not an agent's.** Agents
audit and prepare; they do not speak for toxicwind to an external maintainer
group.

The reference implementation of all four rules is `ranch/roundup/` — a fork of
`vllm-project/guidellm`, with the full procedure in
`ranch/roundup/docs/UPSTREAM-MERGE.md` and the mechanism in
`ranch/roundup/scripts/upstream-merge.sh`.
