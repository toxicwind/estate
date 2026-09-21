#!/usr/bin/env bash
# pitchfork-config-doctor.sh — verify the live pitchfork supervisor's daemon set
# matches the canonical pitchfork.toml, and flag divergent/stale pitchfork.toml
# copies that a CLI invocation could pick up instead.
#
# Background (2026-09-21 audit): `Error: pitchfork::deps::not_found` /
# `daemon '12' not found in configuration` was traced to the CLI daemon-name
# resolution path (pitchfork_toml.rs::resolve_daemon_id_with_namespace), NOT to
# `depends` resolution — i.e. someone passed `12` as a daemon id to a CLI
# command (logs/status/wait/...). A bad `depends` entry raises the distinct
# `missing_dependency` code instead. This script guards the config side:
# live set == canonical set, no divergent configs shadowing the canonical one,
# and the traced error path still behaves.
#
# Read-only. Never starts/stops/restarts anything.
# Exit: 0 = healthy, 1 = divergence/stale configs found, 2 = script error.
#
# Env overrides: PITCHFORK_CANON, PITCHFORK_NS, PITCHFORK_SCAN_ROOT
set -u
export LC_ALL=C  # comm(1) and sort(1) must agree on collation order

CANON="${PITCHFORK_CANON:-/home/toxic/sovereign/pitchfork.toml}"
NS="${PITCHFORK_NS:-sovereign}"
SCAN_ROOT="${PITCHFORK_SCAN_ROOT:-/home/toxic}"
FAIL=0

die()  { echo "DOCTOR-ERROR: $*" >&2; exit 2; }
warn() { echo "DOCTOR-WARN: $*"; FAIL=1; }
ok()   { echo "DOCTOR-OK: $*"; }

command -v pitchfork >/dev/null || die "pitchfork not on PATH"

LIVE_TMP="$(mktemp)"; CANON_TMP="$(mktemp)"
trap 'rc=$?; rm -f "$LIVE_TMP" "$CANON_TMP"; exit $rc' EXIT

# 1. live daemon set (namespaced ids, header hidden)
pitchfork list --hide-header 2>/dev/null | awk 'NF{print $1}' | LC_ALL=C sort -u >"$LIVE_TMP" \
  || die "pitchfork list failed"
LIVE_N="$(wc -l <"$LIVE_TMP")"
[ "$LIVE_N" -gt 0 ] || die "pitchfork list returned zero daemons"

# 2. canonical daemon short names -> namespaced ids
[ -f "$CANON" ] || die "canonical config not found: $CANON"
python3 - "$CANON" "$NS" >"$CANON_TMP" <<'PYEOF' || die "toml parse failed"
import re, sys
canon, ns = sys.argv[1], sys.argv[2]
names = set()
pat = re.compile(r'^\s*\[daemons\.([^\]]+)\]')
with open(canon, encoding='utf-8', errors='replace') as fh:
    for line in fh:
        m = pat.match(line)
        if m:
            names.add(m.group(1).strip().strip('"').strip("'"))
for n in sorted(names):
    print(f"{ns}/{n}")
PYEOF
LC_ALL=C sort -u -o "$CANON_TMP" "$CANON_TMP" || die "sort failed"
CANON_N="$(wc -l <"$CANON_TMP")"

# 3. compare live vs canonical
if diff -q "$LIVE_TMP" "$CANON_TMP" >/dev/null; then
  ok "live daemon set == canonical ($CANON_N daemons, namespace '$NS')"
else
  warn "live set != canonical set (live=$LIVE_N canon=$CANON_N)"
  comm -23 "$LIVE_TMP" "$CANON_TMP" | sed 's/^/  live-only: /'
  comm -13 "$LIVE_TMP" "$CANON_TMP" | sed 's/^/  canon-only: /'
fi

