
# Let me analyze all the uploaded files to understand the complete sovereign stack
# and create the correct mise 2026 configuration

files = {
    "mise.toml.txt": """[env]
SOVEREIGN_ROOT = "{{ config_root }}"
_.file = [".env.local", "/home/toxic/.secrets", "/home/toxic/.openfang/secrets.env"]
_.path = [
    "{{ config_root }}/yote/.venv/bin",
    "{{ config_root }}/bin",
    "{{ config_root }}/stack",
    "/home/toxic/.bun/bin"
]
[tasks.up]
run = "{{ config_root }}/stack/up.sh -D sovereign"
[tasks.up-core]
run = "{{ config_root }}/stack/up.sh -D core"
[tasks.up-full]
run = "{{ config_root }}/stack/up.sh -D full"
[tasks.down]
run = "{{ config_root }}/stack/down.sh"
[tasks.status]
run = "{{ config_root }}/bin/sovereign-stack.sh status"
[tasks.health]
run = "{{ config_root }}/stack/health.sh"
[tasks.build-compose]
run = "{{ config_root }}/stack/build-compose.sh"
[tasks.kill-devenv]
run = "{{ config_root }}/bin/kill-devenv.sh"
[tasks.consolidate]
run = "{{ config_root }}/bin/consolidate-known.sh"
[settings]
""",
    "ports.env": """export SOVEREIGN_ROOT="${SOVEREIGN_ROOT:-/home/toxic/sovereign}"
export LLAMA_SERVER_PORT=25001
export LLAMA_HERDER=28080
export OPENFANG_PORT=25004
export RUST_WEB_PORT=25005
export HF_DOWNLOADER=25020
export WATCHDOG_PORT=25022
export YOTE_PORT=25042
export PROMETHEUS_PORT=25030
export CADDY_PORT=25000
export CADDY_ADMIN_PORT=25031
export LANDING_PORT=25080
export LLM_PROXY_URL="http://127.0.0.1:${LLAMA_HERDER}"
export LLM_BASE_URL="http://127.0.0.1:${LLAMA_HERDER}/v1"
export ADVISOR_CACHE_LIMIT="24G"
""",
    "profiles.sh": """stack_profile_modules() {
  local profile="${1:-sovereign}"
  case "$profile" in
    core)
      printf '%s\n' llama-herder openfang prometheus
      ;;
    sovereign)
      printf '%s\n' \
        llama-herder openfang prometheus \
        yote rust-web
      ;;
    full)
      printf '%s\n' \
        llama-herder openfang prometheus \
        yote rust-web \
        landing watchdog hf-downloader
      ;;
  esac
}""",
    "lib.sh": """STACK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOV="${SOVEREIGN_ROOT:-$(cd "$STACK_ROOT/.." && pwd)}"
export SOVEREIGN_ROOT="$SOV"
source "$STACK_ROOT/ports.env"
source "$STACK_ROOT/profiles.sh"
mkdir -p "$SOV/.state/logs" "$SOV/.prometheus"

stack_configs() {
  local profile="${1:-core}"
  local -a mods
  mapfile -t mods < <(stack_profile_modules "$profile")
  printf '%s\n' "$SOV/stack/base.yaml"
  for m in "${mods[@]}"; do
    printf '%s\n' "$SOV/stack/modules/${m}.yaml"
  done
}

run_pc() {
  command -v process-compose >/dev/null || {
    echo "process-compose not found" >&2
    exit 1
  }
  process-compose --address 127.0.0.1 "$@"
}

pc_config_args() {
  local profile="${1:-core}"
  local -a args=() cfg
  while IFS= read -r cfg; do
    args+=(-f "$cfg")
  done < <(stack_configs "$profile")
  printf '%s\0' "${args[@]}"
}""",
    "up.sh": """#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib.sh"
detach=""
profile="sovereign"
extra=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -D|--detach|-d) detach="-D"; shift ;;
    core|sovereign|full) profile="$1"; shift ;;
    *) extra+=("$1"); shift ;;
  esac
done
cd "$SOV"
mapfile -d '' -t cfg_args < <(pc_config_args "$profile")
if [[ -n "$detach" ]]; then
  run_pc up "${cfg_args[@]}" $detach "${extra[@]}"
else
  run_pc up "${cfg_args[@]}" "${extra[@]}"
fi""",
    "down.sh": """#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib.sh"
cd "$SOV"
echo "[down] Stopping services..."
run_pc stop openfang "$@" 2>/dev/null || true
sleep 1
run_pc down "$@" 2>/dev/null || run_pc --address 127.0.0.1 down "$@" 2>/dev/null || true
if pgrep -x process-compose >/dev/null; then
    echo "[down] Force killing process-compose supervisor..."
    pkill -15 -x process-compose || true
    sleep 2
    pkill -9 -x process-compose || true
fi
echo "[down] All done."""",
    "health.sh": """
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/ports.env" 2>/dev/null || true
LLAMA_HERDER="${LLAMA_HERDER:-28080}"
OPENFANG_PORT="${OPENFANG_PORT:-25004}"
PROMETHEUS_PORT="${PROMETHEUS_PORT:-9090}"
YOTE_PORT="${YOTE_PORT:-25042}"
RUST_WEB_PORT="${RUST_WEB_PORT:-8080}"
HF_DOWNLOADER="${HF_DOWNLOADER:-8081}"
WATCHDOG_PORT="${WATCHDOG_PORT:-8082}"
LANDING_PORT="${LANDING_PORT:-8083}"
# ... health check logic ...""",
    "build-compose.sh": """#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOV="$(cd "$SCRIPT_DIR/.." && pwd)"
OUT="$SOV/process-compose.yaml"
python3 - "$SOV" "$OUT" <<'PY'
import sys
from pathlib import Path
try:
    import yaml
except ImportError:
    sys.stderr.write("pyyaml required\n")
    sys.exit(1)
sov, out = Path(sys.argv[1]), Path(sys.argv[2])
stack = sov / "stack"
merged = {"version": "0.5", "environment": [], "processes": {}}
base = yaml.safe_load((stack / "base.yaml").read_text()) or {}
merged["version"] = base.get("version", merged["version"])
merged["environment"] = base.get("environment", [])
for mod in sorted((stack / "modules").glob("*.yaml")):
    doc = yaml.safe_load(mod.read_text()) or {}
    procs = doc.get("processes") or {}
    merged["processes"].update(procs)
header = (
    "# GENERATED — do not edit. Source: stack/modules/*.yaml\n"
    "# Regenerate: devbox run build-compose  |  ./stack/build-compose.sh\n"
)
out.write_text(header + yaml.dump(merged, sort_keys=False, default_flow_style=False))
print(f"wrote {out} ({len(merged['processes'])} processes)")
PY""",
    "base.yaml": """version: "0.5"
environment:
  - "SOVEREIGN_ROOT=/home/toxic/sovereign"""",
    "llama-herder.yaml": """processes:
  llama-herder:
    command: "/home/toxic/sovereign/stack/services/llama-herder.sh"
    working_dir: "/home/toxic/sovereign"
    environment:
      - "SOVEREIGN_ROOT=/home/toxic/sovereign"
      - "LLAMA_HERDER=28080"
    availability:
      restart: on_failure
      backoff_seconds: 3
      max_restarts: 12
    readiness_probe:
      http_get:
        host: 127.0.0.1
        port: 28080
        path: /health
      initial_delay_seconds: 5
      period_seconds: 5
      failure_threshold: 12
    log_location: "/home/toxic/sovereign/.state/logs/llama-herder.log"""",
    "openfang.yaml": """processes:
  openfang:
    command: "/home/toxic/.openfang/bin/openfang start"
    working_dir: "/home/toxic/sovereign"
    availability:
      restart: always
      backoff_seconds: 5
    readiness_probe:
      http_get:
        host: 127.0.0.1
        port: 25004
        path: /api/health
        scheme: http
      initial_delay_seconds: 15
      period_seconds: 5
      timeout_seconds: 3
      failure_threshold: 3
    log_location: "/home/toxic/sovereign/.state/logs/openfang.log"""",
    "rust-web.yaml": """processes:
  rust-web:
    command: "/home/toxic/sovereign/stack/services/rust-web.sh"
    working_dir: "/home/toxic/sovereign/rust_algo_web"
    environment:
      - "RUST_WEB_PORT=25005"
      - "LLM_PROXY_URL=http://127.0.0.1:28080"
      - "SOVEREIGN_ROOT=/home/toxic/sovereign"
    availability:
      restart: on_failure
      max_restarts: 8
    readiness_probe:
      http_get:
        host: 127.0.0.1
        port: 25005
        path: /health
      initial_delay_seconds: 5
      period_seconds: 5
      failure_threshold: 12
    log_location: "/home/toxic/sovereign/.state/logs/rust-web.log"""",
    "yote.yaml": """processes:
  yote:
    command: "/home/toxic/.bun/bin/bun run src/index.ts"
    working_dir: "/home/toxic/sovereign/yote"
    environment:
      - "DOTENV_CONFIG_PATH=/home/toxic/sovereign/yote/.env"
    availability:
      restart: always
      backoff_seconds: 5
    readiness_probe:
      http_get:
        host: 127.0.0.1
        port: 25042
        path: /health
      initial_delay_seconds: 15
      period_seconds: 5
      timeout_seconds: 5
      failure_threshold: 5
    log_location: "/home/toxic/sovereign/.state/logs/yote.log"""",
    "watchdog.yaml": """processes:
  watchdog:
    command: "/home/toxic/.bun/bin/bun run src/watchdog.ts"
    working_dir: "/home/toxic/sovereign"
    readiness_probe:
      http_get:
        host: 127.0.0.1
        port: 25022
        path: /health
      initial_delay_seconds: 2
      period_seconds: 5
    log_location: "/home/toxic/sovereign/.state/logs/watchdog.log"""",
    "prometheus.yaml": """processes:
  prometheus:
    command: "prometheus --config.file=/home/toxic/sovereign/prometheus.yml --storage.tsdb.path=/home/toxic/sovereign/.prometheus --web.listen-address=0.0.0.0:25030"
    working_dir: "/home/toxic/sovereign"
    readiness_probe:
      http_get:
        host: 127.0.0.1
        port: 25030
        path: /-/healthy
      initial_delay_seconds: 3
      period_seconds: 5
    log_location: "/home/toxic/sovereign/.state/logs/prometheus.log"""",
    "landing.yaml": """processes:
  landing:
    command: "/home/toxic/.bun/bin/bun run src/landing/server.ts"
    working_dir: "/home/toxic/sovereign"
    readiness_probe:
      http_get:
        host: 127.0.0.1
        port: 25080
        path: /health
      initial_delay_seconds: 2
      period_seconds: 5
    log_location: "/home/toxic/sovereign/.state/logs/landing.log"""",
    "hf-downloader.yaml": """processes:
  hf-downloader:
    command: "bash -c '/home/toxic/.bun/bin/bun install && /home/toxic/.bun/bin/bun run src/hf_downloader.ts'"
    working_dir: "/home/toxic/sovereign"
    readiness_probe:
      http_get:
        host: 127.0.0.1
        port: 25020
        path: /health
      initial_delay_seconds: 5
      period_seconds: 5
    log_location: "/home/toxic/sovereign/.state/logs/hf-downloader.log"""",
    "llama-herder.sh": """#!/usr/bin/env bash
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-/home/toxic/sovereign}"
PORT="${LLAMA_HERDER_PORT:-28080}"
BIN_CANDIDATES=(
    "/home/toxic/projects/llama-swap-main/llama-swap"
)
BIN=""
for c in "${BIN_CANDIDATES[@]}"; do
    [[ -x "$c" ]] && { BIN="$(realpath "$c")"; break; }
done
[[ -n "$BIN" ]] || { echo "llama-swap binary not found" >&2; exit 1; }
CONF_CANDIDATES=(
    "${SOV}/tools/llama-swap/config.yaml"
)
CONF=""
for c in "${CONF_CANDIDATES[@]}"; do
    [[ -f "$c" ]] && { CONF="$(realpath "$c")"; break; }
done
[[ -n "$CONF" ]] || { echo "config.yaml not found" >&2; exit 1; }
START_PORT="$(grep -E '^\s*startPort:\s*[0-9]+' "$CONF" | grep -oE '[0-9]+' | head -1 || echo 25001)"
MODEL_COUNT="$(grep -cE '^\s{2}"[^"]+":' "$CONF" 2>/dev/null || grep -cE '^\s{2}[a-z_]+/[a-z0-9_-]+:' "$CONF" || echo 30)"
END_PORT=$((START_PORT + MODEL_COUNT + 10))
if (( PORT >= START_PORT && PORT <= END_PORT )); then
    echo "ERROR: PORT $PORT collides with backend range $START_PORT-$END_PORT" >&2
    exit 1
fi
if command -v fuser >/dev/null 2>&1; then
    fuser -k "${PORT}/tcp" 2>/dev/null || true
else
    lsof -ti tcp:"$PORT" 2>/dev/null | xargs -r kill -9 || true
fi
(
    for _ in {1..60}; do
        curl -sf --max-time 1 "http://127.0.0.1:${PORT}/health" >/dev/null && break
        sleep 1
    done
    curl -sf --max-time 120 "http://127.0.0.1:${PORT}/v1/chat/completions" \
        -H 'Content-Type: application/json' \
        -d '{"model":"beellama/qwen-flash-128k","messages":[{"role":"user","content":"ok"}],"max_tokens":1}' \
        >/dev/null 2>&1 || true
) & disown
echo "[llama-swap] BIN=$BIN CONF=$CONF PORT=$PORT"
exec "$BIN" --config "$CONF" --listen "127.0.0.1:${PORT}"""",
    "rust-web.sh": """#!/usr/bin/env bash
set -euo pipefail
SOV="${SOVEREIGN_ROOT:-/home/toxic/sovereign}"
cd "$SOV/rust_algo_web"
export RUST_WEB_PORT="${RUST_WEB_PORT:-25005}"
export LLM_PROXY_URL="${LLM_PROXY_URL:-http://127.0.0.1:28080}"
BIN="./target/release/sovereign_devops_advisor"
pkill -f "$BIN" >/dev/null 2>&1 || true
if command -v fuser >/dev/null 2>&1; then
    fuser -k "${RUST_WEB_PORT}/tcp" >/dev/null 2>&1 || true
fi
if [[ ! -x "$BIN" ]] || [[ "$BIN" -ot src/ ]]; then
    cargo build --release -q
fi
exec "$BIN"""",
    "download-models.sh": """#!/usr/bin/env bash
set -euo pipefail
# SOVEREIGN FINAL DOWNLOADER v12.0
MODEL_DIR="${MODEL_DIR:-$HOME/sovereign/models}"
# ... long script ...""",
    "code-insiders-deploy.sh": """#!/usr/bin/env bash
# VS Code Insiders + OAI extension configs generator""",
}

# Let me understand the full picture:
# 1. The stack uses process-compose with modular YAML files in stack/modules/
# 2. There are shell scripts in stack/ that handle up/down/health/build-compose
# 3. There are service scripts in stack/services/ (llama-herder.sh, rust-web.sh)
# 4. There are TypeScript files for yote (Bun-based Telegram bot)
# 5. There's a ports.env that defines all the port mappings
# 6. profiles.sh defines which modules go with which profile

# The user wants to:
# - Move everything to mise convention (July 2026)
# - Delete the shell scripts from stack/
# - Use proper mise.toml at project root
# - Use file-based tasks in .mise/tasks/ or mise/tasks/
# - Keep env vars in [env] not ports.env
# - Use env._.file and env._.path (NOT deprecated top-level dotenv/env_file)

print("Analysis complete. Now generating correct mise 2026 configuration...")
