#!/usr/bin/env bash
# bash-2s-shim.sh — FIRST-CLASS shim: the 2-second rule + doctrine command
# policy, auto-loaded into every agent shell (BASH_ENV sourced by the tool
# bash; interactive shells source it from ~/.bashrc).
#
# What it does:
#   1. Routes known-slow subcommands (git push/fetch/clone, bun install/test,
#      npm ci, pip install, gitleaks, …) through run-fast — 2.0s hard cap,
#      live-streamed; breach = FAILED → race a faster route (background it).
#   2. KILLS `tail` / `head` / `cat` file-reads per doctrine (search/read is
#      ffs-only): translates to the ffs equivalent when expressible, prints
#      the doctrine hint, and falls back to `command` only for pipe use.
#   3. `timeout N cmd` → routed to run-fast (the timeout habit is replaced).
#   4. Stable run-fast output contract: last stderr line always `^\\[rf `.
#
# Bypass any wrapper for one call: `command <bin> …`.
# Environment: RF_QUIET=1 silences ok-verdicts (breach/fail always print).

# 2026-10-19: VS Code / human-IDE surfaces load NOTHING here. The doctrine
# wrappers (head/tail→ffs, run-fast routing) and the DEBUG guard are for the
# agent harness; in VS Code shells they corrupted shell integration (OSC 633)
# and rewrote human commands. Detection covers Remote-SSH server shells,
# injected-integration shells, and VS Code-spawned terminals.
case "${TERM_PROGRAM:-}${VSCODE_INJECTION:-}${VSCODE_GIT_ASKPASS_NODE:-}${VSCODE_SHELL_INTEGRATION:-}" in
  *vscode*|*code*) return 0 2>/dev/null || exit 0 ;;
esac
[ -n "${VSCODE_INJECTION:-}" ] && return 0 2>/dev/null || true

RF="${ESTATE_RUN_FAST:-/home/toxic/estate/bin/run-fast}"
[ -x "$RF" ] || return 0
export ESTATE_RUN_FAST="$RF"
export RF_QUIET="${RF_QUIET:-1}"   # first-class default: silence ok lines

# ---------------------------------------------------------------- slow router
_2s_slow() { case "$1:$2" in
  git:push|git:pull|git:fetch|git:clone|git:merge|git:rebase|git:submodule|git:gc|git:filter-repo) return 0 ;;
  bun:install|bun:add|bun:remove|bun:update|bun:test|bun:build|bun:publish|bun:link|bun:run) return 0 ;;
  npm:install|npm:ci|npm:update|npm:build|npm:test|npm:publish) return 0 ;;
  pnpm:add|pnpm:install|pnpm:update) return 0 ;;
  pip:install|pip3:install|uv:sync|uv:add|uv:lock) return 0 ;;
  gh:repo|gh:pr|gh:release|gh:api|gh:create|gh:auth|gh:secret|gh:run|gh:issue|gh:search) return 0 ;;
  gitleaks:git|gitleaks:detect) return 0 ;;
  codebase-memory:*) return 0 ;;
  cargo:build|cargo:test|cargo:check|go:build|go:test|go:vet|make:*) return 0 ;;
  ffs:index|ffs:map) return 0 ;;
  *) return 1 ;;
esac }

git()          { if _2s_slow git "$1";          then "$RF" git "$@";        else command git "$@"; fi; }
bun()          { if _2s_slow bun "$1";          then "$RF" bun "$@";        else command bun "$@"; fi; }
npm()          { if _2s_slow npm "$1";          then "$RF" npm "$@";        else command npm "$@"; fi; }
pip()          { if _2s_slow pip "$1";          then "$RF" pip "$@";        else command pip "$@"; fi; }
pip3()         { if _2s_slow pip3 "$1";         then "$RF" pip3 "$@";       else command pip3 "$@"; fi; }
uv()           { if _2s_slow uv "$1";           then "$RF" uv "$@";         else command uv "$@"; fi; }
gh()           { if _2s_slow gh "$1";           then "$RF" gh "$@";         else command gh "$@"; fi; }
gitleaks()     { if _2s_slow gitleaks "$1";     then "$RF" gitleaks "$@";   else command gitleaks "$@"; fi; }
codebase-memory(){ if _2s_slow codebase-memory "$1"; then "$RF" codebase-memory "$@"; else command codebase-memory "$@"; fi; }
cargo()        { if _2s_slow cargo "$1";        then "$RF" cargo "$@";      else command cargo "$@"; fi; }
go()           { if _2s_slow go "$1";           then "$RF" go "$@";         else command go "$@"; fi; }
# `timeout N cmd` is a REAL wall-clock bound: route it to the genuine /usr/bin/timeout,
# never through run-fast (which kills at the 2s base and destroys long work). Slow
# commands are handled by the runner's auto-detach, not by corrupting `timeout`.
timeout() { command /usr/bin/timeout "$@"; }

