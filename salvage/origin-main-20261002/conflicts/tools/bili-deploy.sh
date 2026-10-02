#!/usr/bin/env bash
# Deploy the sigma fork as the live compression proxy.
#
# Why this is a script and not tribal knowledge: the swap has two traps that both
# fail SILENTLY. A running daemon keeps its old inode, so a copied dist looks
# deployed while the old code keeps serving. And the extension's watchdog cannot
# revive an orphaned daemon, because it only arms while a parent session lives.
# Both are handled below, and both are verified rather than assumed.
#
# Usage:
#   tools/bili-deploy.sh              # build, verify, swap, restart, verify
#   tools/bili-deploy.sh --no-build   # reuse the existing dist/ build
#   tools/bili-deploy.sh --check      # report only, change nothing
#
# Rollback: every previous dist is kept as dist.fork-<stamp>/ beside the live one.
#   G=/home/totoxic/.bun/install/global/node_modules/billion-context
#   rm -rf "$G/dist" && cp -a "$G/dist.fork-<stamp>" "$G/dist" && tools/bili-deploy.sh --no-build
set -euo pipefail

FORK="${BILI_FORK_DIR:-/home/toxic/estate/projects/sigma}"
GLOBAL="${BILI_GLOBAL_DIR:-/home/toxic/.bun/install/global/node_modules/billion-context}"
DIST="$GLOBAL/dist"
PORT="${BILI_PORT:-32847}"
HEALTH="http://127.0.0.1:$PORT/__bili/health"
STATS="http://127.0.0.1:$PORT/__bili/stats"
KEEP_BACKUPS="${BILI_KEEP_BACKUPS:-3}"

BUILD=1
CHECK_ONLY=0
for arg in "$@"; do
	case "$arg" in
	--no-build) BUILD=0 ;;
	--check) CHECK_ONLY=1; BUILD=0 ;;
	-h | --help) sed -n '2,25p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
	*) echo "bili-deploy: unknown flag $arg" >&2; exit 2 ;;
	esac
done

say() { printf '  %s\n' "$*"; }
die() { printf 'bili-deploy: %s\n' "$*" >&2; exit 1; }

live_pid() { ss -lptn "sport = :$PORT" 2>/dev/null | grep -o 'pid=[0-9]*' | head -1 | cut -d= -f2; }
count_in() { grep -c -- "$1" "$2" 2>/dev/null || true; }

# Symbols the live proxy must carry. Each one is a fix that was made in the fork
# source and is invisible if the build is stale, so a missing symbol is fatal.
REQUIRED=(
	"DEFAULT_MAX_PREFLIGHT_MS:src/preflight.ts:preflight wall-clock ceiling"
	"trimToSummaryCap:src/preflight.ts:bounded summary output"
	"Hard limit: at most:src/preflight.ts:per-part budget in the prompt"
	"loadOpenRouterModels:src/registry.ts:OpenRouter window discovery"
	"peekOpenRouterContext:src/registry.ts:published window lookup"
)

# ---------------------------------------------------------------- build
if [ "$BUILD" = 1 ]; then
	say "building $FORK"
	(cd "$FORK" && npm run build >/tmp/bili-deploy-build.log 2>&1) ||
		{ tail -30 /tmp/bili-deploy-build.log >&2; die "build failed (see /tmp/bili-deploy-build.log)"; }
	say "build ok"
else
	[ -f "$FORK/dist/index.js" ] || die "no dist/index.js in $FORK; run without --no-build"
fi

# ---------------------------------------------------------------- verify the build
missing=0
for entry in "${REQUIRED[@]}"; do
	sym="${entry%%:*}"
	src="${entry#*:}"; src="${src%%:*}"; what="${entry#*:*:}"
	n=$(count_in "$sym" "$FORK/dist/index.js")
	[ "${n:-0}" -gt 0 ] || { say "MISSING  $sym — $what ($src)"; missing=1; }
done
[ "$missing" = 0 ] || die "built dist is missing fork symbols; refusing to deploy a stale build"

if [ "$CHECK_ONLY" = 1 ]; then
	say "check only: all ${#REQUIRED[@]} fork symbols present in the build"
	say "live pid: $(live_pid || echo none)"
	exit 0
