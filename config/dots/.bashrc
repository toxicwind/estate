# =====================================================================
# AESTHETIC INTERACTIVE TERMINAL CONFIGURATION
# =====================================================================

# 1. Load Universal Environment Tier First
[ -f "$HOME/.bashrc.env" ] && . "$HOME/.bashrc.env"

# 2. Re-entry Guard
if [ -n "${__BASHRC_LOADED:-}" ]; then return 0 2>/dev/null || exit 0; fi
__BASHRC_LOADED=1

# 3. Non-Interactive Guard (Abort cleanly for scp/rsync)
[[ $- != *i* ]] && return

# 4. History Management
HISTCONTROL=ignoreboth:erasedups
HISTSIZE=200000
HISTFILESIZE=500000
HISTTIMEFORMAT='%F %T '
shopt -s histappend cmdhist checkwinsize globstar nocaseglob cdspell dirspell dotglob extglob no_empty_cmd_completion

# 5. Native Tool Integrations
command -v zoxide  >/dev/null 2>&1 && eval "$(zoxide init bash --cmd cd)"
command -v starship >/dev/null 2>&1 && eval "$(starship init bash)"
command -v direnv  >/dev/null 2>&1 && eval "$(direnv hook bash)"
command -v atuin   >/dev/null 2>&1 && eval "$(atuin init bash --disable-up-arrow --disable-ctrl-r)"

if command -v mise >/dev/null 2>&1; then
  case ":$PATH:" in
    *":$HOME/.local/share/mise/shims:"*) ;;
    *) eval "$(mise activate bash --shims)" ;;
  esac
fi

