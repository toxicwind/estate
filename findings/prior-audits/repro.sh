#!/usr/bin/env bash
set -uo pipefail
YHOME="${HOME}"
YUSER="${USER:-yote}"
YTMP="${TMPDIR:-/tmp}/yote-env-${YUSER}-$$"
mkdir -p "${YTMP}"
try_run(){ local label="$1"; shift; local cmd="$*"; echo "=== $label ==="; timeout 2 bash -c "$cmd"; ec=$?; echo "[ec=$ec] $label"; if [ $ec -ne 0 ]; then echo "[TRIGGER INTEGRATION] $label FAILED -> monadic LEFT"; else echo "[RIGHT] $label"; fi; }
try_run "bashrc" "cat ${YHOME}/.bashrc"
try_run "bashrc sources" "grep -E 'source|\.|^\\.' ${YHOME}/.bashrc | head -n 100"
try_run "bash_profile" "cat ${YHOME}/.bash_profile 2>/dev/null; cat ${YHOME}/.profile 2>/dev/null; cat ${YHOME}/.zshrc 2>/dev/null"
try_run "bash_aliases" "cat ${YHOME}/.bash_aliases 2>/dev/null; cat ${YHOME}/.bash_functions 2>/dev/null; ls ${YHOME}/.bashrc.d/ 2>/dev/null"
try_run "referenced files" "for f in $(grep -oE '[^ ]+\\.sh' ${YHOME}/.bashrc 2>/dev/null | sort -u); do echo \"--- ${YHOME}/$f\"; cat ${YHOME}/$f 2>/dev/null || cat $f 2>/dev/null | head -n 30; done"
try_run "CPU" "lscpu; cat /proc/cpuinfo | grep -E 'model name|cpu MHz' | head -n 20; nproc"
try_run "GPU" "lspci | grep -i -E 'vga|3d|display'; nvidia-smi 2>/dev/null; ls /dev/dri 2>/dev/null"
try_run "MOBO" "cat /sys/devices/virtual/dmi/id/board_name 2>/dev/null; cat /sys/devices/virtual/dmi/id/product_name 2>/dev/null"
try_run "NETWORK" "ip a; ip route; tailscale status 2>/dev/null"
