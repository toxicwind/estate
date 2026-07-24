# Add deno completions to search path
if [[ ":$FPATH:" != *":/home/toxic/.zsh/completions:"* ]]; then export FPATH="/home/toxic/.zsh/completions:$FPATH"; fi
# ~/.zshrc — 2026 grade, agent-safe, sm_86 unblinded - FIXED
# --- 1) AGENT DETECT (must stay top) ---
typeset -g _ZSHRC_AGENT=0 _ZSHRC_AGENT_HARD=0 _ZSHRC_AGENT_SOFT=0
_zshrc_mark_ai(){ [[ -n ${GROK_AGENT:-}${CI:-}${CLAUDE_CODE:-}${CURSOR_AGENT:-}${CODEX_SANDBOX:-}${COMPOSER_NO_INTERACTION:-} ]] && return 0; return 1 }
_zshrc_mark_ai && { _ZSHRC_AGENT=1; _ZSHRC_AGENT_SOFT=1 }
[[ ! -o interactive || ! -t 0 ]] && { _ZSHRC_AGENT=1; _ZSHRC_AGENT_HARD=1; _ZSHRC_AGENT_SOFT=0 }
if (( _ZSHRC_AGENT_HARD )); then
  # Minimal interactive-off path — still always include coreutils (/usr/bin)
  typeset -U path
  path=($HOME/bin $HOME/.cargo/bin $HOME/.local/bin $HOME/.bun/bin /usr/local/bin /usr/bin /bin)
  export PATH
  export PAGER=cat MANPAGER=cat GIT_PAGER=cat
  return 0
fi

# --- 2) ENV + PATH + CUDA SM_86 UNBLINDED ---
export LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 EDITOR=nano VISUAL=nano
export TORCH_CUDA_ARCH_LIST="8.6" CMAKE_CUDA_ARCHITECTURES="86" VLLM_FA_ARCHS="8.6"
export CUDA_CACHE_DISABLE=0 CUDA_CACHE_MAXSIZE=10737418240 CUDA_CACHE_PATH=$HOME/.nv/ComputeCache
export CUDA_NVCC_FLAGS="-gencode arch=compute_86,code=sm_86 -O3 --use_fast_math"
export CMAKE_CUDA_COMPILER_LAUNCHER=sccache RUSTC_WRAPPER=sccache SCCACHE_DIR=$HOME/.cache/sccache
export MAKEFLAGS="-j$(nproc) -l$(nproc)" CARGO_BUILD_JOBS="$(nproc)"
# ZLUDA note: if you export LD_LIBRARY_PATH with zluda libcuda.so, unset CUDA_NVCC_FLAGS

typeset -U path fpath
for d in $HOME/.local/bin /usr/bin $HOME/bin $HOME/.cargo/bin $HOME/.bun/bin $HOME/.local/share/mise/shims $HOME/.local/bin $HOME/.grok/bin $HOME/sovereign/bin $HOME/.openfang/bin $HOME/go/bin /usr/local/bin; do
  [[ -d $d ]] && path=($d $path)
done
fpath=($HOME/.zsh/completions $HOME/.grok/completions/zsh $fpath)
export BUN_INSTALL="$HOME/.bun"
# use path array, not export PATH, so typeset -U dedup works
[[ -d $BUN_INSTALL/bin ]] && path=($BUN_INSTALL/bin $path)

# --- 3) OPTIONS + HISTORY - FIXED RM_STAR ---
setopt NO_CHECK_JOBS NO_HUP NO_BG_NICE NO_BEEP INTERACTIVE_COMMENTS AUTOCD PROMPT_SUBST
setopt RM_STAR_SILENT # <-- FIX: never prompt on rm * / rm path/*
setopt NO_NOMATCH # keep, but we handle globs safely below
# for scripts that need empty globs, use (N) qualifier, not global NULL_GLOB
HISTFILE=~/.zsh_history; HISTSIZE=200000; SAVEHIST=200000
setopt APPEND_HISTORY INC_APPEND_HISTORY HIST_IGNORE_SPACE HIST_IGNORE_ALL_DUPS HIST_SAVE_NO_DUPS HIST_FIND_NO_DUPS

# --- 4) ZINIT BOOTSTRAP ---
if [[ ! -f $HOME/.local/share/zinit/zinit.git/zinit.zsh ]]; then
  mkdir -p $HOME/.local/share/zinit && git clone https://github.com/zdharma-continuum/zinit $HOME/.local/share/zinit/zinit.git
