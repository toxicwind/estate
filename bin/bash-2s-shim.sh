#!/usr/bin/env bash
# bash-2s-shim.sh — AUTO-shim the 2-second rule into agent shells.
# Sourced by ~/.bashrc (and on demand in live sessions).
#
# How it works: wraps the common CLIs agents run as bash FUNCTIONS.
# Fast subcommands (status/diff/log/ls…) exec DIRECTLY — zero overhead.
# Known-slow subcommands (push/pull/fetch/clone/test/install/build…)
# exec through run-fast (2.0s hard deadline): breach = FAILED, race a
# faster alternative instead of waiting.
#
# Bypass any single call: `command git push …` (bypasses the function).

RF="${ESTATE_RUN_FAST:-/home/toxic/estate/bin/run-fast}"
[ -x "$RF" ] || return 0
export ESTATE_RUN_FAST="$RF"

# Subcommands that routinely exceed 2s → always run-fast.
_SLOW_GIT="push pull fetch clone merge rebase submodule"
_SLOW_BUN="install add remove update test build publish link"
_SLOW_NPM="install ci update build test publish"
_SLOW_GH="repo pr release"

_shim_route() {
  # $1 = binary, $2 = subcommand ("" = route slow by default for unknown)
  local bin="$1" sub="${2:-}"
  case "$bin:$sub" in
    git:push|git:pull|git:fetch|git:clone|git:merge|git:rebase|git:submodule) return 0 ;;
    bun:install|bun:add|bun:remove|bun:update|bun:test|bun:build|bun:publish|bun:link) return 0 ;;
    npm:install|npm:ci|npm:update|npm:build|npm:test|npm:publish) return 0 ;;
    pip:install|pip3:install|uv:sync|uv:add) return 0 ;;
    gh:repo|gh:pr|gh:release) return 0 ;;
    gitleaks:git|gitleaks:detect) return 0 ;;
    codebase-memory:*) return 0 ;;
    *) return 1 ;;
  esac
}

# Install WRAPPERS NAMED LIKE THE BINARY (functions shadow binaries in both
# interactive and non-interactive shells; aliases do not expand non-interactively).
for _bin in git bun npm pip pip3 uv gh gitleaks codebase-memory; do
  eval "${_bin}() {
    local sub=\"\$1\"; shift || true
    if _shim_route \"${_bin}\" \"\$sub\"; then
      \"\$RF\" \"${_bin}\" \"\$sub\" \"\$\@\"   # slow path: 2s cap, live streaming
    else
      command \"${_bin}\" \"\$sub\" \"\$\@\"      # fast path: direct exec
    fi
  }"
done
export -f _shim_route git bun npm pip pip3 uv gh gitleaks codebase-memory 2>/dev/null
unset _bin

export BASH_2S_SHIM=1
