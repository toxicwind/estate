#!/bin/bash
# estate flock SSOT. sourced by ranch/flock/bin/flock-run.sh before exec.
# Aligns the daemon client list with FLOCK_API_KEY. Does not print secrets.
set -euo pipefail
SSOT="$HOME/estate/config/flock-ssot"
set -a
[ -f "$SSOT/ports.env" ] && . "$SSOT/ports.env"
[ -f "$SSOT/route.env" ] && . "$SSOT/route.env"
[ -f "$SSOT/flock.env" ] && . "$SSOT/flock.env"
set +a
export HOST="${HOST:-127.0.0.1}"
export PORT="${PORT:-${FLOCK_PORT:-25193}}"
export FLOCK_PORT="$PORT"
export DATA_DIR="${DATA_DIR:-${FLOCK_DATA_DIR:-$HOME/.flock-data}}"
export FLOCK_BASE_URL="${FLOCK_BASE_URL:-http://127.0.0.1:${FLOCK_PORT}}"
export FLOCK_MODEL="${FLOCK_MODEL:-nvidia/nemotron-3-ultra-550b-a55b}"
export NIM_BASE_URL="${NIM_BASE_URL:-${FLOCK_BASE_URL}/v1}"
export NIM_MODEL="${NIM_MODEL:-$FLOCK_MODEL}"
export ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL:-$FLOCK_BASE_URL}"
if [ -z "${FLOCK_API_KEY:-}" ] && [ -f "$HOME/.secrets" ]; then
  FLOCK_API_KEY="$(grep -m1 '^FLOCK_API_KEY=' "$HOME/.secrets" | cut -d= -f2- || true)"
  export FLOCK_API_KEY
fi
python3 - "$DATA_DIR/config.json" << 'PY'
import hashlib, json, os, pathlib, sys
path = pathlib.Path(sys.argv[1])
key = os.environ.get("FLOCK_API_KEY", "").strip().strip('"').strip("'")
if not key or not path.exists():
    raise SystemExit(0)
cfg = json.loads(path.read_text())
users = {u.get("username") for u in cfg.get("users", []) if isinstance(u, dict)}
owner = "sovereign" if "sovereign" in users else (next(iter(users)) if users else "sovereign")
sha = hashlib.sha256(key.encode()).hexdigest()
keys = cfg.setdefault("client_auth", {}).setdefault("keys", [])
found = False
for item in keys:
    if item.get("key") == key or item.get("secret_sha256") == sha:
        item["owner"] = owner
        item["secret_sha256"] = sha
        item["last4"] = key[-4:]
        item.setdefault("name", "estate")
        found = True
        break
if not found:
    keys.append({"name": "estate", "secret_sha256": sha, "last4": key[-4:], "owner": owner, "key": key})
path.write_text(json.dumps(cfg, indent=2) + "\n")
path.chmod(0o600)
PY
