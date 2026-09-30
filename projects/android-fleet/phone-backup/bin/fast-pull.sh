#!/usr/bin/env bash
# fast-pull.sh — bootstrap parallel pull: phone code/archives/repos -> /mnt/8TB/phone-archive.
# 4 concurrent plain `adb pull` jobs (measured 30 MB/s vs 7 MB/s tar-stream on 2026-09-30).
# See speed-race.sh for the method shootout. Usage: fast-pull.sh [dest]
set -u
DEST="${1:-/mnt/8TB/phone-archive}"
mkdir -p "$DEST"

PIXEL="${PIXEL:-}"
if [[ -z "$PIXEL" ]]; then
  PIXEL="$(adb devices | awk '/^10\.0\.0\.77:[0-9]+[[:space:]]+device/{print $1; exit}')"
fi
[[ -n "$PIXEL" ]] || { echo "no pixel endpoint"; exit 1; }
export PIXEL DEST
echo "pixel=$PIXEL dest=$DEST"

MANIFEST="$DEST/pull-manifest-$(date -u +%Y%m%dT%H%M%SZ).txt"
export MANIFEST
echo "# fast-pull manifest $(date -u +%FT%TZ) pixel=$PIXEL dest=$DEST" > "$MANIFEST"

pull_one() {
  local src="$1"
  local size files
  if adb -s "$PIXEL" pull "/sdcard/$src" "$DEST/$src" >/tmp/fast-pull-"$src".log 2>&1; then
    size=$(du -sh "$DEST/$src" | cut -f1)
    files=$(find "$DEST/$src" | wc -l)
    echo "OK $src size=$size files=$files" >> "$MANIFEST"
  else
    echo "FAIL $src" >> "$MANIFEST"
  fi
}
export -f pull_one

# 4-way parallel across top-level dirs
printf '%s\n' Download Documents ik_llama.cpp-main Export 1openfang Tasker House | \
  xargs -P4 -I{} bash -c 'pull_one "$@"' _ {}

echo "done. manifest: $MANIFEST"
cat "$MANIFEST"