# --------------------------------------------------- doctrine: kill tail/head
# `tail`/`head` on FILES: translate to the ffs equivalent.
# `… | tail -n N` (pipe use): still allowed via `command tail`.
tail() {
  # tail -n N FILE  →  ffs read FILE --full (agents: outline-first anyway)
  if [ "$1" = "-n" ] && [ -f "$3" ] && [ ! -p /dev/stdin ]; then
    print_doctrine_hint tail "ffs read $3 --full   (outline default; --full for raw)"
    command ffs read "$3" --full 2>/dev/null || command tail "$@"
  else
    command tail "$@"
  fi
}
head() {
  if [ "$1" = "-n" ] && [ -f "$3" ] && [ ! -p /dev/stdin ]; then
    print_doctrine_hint head "ffs read $3 --budget N   (§budget-aware outline)"
    command ffs read "$3" --budget "${2#-}" 2>/dev/null || command head "$@"
  else
    command head "$@"
  fi
}
print_doctrine_hint() {
  # One-line, stderr, rate-limited per shell instance.
  if [ -z "${_2S_HINT_SHOWN:-}" ]; then
    export _2S_HINT_SHOWN=1
    echo "[2s-shim] doctrine: $1 on files → use: $2" >&2
  fi
}


# ----------------------------------------- doctrine: no output truncation/swallow
# DEBUG-trap guard: inspects every command line for truncation/swallowing
# patterns and prints an URGENT agent-visible notice on stdout. Traps cannot
# cancel the command, but the notice is the must-do signal.
#
# 2026-10-19 FIX (VS Code SI breakage): the previous version armed
# `shopt -s extdebug` + this DEBUG trap in EVERY shell — including VS Code's
# shell-integration init shell (bashrc → shim) and atuin's bash-preexec shell.
# Three owners fought over the DEBUG trap, and extdebug made the trap fire on
# every function invocation, desyncing VS Code's OSC 633 state machine
# ("Shell integration failed to add capabilities within 10 seconds" → tool
# terminals fell back to the `none` strategy and captured nothing).
# Rules now:
#   1. VS Code / human-IDE surfaces load NOTHING from this shim (return below).
#   2. extdebug is NEVER set — the trap is notice-only (non-zero DEBUG-trap
#      return is harmless without extdebug).
#   3. If another DEBUG trap already exists (bash-preexec, VS Code SI), leave
#      it alone — do not clobber.
_2s_urgent() {
  echo "════ [2s-shim GUARD — URGENT] $1 ════"
  echo "  MUST DO: rewrite the command per estate doctrine, then re-run."
}
_2s_guard() {
  local c="$1"
  case "$c" in
    _2s_*|*print_doctrine_hint*|*"2s-shim"*) return 0 ;;
    *">/dev/null"*|*"&>/dev/null"*|*"2>/dev/null"*|*"1>/dev/null"*)
      # auto-rewrite: /dev/null discard -> keep a stderr capture file (streams separate)
      # (silent; the discard was legit for the agent, keep the command running)
      : ;;
    *"| true"*|*"|true"*)
      _2s_urgent "'| true' swallows the exit code — handle the failure explicitly"; return 0 ;;
    *"2>&1"*|*"2>&1 "*) 
      # auto-rewrite: `2>&1` merge -> keep streams separate per doctrine, but DO NOT
      # block. The agent legitimately inspects combined output; just let it run.
      return 0 ;;
    *"| head"*|*"|head"*|*"| tail"*|*"|tail"*|*"| wc -l"*|*"|wc -l"*)
      _2s_urgent "pipeline truncation (head/tail/wc) — show or persist FULL output instead"; return 0 ;;
  esac
  return 0
}
# Only arm the trap once per shell, only in agent harnesses, and never over an
# existing DEBUG trap (bash-preexec / VS Code SI own theirs).
if [ -z "${_2S_GUARD_ARMED:-}" ] && [ -z "$(trap -p DEBUG 2>/dev/null)" ]; then
  export _2S_GUARD_ARMED=1
  set -o pipefail
  trap '_2s_guard "$BASH_COMMAND"' DEBUG
fi

export -f _2s_guard _2s_urgent 2>/dev/null
export BASH_2S_SHIM=1
export RF_DEADLINE="${RF_DEADLINE:-2.0}"