fi
source $HOME/.local/share/zinit/zinit.git/zinit.zsh
autoload -Uz _zinit; (( ${+_comps} )) && _comps[zinit]=_zinit

zinit wait'0a' lucid for zsh-users/zsh-completions
zinit wait'0b' lucid for Aloxaf/fzf-tab

# --- 5) COMPLETION SYSTEM ---
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}' 'r:|[._-]=* r:|=*' 'l:|=* r:|=*'
zstyle ':completion:*' use-cache on; zstyle ':completion:*' cache-path ${XDG_CACHE_HOME:-$HOME/.cache}/zsh/completions
zstyle ':completion:*' menu select
zstyle ':completion:*:descriptions' format '[%d]'
zstyle ':fzf-tab:*' switch-group '<' '>'
mkdir -p ${XDG_CACHE_HOME:-$HOME/.cache}/zsh/completions
autoload -Uz compinit; compinit -i -d ${XDG_CACHE_HOME:-$HOME/.cache}/zsh/zcompdump-$ZSH_VERSION
zinit cdreplay -q

# --- 6) PLUGINS ---
zinit wait lucid for \
  atinit"zicompinit; zicdreplay" zdharma-continuum/fast-syntax-highlighting \
  atload"_zsh_autosuggest_start" zsh-users/zsh-autosuggestions \
  MichaelAquilina/zsh-you-should-use \
  hlissner/zsh-autopair

(( $+commands[carapace] )) && { export CARAPACE_BRIDGES='zsh,fish,bash,inshellisense'; source <(carapace _carapace zsh); }
(( $+commands[atuin] )) && eval "$(atuin init zsh --disable-up-arrow)"
(( $+commands[zoxide] )) && eval "$(zoxide init --cmd cd zsh)"
(( $+commands[fzf] )) && source <(fzf --zsh)
(( $+commands[direnv] )) && eval "$(direnv hook zsh)"
(( $+commands[mise] )) && eval "$(mise activate zsh)"

_nvidia_smi_gpus(){ local -a ids; ids=(${(f)"$(nvidia-smi --query-gpu=index --format=csv,noheader 2>/dev/null)"}); _describe 'gpu' ids }
compdef _nvidia_smi_gpus nvidia-smi 2>/dev/null || true

# --- 7) PROMPT + ALIASES ---
(( $+commands[starship] )) && eval "$(starship init zsh)" || PROMPT='%F{green}%n@%m%f %F{blue}%~%f %# '
alias lls='eza --icons=auto --group-directories-first'
alias lll='eza -l --icons=auto --git'
alias lla='eza -la --icons=auto --git'
alias c='clear'
alias reload='exec zsh -l'
alias g='git'
alias gs='git status -sb'
alias ga='git add'
alias gc='git commit'

[ -s "$HOME/.bun/_bun" ] && source "$HOME/.bun/_bun"
[[ "$TERM_PROGRAM" == "vscode" ]] &&. "$(code --locate-shell-integration-path zsh 2>/dev/null || code-insiders --locate-shell-integration-path zsh 2>/dev/null)" || true

# --WCGW_ENVIRONMENT_START--
if [ -n "$IN_WCGW_ENVIRONMENT" ]; then
 PROMPT_COMMAND='printf "◉ $(pwd)──➤ \r\e[2K"'
 prmptcmdwcgw() { eval "$PROMPT_COMMAND" }
 add-zsh-hook -d precmd prmptcmdwcgw
 precmd_functions+=prmptcmdwcgw
fi
# --WCGW_ENVIRONMENT_END--


# === sovereign benchmark timer (source) ===
[ -f "$HOME/.sov_timer.zsh" ] && source "$HOME/.sov_timer.zsh"
export DISPLAY=:0
export WAYLAND_DISPLAY=wayland-1
export XDG_SESSION_TYPE=wayland
. "/home/toxic/.deno/env"
# Initialize zsh completions (added by deno install script)
autoload -Uz compinit
compinit
# Firefox + Hyprland Environment Variables
export MOZ_ENABLE_WAYLAND=1
export MOZ_DISABLE_RDD_SANDBOX=1
export __GLX_VENDOR_LIBRARY_NAME=nvidia
export __GL_VRR_ALLOWED=0
export HYPRLAND_INSTANCE_SIGNATURE=${HYPRLAND_INSTANCE_SIGNATURE:-}
export XDG_SESSION_TYPE=wayland
export DISPLAY=:0
export WAYLAND_DISPLAY=wayland-1