# 6. Completions & FZF
if ! shopt -oq posix; then
  [ -f /usr/share/bash-completion/bash_completion ] && . /usr/share/bash-completion/bash_completion
  for d in "$HOME/.bash_completion.d" "$HOME/.local/share/bash-completion/completions"; do
    [ -d "$d" ] && for f in "$d"/*; do [ -r "$f" ] && . "$f"; done
  done
fi

if command -v fzf >/dev/null 2>&1; then
  [ -f /usr/share/fzf/key-bindings.bash ] && . /usr/share/fzf/key-bindings.bash
  [ -f /usr/share/fzf/completion.bash ]   && . /usr/share/fzf/completion.bash
  export FZF_DEFAULT_OPTS='--height 40% --layout=reverse --border --inline-info'
  command -v fd >/dev/null 2>&1 && export FZF_DEFAULT_COMMAND='fd --type f --hidden --exclude .git' FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
fi

# 7. Colors & Highlights
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

# 8. Core Ergonomic Aliases
alias ls='ls --color=auto --group-directories-first'
alias ll='ls -alFh'
alias la='ls -A'
alias l='ls -CF'
alias lt='ls -alFht'
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias p='pass'
alias py='python3'
alias k9='kubectl'
alias d='docker'
alias dc='docker compose'
alias pf='pitchfork'   # was: $HOME/.local/bin/pitchfork-quiet (binary does not exist)

# First-class Agent Finder Aliases (ffs)
if command -v ffs >/dev/null 2>&1; then
  alias ff='ffs find'
  alias ffg='ffs grep'
  alias ffr='ffs read'
  alias ffm='ffs multi-grep'
  alias ffo='ffs outline'
  alias ffsym='ffs symbol'
fi

# 9. Engine Aliases
# tau/omp/pi resolve via the pinned immutable launcher in ~/.local/bin/tau
alias tau="$HOME/.local/bin/tau"
alias omp="$HOME/.local/bin/omp"
alias pi="$HOME/.local/bin/tau"

# Disable non-standard pi-builtins so standard GNU coreutils (grep, find, sed, etc.) always run
for _b in \
  grep find sed cat cut diff head tail ls ln mv rm cp mkdir mktemp \
  stat dirname basename touch tr sort uniq wc which whoami uname seq \
  date timeout nohup ps top pgrep pkill pidwait printenv realpath \
  readlink md5sum sha1sum sha256sum sha512sum b2sum cksum jq xargs rg fd
do
  enable -n "$_b" 2>/dev/null || true
done
unset _b
# 10. Helper Functions
mkcd() { mkdir -p -- "$1" && cd -- "$1"; }

extract() {
  case "$1" in
    *.tar.bz2) tar xjf "$1";;
    *.tar.gz)  tar xzf "$1";;
    *.tar.xz)  tar xJf "$1";;
    *.tar.zst) tar --zstd -xf "$1";;
    *.bz2)     bunzip2 "$1";;
    *.gz)      gunzip "$1";;
    *.tar)     tar xf "$1";;
    *.zip)     unzip "$1";;
    *.7z)      7z x "$1";;
    *)         printf 'unknown archive: %s\n' "$1";;
  esac
}

# 11. Terminal & Ble.sh Hooks (Must load last)
if [ "${TERM_PROGRAM:-}" = "WezTerm" ] && command -v wezterm >/dev/null 2>&1; then
  [ -f "$HOME/.config/wezterm/shell-integration.sh" ] && . "$HOME/.config/wezterm/shell-integration.sh"
fi

[ -f "$HOME/.bashrc.local" ] && source "$HOME/.bashrc.local"

# ── Skills: resolved, never hardcoded ───────────────────────────────────
# Canonical skills home is estate/skills. See estate/docs/CONVENTIONS.md.
# shellcheck source=/dev/null
[ -f "${SKILLS_LIB:-$HOME/.tau/skills/lib}/estate.sh" ] && . "${SKILLS_LIB:-$HOME/.tau/skills/lib}/estate.sh"
: "${SKILLS_HOME:=$HOME/.tau/skills}"
: "${README_SKILL_DIR:=$SKILLS_HOME/readme}"

# README-MAXIMAL skill — permanent (Chris 2026-09-29)
# Aesthetic GitHub README doctrine lives here; every first-party README.md
# in the estate must conform to it (badges first, why-care hero, feature
# bullets, diagram, quick start, architecture, config, dev, license+security).
export README_SKILL_DIR
export README_SKILL_MD="$README_SKILL_DIR/SKILL.md"

# FP-CANARY-REWRITE-PROOF-20260929
# if this line is gone, an autonomous process rewrote $HOME/.bashrc

# readme-check <file.md> — audit a README against the readme-maximal rubric.
# Exit 0 = conformant, 1 = gaps listed.
readme-check() {
  local f="${1:?usage: readme-check <file.md>}"
  [ -f "$f" ] || { echo "no such file: $f"; return 1; }
  local fails=0
  head -5 "$f" | grep -qiE 'shields\.io|img\.shields|badge' || { echo "FAIL: no badges in first 5 lines"; fails=1; }
  grep -q '^# ' "$f" || { echo "FAIL: no H1 title"; fails=1; }
  grep -qiE 'quick ?start|getting started' "$f" || { echo "FAIL: no Quick Start section"; fails=1; }
  grep -q '```mermaid' "$f" || echo "WARN: no mermaid diagram"
  grep -qiE '^#+ .*(license|security)' "$f" || { echo "FAIL: no License/Security section"; fails=1; }
  grep -qiE 'TODO|FIXME|lorem|coming soon|under construction' "$f" && { echo "FAIL: contains TODO/placeholder text"; fails=1; }
  grep -qi 'placeholder' "$f" && echo "WARN: contains the word placeholder - verify it is prose, not a doc stub"
  [ "$fails" -eq 0 ] && echo "OK: $f conforms to readme-maximal"
  return "$fails"
}

# >>> vercel ai-gateway >>>
# Managed by `vercel ai-gateway setup` — safe to remove this block.
export COPILOT_PROVIDER_BASE_URL='https://ai-gateway.vercel.sh/coding-agent/v1'
export COPILOT_PROVIDER_API_KEY="${VERCEL_AI_GATEWAY_API_KEY:-$AI_GATEWAY_API_KEY}"
export COPILOT_MODEL='zai/glm-5.3'
export AI_GATEWAY_API_KEY="${AI_GATEWAY_API_KEY:-$VERCEL_AI_GATEWAY_API_KEY}"
# <<< vercel ai-gateway <<<


# Generated for pdtm. Do not edit.
export PATH=$PATH:/home/toxic/.pdtm/go/bin


# ── NIM OMNIBUS ──
source /home/toxic/nim-omnibus.sh

# 2-second rule shim (estate doctrine): known-slow cmds via run-fast
shopt -s expand_aliases 2>/dev/null
source /home/toxic/estate/bin/bash-2s-shim.sh 2>/dev/null
