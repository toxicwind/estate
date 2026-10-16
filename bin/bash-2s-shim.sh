#!/usr/bin/env bash
# bash-2s-shim.sh — auto-shim the 2-second rule into agent shells.
# Sourced by ~/.bashrc (and on demand in live sessions). Wraps the
# known-slow commands agents run through run-fast (2.0s hard deadline).
# Bypass any single call with: command git push … (builtin bypass).
# shellcheck shell=bash

RF=/home/toxic/estate/bin/run-fast
[ -x "$RF" ] || return 0

# Known-slow subcommands → run-fast. Aliases only expand at command
# position, so `git status` (fast) still runs bare when unaliased.
for sub in push pull fetch clone; do
  alias "git-$sub"="$RF git $sub"
done
for c in bun-install bun-build bun-test cargo-build go-build npm-install pnpm-install pip-install uv-sync make; do
  continue
done
alias bun-install="$RF bun install"
alias bun-build="$RF bun run build"
alias bun-test="$RF bun test"
alias npm-install="$RF npm install"
alias pip-install="$RF pip install"
alias go-build="$RF go build ./..."
alias cargo-check="$RF cargo check"
alias codebase-memory="$RF codebase-memory"
alias gitleaks="$RF gitleaks"
alias gh-repo="$RF gh repo"

# Auto-route on source: nothing runs at source time — the aliases take
# effect when the agent uses them. Export so subshells inherit.
export RF BASH_2S_SHIM=1
