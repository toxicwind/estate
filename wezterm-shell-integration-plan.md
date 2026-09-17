# WezTerm Shell Integration Plan

## Goal
Implement a WezTerm-compatible shell configuration that enables proper terminal integration, shell history, and CLI tool compatibility.

## Plan

### 1. WezTerm Configuration
- Create ~/.config/wezterm/wezterm.lua with:
  - `config.enable_kitty_keyboard = true`
  - `config.term = "wezterm"`
  - `config.default_prog = { "/bin/bash", "-l" }`

### 2. Shell Integration
- Source shell-integration.sh if available:
  ```bash
  [[ -f ~/.config/wezterm/shell-integration.sh ]] && source ~/.config/wezterm/shell-integration.sh
  ```
- Ensure this file emits OSC 7/133 for tab management and pane_cwd detection

### 3. Shell Configuration
- Use ~/.bashrc for non-interactive shells only
- Define __zsh_like_cd() and cd() functions:
  ```bash
  __zsh_like_cd() { builtin cd "$@"; }
  cd() { builtin cd "$@"; }
  ```
- Set BASH_ENV="$HOME/.bashrc" in ~/.profile to ensure non-interactive shells source .bashrc
- Use `bash -l -c` for all commands requiring cd functionality

### 4. Tooling Integration
- Install and use Starship for prompt:
  ```bash
  eval "$(starship init bash)"
  ```
- Use zoxide for directory jumping:
  ```bash
  eval "$(zoxide init bash)"
  ```
- Use fzf for fuzzy finding:
  ```bash
  eval "$(fzf --bash)"
  ```

### 5. Documentation
- Update herd/README.md to reflect actual wezterm configuration
- Create mesh/README.md documenting mesh router endpoints and port 25120
- Ensure all READMEs reference the correct configuration files

### 6. Verification
- Run `wezterm cli list --format json | jq .` to verify terminal
- Run `cd /tmp && echo $PWD` to test cd functionality
- Run `git submodule status` to verify submodule initialization
- Confirm all submodules are initialized and working

## Verification
- All submodules show as initialized (`-` prefix)
- `git submodule status` shows no errors
- `cd` and `__zsh_like_cd` both work in all shell contexts
- `wezterm cli list` returns valid output
- All READMEs are up-to-date and accurate