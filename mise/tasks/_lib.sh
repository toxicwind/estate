set -euo pipefail
export SOV="${SOVEREIGN_ROOT:-$PWD}"
cd "$SOV"

# Map module names → stack/modules/<name>.yaml (+ base)
pc_args() {
  local a=("$SOV/stack/base.yaml")
  local m
  for m in "$@"; do
    local f="$SOV/stack/modules/${m}.yaml"
    if [[ ! -f "$f" ]]; then
      echo "missing module: $f" >&2
      return 1
    fi
    a+=("$f")
  done
  printf '%s\n' "${a[@]}"
}

# Start selected modules only (not the full generated mega-compose dump).
# Port 25108 = process-compose API (SSOT in .env.local PROCESS_COMPOSE_PORT if set).
pc_up() {
  local cfgs=()
  local l
  while IFS= read -r l; do
    cfgs+=(--config "$l")
  done < <(pc_args "$@")
  local port="${PROCESS_COMPOSE_PORT:-25108}"
  # process-compose inherits env from mise
  exec process-compose \
    --address 127.0.0.1 \
    --port "$port" \
    up "${cfgs[@]}" -D
}
