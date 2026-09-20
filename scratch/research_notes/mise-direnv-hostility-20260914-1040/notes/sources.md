# Source notes

## 1. mise direnv docs page (live)
- URL: https://mise.jdx.dev/direnv.html
- Read: 2026-09-14 via browser_open (verified live)
- Key text:
  - "## direnv deprecated"
  - "[direnv](https://direnv.net) and mise both change the environment when you enter a directory. Their shell hooks can disagree about which `PATH` entries to add, restore, or remove."
  - "Unsupported integration — Using direnv with mise is unsupported. Compatibility issues are not considered mise bugs, and PRs for direnv compatibility are not accepted. The `use mise` integration is deprecated."
  - "Do you need direnv?" mapping table: `export NODE_ENV=development` -> `[env]`; dotenv file -> `env._.file`; add bin to PATH -> `env._.path`; bash script exports -> `env._.source`; python venv -> python venv config.
  - Deprecated `use mise` setup preserved for people maintaining/removing existing integrations: `mise direnv activate > ~/.config/direnv/lib/use_mise.sh`, then `use mise` in `.envrc`. "It gives direnv control of the exported environment and does not provide mise's full activation behavior."
  - "If retaining this integration, avoid having both tools manage the same runtime or virtualenv. A common conflict is direnv's `layout python` alongside a Python version selected by mise."
  - Coexistence note: "the reality is mise and direnv can coexist for simple cases like setting unrelated environment variables. Anything involving PATH — which is most of what people use both tools for — is where problems arise."

## 2. PR #3464 "fix: deprecate direnv integration" — jdx's deprecation rationale
- URL: https://github.com/jdx/mise/pull/3464
- Read: 2026-09-14 via browser automation (verified live)
- jdx (owner) comment, Dec 11, 2024 (edited):
  - "this is not a new decision, this simply documents what has been the actual state of the world for a long time."
  - "If people are still using and liking `use mise` I wouldn't worry, it hasn't had any real changes in a very long time so likely will continue humming along as it does today. I'm probably willing to accept PRs for it too, so it's kind of a "soft" deprecation. I won't be maintaining it myself though so this makes that position clear."
  - "And using direnv with mise together is something I'm going to be more explicit about not supporting. mise may have some lagging feature parity gaps with direnv but I don't think there are very many and certainly not many that are heavily used."
- Merged as commit 816d6ee, Dec 11, 2024; "Fixes #2362"; shipped in release 2024.12.6.
- Commit hid `mise direnv` and `mise direnv activate` from CLI docs (hide: true), updated docs/direnv.md.

