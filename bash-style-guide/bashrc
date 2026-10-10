#!/usr/bin/env bash
# ---
# ~/.bashrc - interactive Bash configuration for the estate.
#
# Twelve numbered sections, in load order. Section 12 loads last; ble.sh
# and starship depend on this ordering. Every tool integration is guarded
# by `command -v`; a missing binary is a no-op, never a broken prompt.
#
# Escape hatches
#   BASH_EVALCACHE_DISABLE=true      skip the cache, eval every time
#   BASH_EVALCACHE_FORCE=1           regenerate the cache once
#   ESTATE_AUTO_JJ=0                 disable jj auto-colocation
#   PI_DISABLE_UUTILS_BUILTINS=0     re-enable uutils builtins
#
# Related files
#   ~/.bashrc.env                    environment tier (sourced first)
#   ~/.bashrc.local                  late hooks      (sourced last)
#   ~/.bash-evalcache/               cache directory for _evalcache
# ---

# --- 01 - environment tier ---
[ -f "$HOME/.bashrc.env" ] && . "$HOME/.bashrc.env"

# --- 02 - re-entry guard ---
# Exported. Subshells inherit the marker and exit early instead of
# re-sourcing the entire file. See R-602.
if [ -n "${__BASHRC_LOADED:-}" ]; then
  return 0 2>/dev/null || exit 0
fi
export __BASHRC_LOADED=1

# --- 03 - non-interactive guard ---
# Return cleanly for scp, rsync, non-login shells.
case $- in
  *i*) ;;
  *) return ;;
esac

# --- 04 - history ---
HISTCONTROL=ignoreboth:erasedups
HISTSIZE=200000
HISTFILESIZE=500000
HISTTIMEFORMAT='%F %T '
shopt -s histappend cmdhist checkwinsize globstar nocaseglob \
        cdspell dirspell dotglob extglob no_empty_cmd_completion

# --- 05 - _evalcache ---
# Cache the output of `tool init bash`. Silent on hit and miss: the cache
# is eval'd, not printed. PID-scoped tmp plus flock guard against the race
# that produced concurrent "mv: cannot stat" errors under fork storms.
# See R-602, R-901.
: "${BASH_EVALCACHE_DIR:=$HOME/.bash-evalcache}"

_evalcache() {
  local cmd="$*"
  local key tmp cache lock

  if [ "${BASH_EVALCACHE_DISABLE:-}" = "true" ]; then
    eval "$cmd"
    return
  fi

  mkdir -p "$BASH_EVALCACHE_DIR" 2>/dev/null || { eval "$cmd"; return; }

  key="$(printf '%s' "$cmd" | tr -c 'a-zA-Z0-9_.-' '_')"
  cache="$BASH_EVALCACHE_DIR/$key"
  tmp="$cache.tmp.$$"
  lock="$cache.lock"

  if [ -s "$cache" ] && [ -z "${BASH_EVALCACHE_FORCE:-}" ]; then
    eval "$(cat "$cache")"
    return 0
  fi

  find "$BASH_EVALCACHE_DIR" -maxdepth 1 -name '*.tmp.*' -mmin +5 \
    -delete 2>/dev/null

  if command -v flock >/dev/null 2>&1; then
    exec 9>"$lock"
    flock 9
  fi

  if [ -s "$cache" ] && [ -z "${BASH_EVALCACHE_FORCE:-}" ]; then
    eval "$(cat "$cache")"
    exec 9>&-
    return 0
  fi

  if eval "$cmd" >"$tmp" 2>/dev/null; then
    mv -f "$tmp" "$cache"
  else
    rm -f "$tmp"
    exec 9>&-
    return 1
  fi

  exec 9>&-
  eval "$(cat "$cache")"
}

