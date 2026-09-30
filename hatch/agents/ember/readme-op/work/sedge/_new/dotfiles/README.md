# toxicwind dotfiles 🏠

![Shell](https://img.shields.io/badge/shell-bash-blue?logo=gnubash)
![Prompt](https://img.shields.io/badge/prompt-starship-yellow)
![Tests](https://img.shields.io/badge/tests-bats-green)
![Private](https://img.shields.io/badge/repo-private-lightgrey)

Curated snapshot of the HypeBrut shell environment: thin Bash loader, segmented
`.bashrc.d` modules, Starship theming, and helper scripts like the Geeqie
Wayland clipboard bridge. Everything in `home/` mirrors the real file layout
so it can be staged or applied without extra tooling.

## Layout

- `home/` – Files that map 1:1 onto `$HOME`: Bash loader (`.bashrc`,
  `.bash_profile`, `.bash_logout`, `.bash-preexec.sh`), 10 `.bashrc.d/`
  modules, Starship config (`.config/starship.toml`), `.local/bin-core`
  helpers, Geeqie module, and a `Makefile`.
- `manifest.txt` – Canonical list of tracked paths. Edit this before adding new
  material.
- `scripts/update-from-home.sh` – Pulls the current workstation state into the
  repo (non-interactive, prints `[update] …`).
- `scripts/deploy-to-home.sh` – Writes repo contents back to `$HOME` with
  timestamped backups in `~/.local/share/dotfiles-backups/` (non-interactive,
  prints `[deploy] …`).
- `docs/AGENTS.md` – Archived copy of the active HypeBrut charter; the
  source-of-truth for shell layout, PATH order, module policy, and reporting.
- `home/tests/` – Bats test suite to sanity-check the shell stack
  (`rc_load.bats`, `bin_core_execs.bats`, `mamba_integration.bats`,
  `python_wrappers.bats`).
- `skills/kimi-sdk/` – Kimi SDK skill: Python client, error types, and
  references (incl. `references/routing.md`).
- `swarm_workspace/` – Kimi agent-gw plugin shims (`audio_unlocked.py`,
  `image_unlocked.py`, `data_unlocked.py`, `manifest.json`); see its own
  [README](swarm_workspace/README.md) for usage.
- `.env.example` – Template for environment secrets (copy to `.env`; never
  commit real values).

## Usage

```bash
# Refresh repo from live system
./scripts/update-from-home.sh

# Deploy repo contents back to $HOME (backs up existing files)
./scripts/deploy-to-home.sh

# Sanity-check the shell stack
bats home/tests/
```

Backups land under `~/.local/share/dotfiles-backups/<timestamp>/`. Restore by
copying files back from there if needed.

## Size & content guardrails

- Keep individual tracked files under **1 MB**. Compiled binaries (e.g.
  `micromamba`, third-party CLI builds) stay out of git; install them
  separately.
- `.gitignore` whitelists only the curated shell helpers inside
  `home/.local/bin-core/`. Anything not whitelisted is ignored to prevent
  accidental binary uploads.
- Secrets, API keys, wallets, caches, node data, or runtime logs must never be
  added. Update `manifest.txt` whenever you onboard new files so they can be
  reviewed deliberately.

> ⚠️ **HypeBrut Charter**
> `docs/AGENTS.md` mirrors the live instructions that govern shell layout, PATH
> order, module policy, and reporting. Every change to the dotfiles must keep
> that contract intact; update the charter copy alongside any structural change
> so new clones stay compliant.

## GitHub automation

The repo is designed to live at `git@github.com:toxicwind/dotfiles.git`
(private). Use the GitHub CLI for routine sync:

```bash
# Commit latest edits
./scripts/update-from-home.sh
git add -A
git commit -m "chore: refresh dotfiles"

# Push to GitHub via gh
gh repo sync
```

If the remote ever needs to be rebuilt from scratch:

```bash
gh repo delete toxicwind/dotfiles --yes
gh repo create toxicwind/dotfiles --private --source . --push
```

## Roadmap ideas

- Mirror additional modules (tmux, kitty, neovim) by appending to
  `manifest.txt`.
- Add CI lint to smoke-test shell scripts (e.g. `shellcheck`, `shfmt`).
- Integrate secrets with `pass` or age if encrypted files become necessary.

## License

No `LICENSE` file is present in this snapshot. Private dotfiles.
