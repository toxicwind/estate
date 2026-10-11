#!/usr/bin/env bash
# shep-upstream-recover.sh — 31485d4e recovery recipes.
# Reinstalls the three shep upstreams that failed with MCPX_STDIO_SPAWN_ENOENT
# (missing launch binaries, 2026-09-19). Idempotent: safe to re-run.
# No credentials here: ghas-mcp authenticates via env or the gh CLI store.
set -euo pipefail
BIN="${HOME}/.local/bin"
mkdir -p "$BIN"

echo "--- ast-grep-xray (uv tool install from local source) ---"
# PROVEN PATH (2026-09-19): PyPI `xray==0.6.1` ships NO xray-mcp entrypoint —
# `uv tool install xray==0.6.1` fails with "No executables are provided by
# package `xray`". The live box installs from the local source checkout,
# whose pyproject declares [project.scripts] xray-mcp.
XRAY_SRC="/home/toxic/projects/ast-grep-mcps/xray"
if [ -x "$BIN/xray-mcp" ]; then
  echo "present: $("$BIN/xray-mcp" --version 2>/dev/null || echo ok)"
elif [ -d "$XRAY_SRC" ]; then
  uv tool install "$XRAY_SRC"
  echo "installed xray-mcp from local source"
else
  echo "ERROR: xray source missing at $XRAY_SRC and PyPI xray has no xray-mcp entrypoint; cannot recover" >&2
  exit 1
fi

echo "--- codebase-memory (GitHub release binary 0.11.0) ---"
# Validated 2026-09-19: asset codebase-memory-mcp-linux-amd64.tar.gz exists
# under DeusData/codebase-memory-mcp releases tag v0.11.0.
if [ -x "$BIN/codebase-memory-mcp" ]; then
  echo "present: $("$BIN/codebase-memory-mcp" --version 2>/dev/null || echo ok)"
else
  tmp="$(mktemp -d)"
  curl -fsSL -o "$tmp/cbm.tar.gz" \
    "https://github.com/DeusData/codebase-memory-mcp/releases/download/v0.11.0/codebase-memory-mcp-linux-amd64.tar.gz"
  tar -xzf "$tmp/cbm.tar.gz" -C "$tmp"
  install -m755 "$tmp/codebase-memory-mcp" "$BIN/codebase-memory-mcp"
  rm -rf "$tmp"
  echo "installed codebase-memory-mcp 0.11.0"
fi

echo "--- ghas (build from source github.com/dipsylala/ghas-mcp) ---"
if [ -x "$BIN/ghas-mcp" ] && [ -x "$BIN/ghas-mcp-stdio.sh" ]; then
  echo "present: binary + stdio wrapper"
else
  src="${HOME}/build/ghas-mcp"
  [ -d "$src/.git" ] || git clone https://github.com/dipsylala/ghas-mcp "$src"
  # Never mask pull failures: a stale checkout aborts loudly instead of
  # building silently from old sources.
  (cd "$src" && git pull --ff-only) || { echo "ERROR: git pull --ff-only failed in $src; refusing to build from a stale checkout" >&2; exit 1; }
  (cd "$src" && go build -o "$BIN/ghas-mcp" .)
  cat > "$BIN/ghas-mcp-stdio.sh" <<EOF
#!/usr/bin/env bash
# ghas-mcp stdio launcher for shep.
# No secrets here: ghas-mcp resolves auth as GITHUB_TOKEN env,
# else \`gh auth token\` (gh CLI session on this box).
set -euo pipefail
exec $BIN/ghas-mcp "\$@"
EOF
  chmod +x "$BIN/ghas-mcp-stdio.sh"
  echo "built ghas-mcp + wrapper"
fi

echo "done. Restart shep (pitchfork restart sovereign/shep) to re-probe upstreams."