_evalcache_clear() {
  local cmd="$*"
  if [ -z "$cmd" ]; then
    rm -f "$BASH_EVALCACHE_DIR"/* 2>/dev/null
    return
  fi
  local key
  key="$(printf '%s' "$cmd" | tr -c 'a-zA-Z0-9_.-' '_')"
  rm -f "$BASH_EVALCACHE_DIR/$key" \
        "$BASH_EVALCACHE_DIR/$key.tmp."* \
        "$BASH_EVALCACHE_DIR/$key.lock" 2>/dev/null
}

# --- 06 - tool hooks ---
if command -v zoxide >/dev/null 2>&1; then
  _evalcache zoxide init bash --cmd cd
fi

# direnv: guarded. If direnv was removed, purge a stale _direnv_hook from
# PROMPT_COMMAND so the prompt stops erroring on every command.
if command -v direnv >/dev/null 2>&1; then
  _evalcache direnv hook bash
else
  if [ -n "${PROMPT_COMMAND:-}" ]; then
    PROMPT_COMMAND="${PROMPT_COMMAND//_direnv_hook/}"
    while [[ "$PROMPT_COMMAND" == ';'* ]]; do PROMPT_COMMAND="${PROMPT_COMMAND#;}"; done
    while [[ "$PROMPT_COMMAND" == *';' ]]; do PROMPT_COMMAND="${PROMPT_COMMAND%;}"; done
    PROMPT_COMMAND="${PROMPT_COMMAND//;;/;}"
  fi
  unset -f _direnv_hook 2>/dev/null || true
fi

if command -v atuin >/dev/null 2>&1; then
  _evalcache atuin init bash --disable-up-arrow --disable-ctrl-r
fi

if command -v mise >/dev/null 2>&1; then
  case ":$PATH:" in
    *":$HOME/.local/share/mise/shims:"*) ;;
    *) _evalcache mise activate bash --shims ;;
  esac
fi

# --- 07 - completions ---
if ! shopt -oq posix; then
  [ -f /usr/share/bash-completion/bash_completion ] && \
    . /usr/share/bash-completion/bash_completion
  for d in "$HOME/.bash_completion.d" \
           "$HOME/.local/share/bash-completion/completions"; do
    [ -d "$d" ] && for f in "$d"/*; do
      [ -r "$f" ] && . "$f"
    done
  done
fi

# --- 08 - fzf ---
if command -v fzf >/dev/null 2>&1; then
  [ -f /usr/share/fzf/key-bindings.bash ] && . /usr/share/fzf/key-bindings.bash
  [ -f /usr/share/fzf/completion.bash ]   && . /usr/share/fzf/completion.bash
  export FZF_DEFAULT_OPTS='--height 40% --layout=reverse --border --inline-info'
  if command -v fd >/dev/null 2>&1; then
    export FZF_DEFAULT_COMMAND='fd --type f --hidden --exclude .git'
    export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
  fi
fi

# --- 09 - colors ---
export CLICOLOR=1
unset NO_COLOR
export GCC_COLORS='error=01;31:warning=01;35:note=01;36:caret=01;32:locus=01:quote=01'
export GREP_COLORS='ms=01;31:mc=01;31:sl=:cx=:fn=35:ln=32:bn=32:se=36'
export LESS_TERMCAP_mb=$'\e[01;31m'
export LESS_TERMCAP_md=$'\e[01;31m'
export LESS_TERMCAP_me=$'\e[0m'
export LESS_TERMCAP_se=$'\e[0m'
export LESS_TERMCAP_so=$'\e[01;44;33m'
export LESS_TERMCAP_ue=$'\e[0m'
export LESS_TERMCAP_us=$'\e[01;32m'

# --- 10 - aliases ---
alias ls='ls -l --color=auto --group-directories-first'
alias ll='ls -alFh'
alias la='ls -A'
alias l='ls -CF'
alias lt='ls -alFht'
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias py='python3'
alias d='docker'
alias dc='docker compose'
alias pf='pitchfork'

if command -v ffs >/dev/null 2>&1; then
  alias ff='ffs find'
  alias ffg='ffs grep'
  alias ffr='ffs read'
  alias ffm='ffs multi-grep'
  alias ffo='ffs outline'
  alias ffsym='ffs symbol'
fi

# --- 11 - helpers ---
mkcd() { mkdir -p -- "$1" && cd -- "$1"; }

extract() {
  case "$1" in
    *.tar.bz2) tar xjf "$1" ;;
    *.tar.gz)  tar xzf "$1" ;;
    *.tar.xz)  tar xJf "$1" ;;
    *.tar.zst) tar --zstd -xf "$1" ;;
    *.bz2)     bunzip2 "$1" ;;
    *.gz)      gunzip "$1" ;;
    *.tar)     tar xf "$1" ;;
    *.zip)     unzip "$1" ;;
    *.7z)      7z x "$1" ;;
    *)         printf 'unknown archive: %s\n' "$1" ;;
  esac
}

readme-check() {
  local f="${1:?usage: readme-check <file.md>}"
  [ -f "$f" ] || { echo "no such file: $f"; return 1; }
  local fails=0
  head -5 "$f" | grep -qiE 'shields\.io|img\.shields|badge' || \
    { echo "FAIL: no badges in first 5 lines"; fails=1; }
  grep -q '^# ' "$f" || { echo "FAIL: no H1 title"; fails=1; }
  grep -qiE 'quick ?start|getting started' "$f" || \
    { echo "FAIL: no Quick Start section"; fails=1; }
  grep -q '```mermaid' "$f" || echo "WARN: no mermaid diagram"
  grep -qiE '^#+ .*(license|security)' "$f" || \
    { echo "FAIL: no License/Security section"; fails=1; }
  grep -qiE 'TODO|FIXME|lorem|coming soon|under construction' "$f" && \
    { echo "FAIL: contains TODO/placeholder text"; fails=1; }
  [ "$fails" -eq 0 ] && echo "OK: $f conforms to readme-maximal"
  return "$fails"
}

# --- 12 - late hooks ---
# Must load last. ble.sh and starship expect to source after everything else.

if [ "${TERM_PROGRAM:-}" = "WezTerm" ] && command -v wezterm >/dev/null 2>&1; then
  [ -f "$HOME/.config/wezterm/shell-integration.sh" ] && \
    . "$HOME/.config/wezterm/shell-integration.sh"
fi

[ -f "$HOME/.bashrc.local" ] && source "$HOME/.bashrc.local"

[ -f "${SKILLS_LIB:-$HOME/.tau/skills/lib}/estate.sh" ] && \
  . "${SKILLS_LIB:-$HOME/.tau/skills/lib}/estate.sh"
: "${SKILLS_HOME:=$HOME/.tau/skills}"
: "${README_SKILL_DIR:=$SKILLS_HOME/readme}"
export README_SKILL_DIR
export README_SKILL_MD="$README_SKILL_DIR/SKILL.md"

# FP-CANARY-REWRITE-PROOF-20260929
# If this line is gone, an autonomous process rewrote $HOME/.bashrc.

[ -r "/home/toxic/.config/bloodhound/aliases.sh" ] && \
  . "/home/toxic/.config/bloodhound/aliases.sh"
set +H

_estate_jj_adopt() {
  [ "${ESTATE_AUTO_JJ:-1}" = "0" ] && return 0
  local d="$PWD"
  [ -d "$d/.git" ] || return 0
  [ -d "$d/.jj" ] && return 0
  command -v jj >/dev/null 2>&1 || return 0
  [ "$(git -C "$d" rev-parse --is-bare-repository 2>/dev/null)" = "true" ] && return 0
  if jj git init --colocate >/dev/null 2>&1; then
    echo "jj: auto-colocated $d (ESTATE_AUTO_JJ=0 to disable)"
  fi
}
case ";${PROMPT_COMMAND:-};" in
  *";_estate_jj_adopt;"*) ;;
  *) PROMPT_COMMAND="${PROMPT_COMMAND:+${PROMPT_COMMAND};}_estate_jj_adopt" ;;
esac

[ -f "$HOME/estate/config/flock-ssot/ports.env" ] && \
  set -a && . "$HOME/estate/config/flock-ssot/ports.env" && set +a
[ -f "$HOME/estate/config/flock-ssot/flock.env" ] && \
  set -a && . "$HOME/estate/config/flock-ssot/flock.env" && set +a

export PI_DISABLE_UUTILS_BUILTINS=1