fi

# ---------------------------------------------------------------- swap
[ -d "$DIST" ] || die "no live dist at $DIST"
STAMP=$(date +%H%M%S)
BACKUP="$DIST.fork-$STAMP"
say "backing up live dist -> $(basename "$BACKUP")"
mv "$DIST" "$BACKUP"
cp -a "$FORK/dist" "$DIST"
for entry in "${REQUIRED[@]}"; do
	sym="${entry%%:*}"
	[ "$(count_in "$sym" "$DIST/index.js")" -gt 0 ] || { rm -rf "$DIST"; cp -a "$BACKUP" "$DIST"; die "post-copy verification failed for $sym; live dist restored"; }
done
say "fork dist in place, verified"

# The extension entry must stay byte-identical, or the tau extension breaks in a
# way that only shows up as a missing compress nudge.
if [ "$(stat -c%s "$DIST/agent/omp-native.js" 2>/dev/null || echo 0)" != "$(stat -c%s "$BACKUP/agent/omp-native.js")" ]; then
	rm -rf "$DIST"; cp -a "$BACKUP" "$DIST"
	die "omp-native.js size changed; live dist restored"
fi
say "omp-native.js size unchanged"

# ---------------------------------------------------------------- restart
# A dist swap alone does nothing for a running process. The daemon must be
# restarted, and the old one will not exit on TERM in some states.
OLD=$(live_pid || true)
if [ -n "$OLD" ]; then
	say "stopping pid $OLD"
	kill -TERM "$OLD" 2>/dev/null || true
	for _ in $(seq 1 20); do kill -0 "$OLD" 2>/dev/null || break; sleep 0.5; done
	if kill -0 "$OLD" 2>/dev/null; then say "pid $OLD ignored TERM, sending KILL"; kill -KILL "$OLD" 2>/dev/null || true; sleep 1; fi
	for _ in $(seq 1 10); do [ -z "$(live_pid || true)" ] && break; sleep 0.5; done
	[ -z "$(live_pid || true)" ] || die "port $PORT still held after KILL"
fi

say "starting the daemon"
setsid nohup /usr/bin/node "$DIST/index.js" start --host 127.0.0.1 --port "$PORT" \
	>/tmp/bili-deploy-proxy.log 2>&1 </dev/null &
sleep 6
NEW=$(live_pid || true)
[ -n "$NEW" ] || die "daemon did not come up (see /tmp/bili-deploy-proxy.log)"

# A fresh daemon has no sessions attached, so its stats legitimately report no
# windows at all. Judging discovery from that would fire a false alarm on every
# deploy. The real signal is whether the OpenRouter window cache loaded; the
# window distribution is then reported as information, not a verdict.
if grep -q 'loaded openrouter model windows' "${BILI_LOG:-$HOME/.local/state/billion-context/bili.log}" 2>/dev/null; then
	say "openrouter window cache has loaded at least once (discovery active)"
else
	die "the openrouter window cache has never loaded; discovery is not running"
fi
# The JSON is pretty-printed, so there is a space after the colon. Matching
# digits immediately after ":" silently yields empty values and a count of
# zero-width matches, which reads as "no windows" rather than as a bug.
windows=$(curl -sf --max-time 10 "$STATS" 2>/dev/null | grep -oE '"contextWindow":[[:space:]]*[0-9]+' | grep -oE '[0-9]+$' | sort -n | uniq -c | tr '\n' ' ' || true)
if [ -n "$windows" ]; then
	say "live windows (count value): $windows"
else
	say "no sessions attached yet, so no windows are resolved; the next request will show them"
fi

# ---------------------------------------------------------------- prune old backups
if [ "$KEEP_BACKUPS" -gt 0 ]; then
	# shellcheck disable=SC2012
	ls -1dt "$GLOBAL"/dist.fork-* 2>/dev/null | tail -n +$((KEEP_BACKUPS + 1)) | while read -r old; do
		say "pruning $(basename "$old")"
		rm -rf "$old"
	done
fi
say "done. previous dist kept at $(basename "$BACKUP")"
