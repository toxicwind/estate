#!/usr/bin/env bash
# Whitelist-only config dedup — NO home-directory scans.
# Compares sha256 + mtime; archives stale copies; never deletes without archive.
set -euo pipefail

ARCHIVE="${HOME}/.archive/consolidation-$(date +%Y-%m-%d)"
mkdir -p "$ARCHIVE"

log() { printf '[consolidate] %s\n' "$*"; }

hash_file() { sha256sum "$1" | awk '{print $1}'; }
mtime_file() { stat -c '%Y' "$1" 2>/dev/null || echo 0; }

# path|canonical|notes
PAIRS=(
  "$HOME/.grok/config.toml|$HOME/.grok/config.toml.bak|grok MCP config"
  "$HOME/sovereign/config.toml|$HOME/sovereign/modules/nix/d/config.toml|openfang sovereign vs stale nix/d copy"
  "$HOME/.openfang/config.toml||openfang runtime (keep; differs from sovereign)"
)

archive_stale() {
  local src="$1" reason="$2"
  local dest="$ARCHIVE${src}"
  mkdir -p "$(dirname "$dest")"
  mv "$src" "$dest"
  log "archived stale: $src -> $dest ($reason)"
}

for entry in "${PAIRS[@]}"; do
  IFS='|' read -r canonical stale note <<<"$entry"
  [[ -f "$canonical" ]] || { log "skip missing canonical: $canonical"; continue; }
  [[ -n "$stale" && -f "$stale" ]] || continue

  h_can=$(hash_file "$canonical")
  h_stale=$(hash_file "$stale")
  t_can=$(mtime_file "$canonical")
  t_stale=$(mtime_file "$stale")

  if [[ "$h_can" == "$h_stale" ]]; then
    archive_stale "$stale" "identical hash to $canonical ($note)"
  elif (( t_can >= t_stale )); then
    archive_stale "$stale" "older than canonical ($note)"
  else
    log "KEEP both — stale newer than canonical? $stale ($note)"
  fi
done

# Lone stale backups without a PAIRS sibling
if [[ -f "$HOME/data_dumps/audit/devenv.nix.bak" ]]; then
  archive_stale "$HOME/data_dumps/audit/devenv.nix.bak" "devenv retired"
fi

log "Archive root: $ARCHIVE"