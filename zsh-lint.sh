#!/usr/bin/env zsh
file=${1:-$HOME/.zshrc}

echo "== $file =="

# syntax
if ! zsh -n "$file"; then
  echo "FAIL: syntax"
  exit 1
fi

# strict warnings
if ! zsh -o no_global_rcs -o no_rcs --sourcetrace -c "
  setopt WARN_CREATE_GLOBAL WARN_NESTED_VAR
  source \"$file\"
" 2>&1; then
  echo "FAIL: strict warnings"
  exit 1
fi

# compile
if ! zcompile -U "${file}.zwc" "$file"; then
  echo "FAIL: compile"
  exit 1
fi
rm -f "${file}.zwc"

echo "OK: $file"