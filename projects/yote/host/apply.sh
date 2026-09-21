#!/usr/bin/env bash
# Apply yote host provisioning artifacts from this repo onto /etc and $HOME.
# Run ON YOTE as a user with sudo:  ./apply.sh
# Idempotent: safe to re-run after package upgrades or config drift.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

install_file() {
  local src="$1" dest="$2"
  sudo install -D -m 644 "$src" "$dest"
  echo "installed $dest"
}

install_file "$HERE/etc/udev/rules.d/30-zram.rules" /etc/udev/rules.d/30-zram.rules
install_file "$HERE/etc/systemd/system/nvidia-persistenced.service.d/override.conf" \
  /etc/systemd/system/nvidia-persistenced.service.d/override.conf

# Build-cache home configs (no sudo; installed as the invoking user).
# Canonical sources for the buildsrv-injected cache environment.
install_home_file() {
  local src="$1" dest="$2"
  install -D -m 644 "$src" "$dest"
  echo "installed $dest"
}

install_home_file "$HERE/home/.cargo/config.toml" "$HOME/.cargo/config.toml"
install_home_file "$HERE/home/.config/ccache/ccache.conf" \
  "$HOME/.config/ccache/ccache.conf"

sudo udevadm control --reload-rules
sudo systemctl daemon-reload

echo "--- verify:"
printf "swappiness: "; cat /proc/sys/vm/swappiness
printf "zswap:      "; cat /sys/module/zswap/parameters/enabled
systemctl is-active nvidia-persistenced
systemd-analyze verify nvidia-persistenced.service && echo "unit verify: clean"
printf "cargo sccache: "; grep -h rustc-wrapper "$HOME/.cargo/config.toml"
printf "ccache max_size: "; grep -h max_size "$HOME/.config/ccache/ccache.conf"
