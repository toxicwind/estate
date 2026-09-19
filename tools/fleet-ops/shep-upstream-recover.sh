#!/usr/bin/env bash
# shep-upstream-recover.sh — 31485d4e recovery recipes.
# Reinstalls the three shep upstreams that failed with MCPX_STDIO_SPAWN_ENOENT
# (missing launch binaries, 2026-09-19). Idempotent: safe to re-run.
# No credentials here: ghas-mcp authenticates via env or the gh CLI store.
set -euo pipefail
BIN="${HOME}/.local/bin"
mkdir -p "$BIN"

echo "--- ast-grep-xray (uv tool install xray 0.6.1) ---"
if [ -x "$BIN/xray-mcp" ]; then
  echo "present: $("$BIN/xray-mcp" --version 2>/dev/null || echo ok)"
else
  uv tool install xray==0.6.1
  echo "installed xray-mcp"
fi

echo "--- codebase-memory (GitHub release binary 0.11.0) ---"
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
  (cd "$src" && git pull --ff-only 2>/dev/null || true && go build -o "$BIN/ghas-mcp" .)
  cat > "$BIN/ghas-mcp-stdio.sh" <<EOF
#!/usr/bin/env bash
# stdio launcher for ghas-mcp; auth comes from env or the gh CLI credential store.
exec $BIN/ghas-mcp "\$@"
EOF
  chmod +x "$BIN/ghas-mcp-stdio.sh"
  echo "built ghas-mcp + wrapper"
fi

echo "done. Restart shep (pitchfork restart sovereign/shep) to re-probe upstreams."