# 4. canonical toml newer than supervisor boot?
#    pitchfork does NOT hot-reload pitchfork.toml; `supervisor run --boot`
#    restores daemon definitions from state.toml, so edits need a restart.
SUP_PID="$(pgrep -f 'pitchfork supervisor run' | head -1)"
if [ -n "$SUP_PID" ] && [ -d "/proc/$SUP_PID" ]; then
  BOOT_EPOCH="$(stat -c %Y "/proc/$SUP_PID" 2>/dev/null || echo 0)"
  CANON_EPOCH="$(stat -c %Y "$CANON")"
  if [ "$CANON_EPOCH" -gt "$BOOT_EPOCH" ]; then
    warn "canonical toml (mtime $(date -d "@$CANON_EPOCH" '+%F %T')) is NEWER than supervisor boot ($(date -d "@$BOOT_EPOCH" '+%F %T')) — edits not yet live; restart supervisor to pick them up"
  else
    ok "canonical toml predates supervisor boot — no pending config changes"
  fi
else
  warn "supervisor process not found (pgrep 'pitchfork supervisor run')"
fi

# 5. purely-numeric daemon names (the '12' class): syntactically valid, but a CLI
#    arg like `pitchfork logs 12` resolves as a daemon NAME — flag for awareness.
NUMERIC="$(awk -F/ 'NF==2 && $2 ~ /^[0-9]+$/ {print $2}' "$CANON_TMP" | tr '\n' ' ')"
if [ -n "$NUMERIC" ]; then
  warn "purely-numeric daemon names defined (ambiguous with PIDs/ports/seqs as CLI args): $NUMERIC"
else
  ok "no purely-numeric daemon names in canonical config"
fi

# 6. divergent/shadowing pitchfork.toml scan (bounded).
#    Discovery order: /etc/pitchfork/config.toml -> ~/.config/pitchfork/config.toml
#    -> upward walk from CWD (pitchfork.local.toml > pitchfork.toml >
#    .config/pitchfork.local.toml > .config/pitchfork.toml), merged root->cwd.
#    Any divergent copy under a dir tree you run CLI commands from shadows the
#    canonical daemon set.
CANON_SHA="$(sha256sum "$CANON" | awk '{print $1}')"
DIVERGENT=0
while IFS= read -r f; do
  [ "$f" = "$CANON" ] && continue
  if [ -L "$f" ]; then
    target="$(readlink -f "$f")"
    if [ "$target" = "$CANON" ]; then continue; fi
    warn "symlink config not pointing at canonical: $f -> $target"
    DIVERGENT=$((DIVERGENT+1)); continue
  fi
  sha="$(sha256sum "$f" | awk '{print $1}')"
  if [ "$sha" = "$CANON_SHA" ]; then continue; fi
  n="$(grep -cE '^\s*\[daemons\.' "$f" 2>/dev/null || true)"
  warn "divergent pitchfork.toml ($n daemons, sha ${sha:0:12}…): $f"
  DIVERGENT=$((DIVERGENT+1))
done < <(find "$SCAN_ROOT" -maxdepth 6 \
           \( -name pitchfork.toml -o -name pitchfork.local.toml \) \
           -not -path '*/node_modules/*' 2>/dev/null | sort)
if [ "$DIVERGENT" -eq 0 ]; then
  ok "no divergent pitchfork.toml copies under $SCAN_ROOT (maxdepth 6)"
fi

# 7. behavior probe (read-only): the traced error path must stay a clean
#    DaemonNotFound, not a crash and not missing_dependency.
PROBE_OUT="$(pitchfork status 12 2>&1 || true)"
if echo "$PROBE_OUT" | grep -q "not found in configuration"; then
  ok "behavior probe: \`pitchfork status 12\` -> clean DaemonNotFound (deps::not_found path intact)"
else
  warn "behavior probe: unexpected output for \`pitchfork status 12\`: $(echo "$PROBE_OUT" | head -2 | tr '\n' ';')"
fi

echo "DOCTOR-DONE fail=$FAIL"
exit "$FAIL"
