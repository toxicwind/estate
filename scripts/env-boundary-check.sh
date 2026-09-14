#!/usr/bin/env bash
# ── PROTOTYPE ─────────────────────────────────────────────────────────────
# mise/direnv boundary check: fail loudly when a .envrc manages a runtime
# that mise also manages in the same scope (the unsupported combo per
# mise.jdx.dev/direnv, e.g. direnv `layout python` alongside mise python;
# real-world fallout: jdx/mise#70 PATH wipe, #2362 random venv deactivation).
#
# direnv lane (allowed): plain `export`s, dotenv loading, project-local PATH
# additions that do not overlap mise shims.
# mise lane: tool versions, shims, tasks, [daemons], [vars], sovereign [env].
#
# NOT FINAL: boundary rules are held pending the direnv/mise investigator's
# findings. Prototype for local verification only — not wired into CI/doctor.
# ─────────────────────────────────────────────────────────────────────────
set -euo pipefail

ROOT="${1:-/home/toxic}"
GLOBAL_MISE="$HOME/.config/mise/config.toml"
FAIL=0

# tool keys from a mise [tools] section (best-effort TOML scan)
mise_tools_in() { # $1 = file
  [ -f "$1" ] || return 0
  sed -n '/^\[tools\]/,/^\[/p' "$1" 2>/dev/null \
    | rg -N '^[A-Za-z0-9_.-]+[[:space:]]*=' \
    | sed 's/[[:space:]]*=.*//' || true
}

global_tools="$(mise_tools_in "$GLOBAL_MISE")"

# nearest mise.toml files walking up from $1 to $ROOT
scope_tools() { # $1 = dir
  d="$1"
  while true; do
    mise_tools_in "$d/mise.toml"
    mise_tools_in "$d/.mise.toml"
    [ "$d" = "$ROOT" ] && break
    nd="$(dirname "$d")"
    [ "$nd" = "$d" ] && break
    case "$d" in "$ROOT"*) ;; *) break ;; esac
    d="$nd"
  done
}

manages() { # $1 = tool, $2+ = tools list (newline separated)
  tool="$1"; shift
  printf "%s\n" "$@" | rg -q -x -- "$tool"
}

check_file() { # $1 = .envrc path
  f="$1"
  # shellcheck disable=SC2207
  tools=( $global_tools $(scope_tools "$(dirname "$f")") )
  hit=0
  pat_tool() { # $1 = rg pattern, $2 = mise tool name
    if rg -q -N -- "$1" "$f"; then
      if manages "$2" "${tools[@]}"; then
        printf "FAIL  %s: matches [%s] but mise also manages [%s] in scope\n" "$f" "$1" "$2"
        hit=1
      else
        printf "ok    %s: matches [%s]; mise does not manage [%s] here (direnv owns it)\n" "$f" "$1" "$2"
      fi
    fi
  }
  pat_tool "^[[:space:]]*layout[[:space:]]+python" "python"
  pat_tool "^[[:space:]]*layout[[:space:]]+node" "node"
  pat_tool "^[[:space:]]*layout[[:space:]]+conda" "conda"
  pat_tool "^[[:space:]]*use[[:space:]]+mise" "mise"
  if rg -q -N -- "(source|\.)[[:space:]]+[^;#]*bin/activate([[:space:]]|$|;)" "$f"; then
    if manages "python" "${tools[@]}"; then
      printf "FAIL  %s: venv activation while mise manages [python] in scope\n" "$f"
      hit=1
    else
      printf "ok    %s: venv activation; mise does not manage [python] here\n" "$f"
    fi
  fi
  if [ "$hit" -eq 0 ]; then
    if command -v direnv >/dev/null 2>&1; then
      printf "pass  %s: no tool-management conflicts\n" "$f"
    else
      printf "pass  %s: no tool-management conflicts (direnv not installed: inert here)\n" "$f"
    fi
  fi
  return "$hit"
}

found=0
while IFS= read -r envrc; do
  found=1
  if ! check_file "$envrc"; then FAIL=1; fi
done < <(fd -H -t f '^\.envrc$' "$ROOT" --max-depth 6 \
  -E 'nix/store' -E 'registry/src' -E 'git/checkouts' -E '.git/' 2>/dev/null)

[ "$found" -eq 1 ] || printf "info  no .envrc files found under %s\n" "$ROOT"
if [ "$FAIL" -eq 0 ]; then
  printf "BOUNDARY OK: no .envrc manages a mise-managed runtime\n"
else
  printf "BOUNDARY VIOLATIONS FOUND (see FAIL lines above)\n" >&2
fi
exit "$FAIL"
