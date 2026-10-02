# mise vs direnv: why the maintainers refuse direnv support

## Summary

The mise maintainers (in practice, BDFL Jeff Dickey / jdx) do not support direnv integration for two intertwined reasons:

1. **Principled / technical**: direnv and `mise activate` both install shell hooks that snapshot the environment before/after their hook runs and then try to restore/add/remove `PATH` entries. The two hooks can and do disagree, producing real bugs: wiped `PATH`s (issue #70), PATH resets on unload (PR #79), and randomly deactivated Python venvs mid-session (issue #2362). mise's own source (`src/direnv.rs`) resorts to *rewriting direnv's internal state* ("trick direnv into thinking that this path has always been there") to keep direnv from deleting mise's PATH entries — an arms race, not an integration.
2. **Strategic / territorial**: jdx explicitly repositioned mise as a *replacement* for direnv ("the new direction is for it to be capable of replacing direnv completely for any use-case", Jan 2024), and framed the `use mise` integration as a low-value stopgap ("hasn't seemed like a particularly useful solution and it may help focus mise on the functionality that does work for users"). Notably, in Jan 2024 he said deprecation would **not** be "because it's a maintenance burden" — i.e., the refusal is a product-direction choice, not an inability to make it work.

The timeline moved from a "soft" deprecation (Dec 2024 — jdx said he was "probably willing to accept PRs") to a hard policy (Apr 2026 — "PRs to improve direnv compatibility will not be accepted"). The one softening nuance in the docs: simple coexistence (direnv for *unrelated* env vars) is acknowledged to work fine; the war is over `PATH`.

**Assessment**: the refusal is **both** principled and territorial. The technical incompatibility is real and documented in code and bug reports, but the hard policy ("PRs not accepted") goes beyond what the technical facts require — jdx himself admitted `use mise` was "surprisingly stable" and he would accept PRs for it in 2024. The Apr 2026 hardening looks like a decision to stop spending attention on a competing tool's ecosystem rather than a response to new technical evidence.

## 1. Maintainers' stated reasons (in their own words)

All quotes below are from jdx (Jeff Dickey), the project's owner; no other maintainer has published a distinct position — the repo is BDFL-run.

**Current official policy** (docs, https://mise.jdx.dev/direnv.html):
> "Unsupported integration — Using direnv with mise is unsupported. Compatibility issues are not considered mise bugs, and PRs for direnv compatibility are not accepted. The `use mise` integration is deprecated."

**On the deprecation PR** (https://github.com/jdx/mise/pull/3464, jdx comment, Dec 11, 2024):
> "this is not a new decision, this simply documents what has been the actual state of the world for a long time."
> "If people are still using and liking `use mise` I wouldn't worry, it hasn't had any real changes in a very long time so likely will continue humming along as it does today. I'm probably willing to accept PRs for it too, so it's kind of a 'soft' deprecation. I won't be maintaining it myself though so this makes that position clear."
> "And using direnv with mise together is something I'm going to be more explicit about not supporting. mise may have some lagging feature parity gaps with direnv but I don't think there are very many and certainly not many that are heavily used."

**On project direction** (mise-docs archive, https://github.com/jdx/mise-docs/blob/HEAD/direnv.md, note dated 2024-01-21):
> "The project direction of mise has changed since this was written and the new direction is for it to be capable of replacing direnv completely for any use-case."
> "after `use mise` has been out for a while, the general impression I have is that while it technically functions fine, not many people use it because the DX is notably worse than either switching to mise entirely or using `mise activate` alongside direnv."
> "While I have no immediate plans or reasons to do this now, I could see this functionality being the target of a future deprecation. Not because it's a maintenance burden, but because it just hasn't seemed like a particularly useful solution and it may help focus mise on the functionality that does work for users."

**On the original integration's status as a stopgap** (PR #23, https://github.com/jdx/mise/pull/23, Jan 2023):
> "Direnv isn't compatible with `rtx activate` it may be possible to make that function but in the meantime this adds the ability to use rtx *inside* of direnv."

## 2. The technical conflict, explained

**The mechanism.** Both tools hook directory changes (chpwd / precmd / PROMPT_COMMAND) and, on each hook run, compute the environment delta and rewrite the shell env:

- direnv records the env before and after loading `.envrc` in `DIRENV_DIFF` — a base64+zlib-compressed JSON blob with `p` (old) and `n` (new) maps — and on subsequent hook runs it *restores* the old environment, removing PATH entries it doesn't believe should be there.
- mise's `hook-env` likewise computes which PATH entries to add/remove based on config files.

The docs' one-line summary (https://mise.jdx.dev/direnv.html): *"Their shell hooks can disagree about which `PATH` entries to add, restore, or remove."*

**The arms race in mise's own source** (`src/direnv.rs`, read live at https://github.com/jdx/mise/blob/main/src/direnv.rs). mise parses direnv's private `DIRENV_DIFF` and includes this function:

```rust
/// this adds a directory to both the old and new path in DIRENV_DIFF
/// the purpose is to trick direnv into thinking that this path has always been there
/// that way it does not remove it when it modifies PATH
pub(crate) fn add_path_to_old_and_new(...)
```

That comment is the whole story in miniature: mise is mutating direnv's internal bookkeeping so direnv won't delete mise-installed PATH entries. It works only as long as both sides' assumptions hold — ordering of the two hooks, whether PATH appears in the diff at all, etc.

**Concrete bug reports:**
- Issue #70 / PR #73 (jdx, Feb 2023): mise "was setting PATH when it was *not* in DIRENV_DIFF which effectively cleared the entire PATH except for rtx installs." Fix: ignore DIRENV_DIFF when it lacks PATH. (https://github.com/jdx/mise/pull/73)
- PR #79: e2e test added for a "direnv unload path reset issue" — direnv wiping mise paths on unload. (https://github.com/jdx/mise/pull/79)
- Issue #2362 (2024): with `use mise` + `source .venv/bin/activate` in `.envrc`, the virtualenv got "randomly deactivated" mid-session — "whether this works or not is rather erratic." This is the issue that directly triggered the formal deprecation. (https://github.com/jdx/mise/issues/2362)
- PR #8857 (Apr 2026): empty `DIRENV_DIFF` made mise's parser "bail out" with a spurious warning on every shell start when direnv was also hooked — fixed by a community PR. (https://github.com/jdx/mise/commit/45d5e395b3f6e051367e11c188c9217c86affed8)

**Bottom line on the technical argument**: it is genuine. Two independent snapshot-and-restore loops over the same mutable state (the shell environment) with no coordination protocol will fight over PATH. mise's mitigation is to falsify direnv's ledger, which is inherently fragile.

## 3. Deprecation timeline

| Date | Event | Source |
|---|---|---|
| Jan 28, 2023 | jdx adds the `use mise` integration (PR #23, "direnv integration", fixes #8) as a stopgap: "Direnv isn't compatible with `rtx activate`... in the meantime this adds the ability to use rtx *inside* of direnv." | https://github.com/jdx/mise/pull/23 (index) |
| Feb 2023 | PATH-wipe bug (#70) fixed in PR #73; e2e test for unload PATH reset (PR #79) | https://github.com/jdx/mise/pull/73, https://github.com/jdx/mise/pull/79 (index) |
| Jan 21, 2024 | jdx writes in docs: project direction is now to *replace direnv completely*; floats future deprecation of `use mise` — explicitly "Not because it's a maintenance burden" but because it "hasn't seemed like a particularly useful solution." Notes `use mise` had "virtually no reports of problems... in the year it has been out." | https://github.com/jdx/mise-docs/blob/HEAD/direnv.md (index) |
| Jun 1, 2024 | Docs repo merged into jdx/mise (#2237) | commit 1de52d7 |
| 2024 | Issue #2362: venv randomly deactivated with `use mise` + direnv | https://github.com/jdx/mise/issues/2362 (verified live) |
| Dec 11, 2024 | PR #3464 "fix: deprecate direnv integration" merged (commit 816d6ee, released in 2024.12.6). Closes #2362. `mise direnv` / `mise direnv activate` hidden from CLI docs; docs get a deprecation warning. jdx calls it a "soft" deprecation and says he's "probably willing to accept PRs." | https://github.com/jdx/mise/pull/3464, https://github.com/jdx/mise/commit/816d6eec2c04302b37a8a4c9032bcfe344d80d5a (verified live) |
| Apr 10, 2026 | Commit ca78346 "docs: discourage direnv compatibility PRs and remove issue suggestions": "PRs to improve direnv compatibility will not be accepted"; removes "please open an issue so we can close those gaps" and the "making mise compatible with direnv is, and will always be a major goal" line, replacing it with "mise is capable of replacing direnv for most use-cases." Companion commit ab140c8 "tighten direnv compatibility language." | https://github.com/jdx/mise/commit/ca7834674fe5a926f462e9c65bb748f8cc0f2ccc (verified live) |
| Apr 2026 | Community PR #8857 merged (empty-DIRENV_DIFF parse fix) — minor robustness fixes still land even under the hard policy | https://github.com/jdx/mise/commit/45d5e395b3f6e051367e11c188c9217c86affed8 (index) |

## 4. Contrast: direnv-first patterns and legitimate coexistence

**How direnv handles per-directory env** (mechanics both tools share): direnv hooks `chpwd`/`precmd`, runs `.envrc` in a bash subprocess, diffs the environment before/after, stores the diff in `DIRENV_DIFF`, and exports only the delta back to the interactive shell. Leaving the directory reverses the delta. This is a general mechanism (arbitrary shell code, `layout python`, `use nix`, dotenv, stdlib helpers); mise's `[env]` is declarative config (`KEY="value"`, `_.file`, `_.path`, `_.source`, `_.python.venv`) evaluated by a single tool that also owns the tool shims/PATH.

**The docs' own coexistence carve-out** (https://mise.jdx.dev/direnv.html): "the reality is mise and direnv can coexist for simple cases like setting unrelated environment variables. Anything involving PATH — which is most of what people use both tools for — is where problems arise." And: "A more typical use of direnv is to set arbitrary environment variables or add unrelated binaries to PATH. In these cases, mise does not interfere with direnv."

**Legitimate separation-of-concerns pattern** (acknowledged by the docs and used in the community):
- mise owns tool versions and the PATH entries for those tools (`mise activate`);
- direnv owns everything else (project secrets, arbitrary exports, non-mise PATH additions) — and crucially, **never manages the same runtime or venv** ("avoid having both tools manage the same runtime or virtualenv. A common conflict is direnv's `layout python` alongside a Python version selected by mise").
- For venvs specifically, the maintainers' answer is mise-native: `_.python.venv` / `python.uv_venv_auto` (https://mise.jdx.dev/lang/python.html#python.uv_venv_auto), not `layout python` or `source .venv/bin/activate` inside `.envrc`.

One community dotfiles migration (https://github.com/martinciu/dotfiles/issues/113) formalized exactly this: both tools hook chpwd, so move `.envrc` vars into mise `[env]`, keeping "stay on direnv" exceptions only for `.envrc` files with arbitrary shell logic that doesn't translate.

## 5. Community workarounds / forks keeping direnv+mise alive

- **nix-community/home-manager** ships a first-class `programs.direnv.mise.enable` option that writes `eval "$(mise direnv activate)"` to `~/.config/direnv/lib/hm-mise.sh`, keeping the deprecated `use_mise` integration working for Nix users (added in nix-community/home-manager#6000). Source: https://github.com/nix-community/home-manager/blob/master/modules/programs/direnv.nix (index).
- **Individual users** still choose `use_mise` deliberately: one home-manager user (Apr 2026) kept "per-project version pinning via .mise.toml + direnv's `use_mise` stdlib" while *disabling* `mise activate`, because `mise hook-env` on every prompt cost seconds at shell startup — `use mise` pays the cost once per `cd` instead. (https://github.com/brona90/home-manager/commit/14230f6025bd1f529412ead5000b1113796fb7a6, index).
- **The old docs-endorsed escape hatch**: drive mise from direnv via env vars (`export MISE_NODE_VERSION=20.0.0`, `export MISE_PYTHON_VERSION=3.11` in `.envrc`) with no hooks at all — documented in the archived mise-docs page (https://github.com/jdx/mise-docs/blob/HEAD/direnv.md, index).
- No notable fork of mise itself exists for direnv support; the command (`mise direnv activate`) still exists in the binary, just hidden from docs and unmaintained.

## Could not verify / open questions

- Authorship of the issue-#2362 thread comment "you probably just shouldn't use direnv and mise for venvs together" — the page extraction did not attribute comments to users, so I cannot confirm whether it was jdx or a community member. (jdx's own reply in that thread recommended `python.uv_venv_auto`.)
- Exact diff of commit ab140c8 ("tighten direnv compatibility language", Apr 10, 2026) — not read; the current docs page text reflects its end state.
- The archived mise-docs note "I have had virtually no reports of problems with `use mise`" is jdx's impression from Jan 2024, pre-dating issue #2362.

## Sources

- https://mise.jdx.dev/direnv.html — current direnv docs (read 2026-09-14, verified live)
- https://github.com/jdx/mise/pull/3464 — deprecation PR + jdx rationale comment (read 2026-09-14, verified live)
- https://github.com/jdx/mise/commit/816d6eec2c04302b37a8a4c9032bcfe344d80d5a — deprecation commit (read 2026-09-14, verified live)
- https://github.com/jdx/mise/commit/ca7834674fe5a926f462e9c65bb748f8cc0f2ccc — "PRs not accepted" policy commit (read 2026-09-14, verified live)
- https://github.com/jdx/mise/issues/2362 — venv deactivation report (read 2026-09-14, verified live)
- https://github.com/jdx/mise/blob/main/src/direnv.rs — DIRENV_DIFF handling source (read 2026-09-14, verified live)
- https://github.com/jdx/mise/commits/main/docs/direnv.md — docs history (read 2026-09-14, verified live)
- https://github.com/jdx/mise-docs/blob/HEAD/direnv.md — Jan 2024 direction note (index)
- https://github.com/jdx/mise/pull/73 — PATH-wipe fix (index)
- https://github.com/jdx/mise/pull/23 — original `use mise` integration (index)
- https://github.com/jdx/mise/pull/79 — unload PATH reset e2e test (index)
- https://github.com/jdx/mise/commit/45d5e395b3f6e051367e11c188c9217c86affed8 — PR #8857 empty-diff fix (index)
- https://github.com/nix-community/home-manager/blob/master/modules/programs/direnv.nix — community integration (index)
- https://github.com/martinciu/dotfiles/issues/113 — community direnv→mise migration (index)
- https://github.com/brona90/home-manager/commit/14230f6025bd1f529412ead5000b1113796fb7a6 — deliberate `use_mise` use (index)
