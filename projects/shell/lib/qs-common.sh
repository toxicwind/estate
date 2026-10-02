# qs-common.sh — shared helpers for the qs-* entrypoints (sovereign/projects/shell).
# Source it from a qs-* script AFTER computing QS_HOME:
#   QS_HOME="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
#   . "$QS_HOME/lib/qs-common.sh"

# Canonical locations. Override via env for testing.
: "${QS_CONFIG_NAME:=ii}"
: "${QS_HOME:?QS_HOME must be set by the caller}"
QS_CANON_CONFIG="$QS_HOME/ii/dots/.config/quickshell/$QS_CONFIG_NAME"
QS_USER_CONFIG="$HOME/.config/quickshell/$QS_CONFIG_NAME"
QS_UNIT="quickshell-ii.service"
QS_LAUNCH_LOG="$HOME/.local/state/quickshell/launch.log"

# qs_detect_env — fill in the session env quickshell needs when launched
# outside a full login shell (systemd unit, ssh, cron).
qs_detect_env() {
  export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/1000}"
  if [ -z "${WAYLAND_DISPLAY:-}" ]; then
    for s in "$XDG_RUNTIME_DIR"/wayland-*; do
      case "$s" in *.lock) continue ;; *) WAYLAND_DISPLAY="$(basename "$s")"; break ;; esac
    done
  fi
  export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"
  if [ -z "${HYPRLAND_INSTANCE_SIGNATURE:-}" ] && [ -d "$XDG_RUNTIME_DIR/hypr" ]; then
    HYPRLAND_INSTANCE_SIGNATURE="$(ls -t "$XDG_RUNTIME_DIR/hypr" 2>/dev/null | head -1)"
    export HYPRLAND_INSTANCE_SIGNATURE
  fi
  export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-wayland}"
}

qs_pids() { pgrep -x quickshell 2>/dev/null || true; }

qs_unit_active() { systemctl --user is-active --quiet "$QS_UNIT" 2>/dev/null; }

# qs_config_target — the shell.qml the live config name resolves to.
qs_config_target() {
  local name="${1:-$QS_CONFIG_NAME}"
  printf '%s/.config/quickshell/%s/shell.qml' "$HOME" "$name"
}

# qs_ipc_instances — list instance ids the IPC client can see for config $1.
qs_ipc_instances() {
  local name="${1:-$QS_CONFIG_NAME}"
  /usr/bin/quickshell -c "$name" ipc show 2>&1 || true
}

qs_log() {
  mkdir -p "$(dirname "$QS_LAUNCH_LOG")"
  printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" >>"$QS_LAUNCH_LOG"
}