## 3. Issue #2362 — the bug report that triggered deprecation
- URL: https://github.com/jdx/mise/issues/2362
- Title: "mise + direnv (use mise) + venv; virtual env gets randomly deactivated"
- Read: 2026-09-14 via browser_open (verified live)
- Reporter used direnv configured with `use mise`, plus `source .venv/bin/activate` in some projects; the venv would get randomly deactivated mid-session — "whether this works or not is rather erratic".
- Thread comments (authorship not captured by page extraction; one participant advised "you probably just shouldn't use direnv and mise for venvs together"; a maintainer-style reply suggested `python.uv_venv_auto` from https://mise.jdx.dev/lang/python.html#python.uv_venv_auto).
- Closed by PR #3464.

## 4. Commit ca78346 — "docs: discourage direnv compatibility PRs and remove issue suggestions"
- URL: https://github.com/jdx/mise/commit/ca7834674fe5a926f462e9c65bb748f8cc0f2ccc
- Read: 2026-09-14 via browser automation (verified live); Apr 10, 2026, authored jdx (+Claude)
- Diff changed docs warning from: "Issues arising from incompatibilities are not considered bugs. If mise has feature gaps that direnv resolves, please open an issue so we can close those gaps." to: "Issues arising from incompatibilities are not considered bugs and PRs to improve direnv compatibility will not be accepted."
- Also changed: "While making mise compatible with direnv is, and will always be a major goal of this project, I also want mise to be capable of replacing direnv if needed." -> "mise is capable of replacing direnv for most use-cases."
- Removed from `use mise` section: "If `mise activate` does not fit your use-case please post an issue."

## 5. src/direnv.rs — the DIRENV_DIFF mechanics (technical conflict)
- URL: https://github.com/jdx/mise/blob/main/src/direnv.rs
- Read: 2026-09-14 via browser automation (verified live)
- `DirenvDiff::parse` decodes DIRENV_DIFF: base64-url + zlib-compressed JSON with `p` (old env) and `n` (new env) maps.
- `new_path()`/`old_path()` read PATH from the new/old env maps.
- `add_path_to_old_and_new`: "this adds a directory to both the old and new path in DIRENV_DIFF. the purpose is to trick direnv into thinking that this path has always been there. that way it does not remove it when it modifies PATH."
- `remove_path_from_old_and_new`: removes a path from both old and new maps.
- This is the arms race: direnv's hook snapshots env before/after .envrc and restores the "old" env on the next hook run, deleting PATH entries it doesn't recognize; mise rewrites DIRENV_DIFF so direnv won't delete mise's entries.

## 6. PR #73 (jdx, Feb 1, 2023) — concrete PATH-wipe bug
- URL: https://github.com/jdx/mise/pull/73
- From search index (2026-09-14): "Fixes #70. I believe I've finally resolved this issue. It was setting PATH when it was _not_ in DIRENV_DIFF which effectively cleared the entire PATH except for rtx installs. This change just ignores DIRENV_DIFF if it doesn't contain PATH."

## 7. PR #23 (jdx, Jan 28, 2023) — origin of `use mise`
- URL: https://github.com/jdx/mise/pull/23
- From search index: "Fixes #8. Direnv isn't compatible with `rtx activate` it may be possible to make that function but in the meantime this adds the ability to use rtx _inside_ of direnv."
- So the integration was always a stopgap, not a supported architecture.

## 8. mise-docs direnv.md (archived) — Jan 21, 2024 jdx note
- URL: https://github.com/jdx/mise-docs/blob/HEAD/direnv.md
- From search index (2026-09-14):
  - "Update 2024-01-21: after `use mise` has been out for a while, the general impression I have is that while it technically functions fine, not many people use it because the DX is notably worse than either switching to mise entirely or using `mise activate` alongside direnv."
  - "The project direction of mise has changed since this was written and the new direction is for it to be capable of replacing direnv completely for any use-case."
  - "I have had virtually no reports of problems with `use mise` in the year it has been out. This could be because virtually [nobody] is using it, or it has been surprisingly stable."
  - "While I have no immediate plans or reasons to do this now, I could see this functionality being the target of a future deprecation. Not because it's a maintenance burden, but because it just hasn't seemed like a particularly useful solution and it may help focus mise on the functionality that does work for users."
- Docs repo migrated into jdx/mise Jun 1, 2024 (#2237).

## 9. PR #8857 (Apr 2026) — ongoing friction, community fix merged
- Commit: https://github.com/jdx/mise/commit/45d5e395b3f6e051367e11c188c9217c86affed8
- From search index: "fix: when direnv diff is empty, do not try to parse it (#8857). I kept getting the following error every time mise started with direnv and mise in my `.zshrc`: When the DIRENV_DIFF environment variable was empty, the parser would bail out and it was a spurious warning. This makes mise ignore empty diff's."
- Files: src/cli/hook_env.rs, src/direnv.rs. (Shows minor robustness PRs still merge.)

## 10. PR #79 — e2e test for direnv unload path reset
- URL: https://github.com/jdx/mise/pull/79
- From search index: "add e2e test for direnv unload path reset issue" (Feb 2023 era) — confirms PATH-reset-on-unload was a real, tested failure mode.

## 11. home-manager keeps the integration alive (community workaround)
- URL: https://github.com/nix-community/home-manager/blob/master/modules/programs/direnv.nix
- From search index (2026-09-14): `programs.direnv.mise.enable` = "integration of use_mise for direnv"; writes `~/.config/direnv/lib/hm-mise.sh` containing `eval "$(mise direnv activate)"`. Added via nix-community/home-manager PR #6000.
- Also: brona90/home-manager commit (2026-04-29) deliberately uses "per-project version pinning via .mise.toml + direnv's `use_mise` stdlib" instead of `mise activate` (perf: hook-env on every prompt).
- martinciu/dotfiles#113: community migration plan "Migrate direnv to mise [env]" — notes "`direnv` and `mise` both hook `chpwd` to manage per-project environment", migrates `.envrc` vars to mise `[env]`, flags `.envrc` files with arbitrary shell logic as "stay on direnv" exceptions.

## 12. docs/direnv.md commit history
- URL (history): https://github.com/jdx/mise/commits/main/docs/direnv.md (verified live 2026-09-14)
- Apr 10, 2026: ab140c8 "docs: tighten direnv compatibility language" (jdx); ca78346 "docs: discourage direnv compatibility PRs and remove issue suggestions" (jdx)
- Jan 10, 2025: prettier revert commits (no content change)
- Dec 11, 2024: 816d6ee "fix: deprecate direnv integration (#3464)"
- Jun 1, 2024: 1de52d7 "chore: migrate docs repo into this repo (#2237)"
