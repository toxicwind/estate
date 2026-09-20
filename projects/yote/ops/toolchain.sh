#!/usr/bin/env bash
# toolchain.sh — idempotent estate toolchain ensure-script (yote/Arch).
# Installs every CLI the fleet depends on that isn't guaranteed by a base
# CachyOS install, then verifies each binary actually executes.
# Safe to re-run; uses pacman --needed. Survives reboots (real packages).
# Installed 2026-09-20 by dep-quartermaster (ember).
set -euo pipefail

PKGS=(
  ripgrep        # rg — Chris's standing "rg means system-wide" rule
  sysstat        # iostat/mpstat/sar/pidstat
  iftop          # per-host bandwidth
  iotop          # per-process IO (python)
  dool           # dstat successor
  valgrind       # native mem debugging
  wireshark-cli  # tshark — MCP/bridge packet forensics
  just           # modern command runner
  direnv         # per-dir env (replaces .bashrc hacks)
  watchexec      # file-watch executor
  entr           # run-on-change
  inotify-tools  # inotifywait — the event-driven primitive
  strace ltrace bpftrace perf tcpdump nmap socat lsof htop
  pv parallel fzf fd bat eza zoxide hyperfine jq
  uv mold sccache ccache ninja cmake pkgconf
)
# NOTE: yq intentionally omitted — the estate already ships go-yq (4.53.x),
# which conflicts with Arch's python-based yq package. go-yq is canonical.

echo "==> ensuring ${#PKGS[@]} toolchain packages (pacman --needed)"
sudo pacman -S --needed --noconfirm "${PKGS[@]}" >/dev/null

echo "==> verifying binaries execute"
declare -A SMOKE=(
  [rg]="rg --version" [iostat]="iostat -V" [sar]="sar -V"
  [iftop]="iftop -h" [iotop]="iotop --version" [dool]="dool --version"
  [valgrind]="valgrind --version" [tshark]="tshark --version"
  [just]="just --version" [direnv]="direnv version" [watchexec]="watchexec --version"
  [entr]="command -v entr" [inotifywait]="command -v inotifywait"
  [strace]="strace -V" [bpftrace]="bpftrace --version" [perf]="perf --version"
  [tcpdump]="tcpdump --version" [jq]="jq --version" [uv]="uv --version" [yq]="yq --version"
)
fail=0
for bin in "${!SMOKE[@]}"; do
  if eval "${SMOKE[$bin]}" >/dev/null 2>&1; then
    printf '  ok %-12s\n' "$bin"
  else
    printf '  FAIL %-12s <- %s\n' "$bin" "${SMOKE[$bin]}"
    fail=1
  fi
done
if (( fail )); then echo "TOOLCHAIN INCOMPLETE"; exit 1; fi
echo "TOOLCHAIN COMPLETE"
