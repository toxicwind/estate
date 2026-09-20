#!/usr/bin/env bash
# fix-tau-omp.sh — maximal repair for tau/omp "command not found" + dotfile anomalies
# Target: awrawr-pc (Arch/CachyOS, user toxic).
# Copy-paste safe: no nested heredocs. Backs up every touched file to
# ~/.dotfile-bak-<timestamp>/. Idempotent — safe to re-run.
# Usage:  bash fix-tau-omp.sh
# Then:   exec bash -l   (or just reconnect ssh)

set -euo pipefail

TS="$(date +%Y%m%d-%H%M%S)"
BAK="$HOME/.dotfile-bak-$TS"
mkdir -p "$BAK"
echo "== backups -> $BAK"

pass=0; fail=0
ok() { pass=$((pass+1)); echo "PASS: $1"; }
no() { fail=$((fail+1)); echo "FAIL: $1"; }
backup() {
  if [ -f "$1" ]; then
    cp -p "$1" "$BAK/$(basename "$1").bak"
    echo "   backed up $1"
  fi
}

echo "== [1/8] login shells (ssh, cockpit, bash -l) must source .bashrc"
if [ -f "$HOME/.bash_profile" ]; then
  ok "~/.bash_profile already exists"
else
  printf '%s\n' '# fix-tau-omp.sh: login shells must load .bashrc' \
    '[ -f "$HOME/.bashrc" ] && . "$HOME/.bashrc"' > "$HOME/.bash_profile"
  ok "created ~/.bash_profile"
fi

echo "== [2/8] split concatenated exports (missing newlines)"
for f in "$HOME/.bashrc" "$HOME/.secrets" "$HOME/.config/claude/env"; do
  [ -f "$f" ] || continue
  if grep -qE '[^ ]export [A-Za-z_][A-Za-z0-9_]*=' "$f"; then
    backup "$f"
    sed -i -E 's/([^ ])export ([A-Za-z_][A-Za-z0-9_]*=)/\1\nexport \2/g' "$f"
    echo "   fixed: $f"
  fi
done
left=0
for f in "$HOME/.bashrc" "$HOME/.secrets" "$HOME/.config/claude/env"; do
  [ -f "$f" ] || continue
  n=$(grep -cE '[^ ]export [A-Za-z_][A-Za-z0-9_]*=' "$f" 2>/dev/null || true)
  n=${n:-0}
  left=$((left + n))
done
[ "$left" -eq 0 ] && ok "no concatenated exports remain" || no "$left concatenated exports remain"

echo "== [3/8] repair tau.sh line break (stray 'set' / '+a' lines)"
TSH="$HOME/.local/bin/tau.sh"
if [ -f "$TSH" ]; then
  if grep -qE '^[+]a[[:space:]]*$' "$TSH"; then
    backup "$TSH"
    sed -i 's/&& set[[:space:]]*$/&& set +a/' "$TSH"
    sed -i -E '/^[+]a[[:space:]]*$/d' "$TSH"
    echo "   fixed: $TSH"
  fi
  grep -qE '^[+]a[[:space:]]*$' "$TSH" && no "tau.sh still has a lone +a line" || ok "tau.sh repaired"
else
  echo "   skip: $TSH not present"
fi

echo "== [4/8] remove PATH shadows, ensure real shims"
BT="$HOME/.bun/bin/tau"
if [ -L "$BT" ]; then
  rm -f "$BT"
  echo "   removed shadow symlink $BT (-> directory, shadowed the launcher)"
fi
TAU="$HOME/.local/bin/tau"
if [ -f "$TAU" ]; then
  chmod +x "$TAU"
  ok "~/.local/bin/tau present and executable"
  # real symlinks beat aliases: aliases do not expand in scripts / non-interactive shells
  for n in omp pi; do
    ln -sfn "$TAU" "$HOME/.local/bin/$n"
  done
  ok "~/.local/bin/omp and ~/.local/bin/pi symlinked to tau"
else
  no "~/.local/bin/tau missing — restore it before creating shims"
fi

echo "== [5/8] drop redundant aliases appended past ble-attach"
BR="$HOME/.bashrc"
if grep -qE '^alias (omp|pi)=tau$' "$BR"; then
  backup "$BR"
  sed -i -E '/^alias (omp|pi)=tau$/d' "$BR"
  ok "removed redundant aliases (symlinks cover it, everywhere)"
else
  ok "no redundant aliases"
fi

echo "== [6/8] fix phantom engine/ segment in launcher ENGINE_ENTRY"
if [ -f "$TAU" ] && grep -q 'sovereign/tau/engine/packages' "$TAU"; then
  backup "$TAU"
  sed -i 's|sovereign/tau/engine/packages|sovereign/tau/packages|' "$TAU"
  ok "ENGINE_ENTRY now -> sovereign/tau/packages/... (matches toxicwind/tau layout on GitHub)"
elif [ -f "$TAU" ]; then
  ok "ENGINE_ENTRY already patched"
fi

echo "== [7/8] materialize the tau tree + deps (best effort)"
if [ ! -d "$HOME/sovereign/tau" ]; then
  if git clone https://github.com/toxicwind/tau.git "$HOME/sovereign/tau" 2>&1 | tail -2; then
    ok "cloned toxicwind/tau -> ~/sovereign/tau"
  else
    no "git clone failed (repo may be private — use an authenticated remote or copy the tree manually)"
  fi
else
  ok "~/sovereign/tau already exists"
fi
CA="$HOME/sovereign/tau/packages/coding-agent"
if [ -f "$CA/package.json" ] && [ ! -d "$CA/node_modules" ] && command -v bun >/dev/null 2>&1; then
  echo "   running bun install in packages/coding-agent (may take a bit)..."
  if (cd "$CA" && bun install >/dev/null 2>&1); then
    ok "bun install done"
  else
    no "bun install failed — run it manually in $CA"
  fi
fi

echo "== [8/8] verify in a fresh LOGIN shell (exactly what ssh/cockpit get)"
if bash -l -c 'command -v tau >/dev/null && command -v omp >/dev/null && command -v pi >/dev/null'; then
  ok "login shell resolves tau, omp, pi:"
  bash -l -c 'command -v tau; command -v omp; command -v pi'
else
  no "login shell still cannot resolve tau/omp/pi"
fi

echo
echo "== launching tau once (should NOT say 'command not found' anymore)"
bash -l -c 'tau --version' 2>&1 | head -3 || true

echo
echo "== result: $pass passed, $fail failed =="
echo "Backups in: $BAK"
echo "Next: run 'exec bash -l' (or reconnect ssh) to load the fixed environment."
echo "Left alone (harmless): unquoted '!' in NITRADO_PASSWORD (followed by space, no history expansion),"
echo "missing ble.sh / starship.toml / mise config (all guarded in .bashrc)."
