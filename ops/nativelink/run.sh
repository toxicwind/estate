#!/usr/bin/env bash
# NativeLink launcher for pitchfork.
#
# Why the mkdir: NativeLink's FilesystemStore does NOT create its `temp_path`,
# and it does not report a health failure when that directory is missing -- it
# just answers "No route for ..." on every RE endpoint while the process still
# logs "Ready". Verified against 1.7.6: with content_path present and
# temp_path absent, /status 404s; with both present, /status 200s.
#
# So the store layout is materialized here, before exec, every start. Keep the
# four paths in sync with config/nativelink/nativelink.json5.
set -euo pipefail

ROOT=/home/toxic/var/runtime/nativelink
install -d -m 0755 \
	"$ROOT/cas/content" \
	"$ROOT/cas/tmp" \
	"$ROOT/ac/content" \
	"$ROOT/ac/tmp"

exec /home/toxic/.local/bin/nativelink \
	/home/toxic/estate/config/nativelink/nativelink.json5