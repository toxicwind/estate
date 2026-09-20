#!/usr/bin/env bash
# REORG-EXECUTE.sh — sovereign reorg, staged one-command execution.
# PLAN: /home/toxic/sovereign/REORG-PLAN.md — READ IT FIRST. DO NOT RUN BLINDLY.
# Runs on yote as user `toxic` (via the exec bridge or a local shell).
# This script does NOT restart the bridge itself; the cutover is OPERATOR-DRIVEN
# (systemd-run --user is broken on yote — user manager degraded, transient units
# vanish; verified 2026-09-20). The hatch operator runs `pitchfork restart
# sovereign/awrawr-ws-exec` from hatch AFTER this script's bridge call returns.
# Copy-first (Phase 4) means the toml never points at a missing file meanwhile.
# See REORG-PLAN.md §6.
set -euo pipefail

# The repo pre-commit hook rejects lockfile changes unless this is set; the
# baseline/reorg commits are deliberate, so opt in (the hook's own documented bypass).
export PI_ALLOW_LOCKFILE_CHANGE=1

SOV=/home/toxic/sovereign
HATCH=$SOV/hatch
EMBER=$HATCH/agents/ember
PITCHFORK_BIN=/home/toxic/.local/share/mise/installs/pitchfork/2.25.0/pitchfork
MANIFEST=$SOV/REORG-MANIFEST.txt
TS=$(date +%Y%m%d-%H%M%S)

log() { echo "[reorg $TS] $*"; }
die() { echo "[reorg FATAL] $*" >&2; exit 1; }
note() { echo "$*" >> "$MANIFEST"; }

# Stage exactly the reorg paths (renames/deletions included) -- never git add -A.
# The tree is shared with ~8 active workers; a blind add sweeps in their
# in-flight lockfiles and secret-bearing logs, tripping the pre-commit hook.
# The secret-entropy rule must NOT be bypassed, so we stage only our own paths.
reorg_add() {
  local args=()
  for q in shingle-workspace sovereign/bin hatch bridge scratch \
      docs/ws-exec-8379-audit-20260914.md docs/connector-bridge-routing-d4734168.md \
      pitchfork.toml tools/stash-guard/stash-guard.py \
      fleet/dispatch_fallback.py REORG-PLAN.md REORG-EXECUTE.sh REORG-MANIFEST.txt \
      "pitchfork.toml.pre-reorg-$TS"; do
    [ -e "$q" ] && args+=("$q")
  done
  [ -e "docs/Meta/Muse AI/Jarvis/runtime-cell.md" ] && args+=("docs/Meta/Muse AI/Jarvis/runtime-cell.md")
  if [ ${#args[@]} -gt 0 ]; then git add -A -- "${args[@]}"; fi
}

# ---------- Phase 0: preflight (read-only) ----------
log "phase 0: preflight"
[ "$(whoami)" = "toxic" ] || die "must run as toxic, got $(whoami)"
[ -d "$SOV" ] || die "$SOV missing"
[ -d /home/toxic/shingle ] || die "/home/toxic/shingle missing"
[ -L /home/toxic/shingle ] && die "/home/toxic/shingle is already a symlink — move already done?"
pgrep -f "pitchfork supervisor run" >/dev/null || die "pitchfork supervisor not running"
ss -ltn 2>/dev/null | grep -q ':8379' || die ":8379 (ws-exec) not listening"
[ -x "$PITCHFORK_BIN" ] || die "pitchfork binary not at $PITCHFORK_BIN"
DAEMON_ID=$("$PITCHFORK_BIN" list 2>/dev/null | grep -o '[^ ]*awrawr-ws-exec' | head -1 || true)
[ -n "$DAEMON_ID" ] || die "could not resolve awrawr-ws-exec daemon id via pitchfork list"
log "daemon id: $DAEMON_ID"
cd "$SOV"
git rev-parse --show-toplevel >/dev/null 2>&1 || die "$SOV is not a git repo"

# inode manifest (inotify continuity check later)
find /home/toxic/shingle/squawk-root -maxdepth 2 -printf '%i %p\n' 2>/dev/null | sort > /tmp/reorg-inodes-shingle.txt || true
find "$SOV/shingle-workspace" -maxdepth 1 -printf '%i %p\n' 2>/dev/null | sort > /tmp/reorg-inodes-ws.txt || true

# warn on processes with cwd under the moved trees
for pid in $(ls /proc | grep -E '^[0-9]+$'); do
  cwd=$(readlink "/proc/$pid/cwd" 2>/dev/null || true)
  case "$cwd" in
    /home/toxic/shingle*|"$SOV"/shingle-workspace*) log "WARN: pid $pid cwd=$cwd" ;;
  esac
done
: > "$MANIFEST"
note "# REORG manifest $TS — reverse order = rollback"

# ---------- Phase 1: baseline commit ----------
log "phase 1: baseline commit (reorg paths only -- see reorg_add)"
git reset -q
reorg_add
if git diff --cached --quiet; then
  log "reorg paths unchanged, no baseline commit needed"
else
  git commit -m "reorg: pre-move baseline ($TS)"
  git push || log "WARN: git push failed — continuing (push manually)"
fi
note "baseline committed $TS"

# ---------- Phase 2: new homes ----------
log "phase 2: mkdir hatch/agents hatch/docs bridge"
mkdir -p "$HATCH/agents" "$HATCH/docs" "$SOV/bridge"
[ -f "$HATCH/README.md" ] || cat > "$HATCH/README.md" <<'EOF'
# hatch/ — the hatch (cell) side of the world, on yote
`agents/ember/` is the Ember operational home (moved from /home/toxic/shingle).
`docs/` consolidates hatch/bridge/cell documentation.
Layout SSOT: ../REORG-PLAN.md
EOF
[ -f "$SOV/bridge/README.md" ] || cat > "$SOV/bridge/README.md" <<'EOF'
# bridge/ — production home of the live hatch<->yote exec bridge
`awrawr_ws_exec.py` is the canonical tracked copy, run by pitchfork daemon
`sovereign/awrawr-ws-exec` (Funnel /exec-ws -> 127.0.0.1:8379).
Compat: /home/toxic/sovereign/shingle-workspace/awrawr_ws_exec.py resolves here via symlink.
EOF

# ---------- Phase 3: Ember move (atomic rename) ----------
log "phase 3: move /home/toxic/shingle -> $EMBER"
if [ ! -e "$EMBER" ]; then
  mv /home/toxic/shingle "$EMBER"
  note "mv /home/toxic/shingle -> $EMBER"
else
  log "ember home already exists, skipping mv"
fi
if [ ! -L /home/toxic/shingle ]; then
  ln -s "$EMBER" /home/toxic/shingle
  note "ln -s $EMBER /home/toxic/shingle"
fi
# inode continuity: every pre-move path must keep its inode (new files may
# appear concurrently — additions are fine; changes/losses are not)
find "$EMBER/squawk-root" -maxdepth 2 -printf '%i %p\n' 2>/dev/null | sed "s|$EMBER|/home/toxic/shingle|" | sort > /tmp/reorg-inodes-shingle-after.txt
python3 - <<'PYEOF' || die "inode manifest changed — aborting"
pre, post = {}, {}
for p in ("/tmp/reorg-inodes-shingle.txt", "/tmp/reorg-inodes-shingle-after.txt"):
    d = pre if "after" not in p else post
    for line in open(p):
        ino, path = line.split(None, 1)
        d[path.strip()] = ino
bad = [(p, pre[p], post.get(p)) for p in pre if post.get(p) != pre[p]]
if bad:
    print("CHANGED/MISSING inodes:")
    for b in bad[:20]:
        print("  path=%s pre=%s post=%s" % b)
    raise SystemExit(1)
print("inodes stable for %d pre-existing paths (inotify watches survive)" % len(pre))
PYEOF
log "inodes stable (inotify watches survive)"
# runner-profiles shipment (2026-09-20, after the plan was written) rides along
# in this atomic mv: squawk-root/runners.yml (v1, 6 profiles), bin/squawk-profile,
# bin/squawk-trace, bin/squawk-follow, 5 new 0600 keys, wrapper --profile +
# FLEET_KEYS_DIR=$ROOT/keys fix. All resolve via $SQUAWK_ROOT + readlink -f.
note "atomic mv incl. runner-profiles: runners.yml, bin/squawk-{profile,trace,follow}, 5 keys, wrapper --profile/FLEET_KEYS_DIR fix"

# ---------- Phase 4: bridge extraction (copy-first) ----------
log "phase 4: extract bridge file (copy-first, daemon untouched)"
if [ ! -f "$SOV/bridge/awrawr_ws_exec.py" ]; then
  cp -p "$SOV/shingle-workspace/awrawr_ws_exec.py" "$SOV/bridge/awrawr_ws_exec.py"
  # update the "Tracked copy" header note inside the file
  sed -i 's|sovereign/shingle-workspace/awrawr_ws_exec.py|sovereign/bridge/awrawr_ws_exec.py|' "$SOV/bridge/awrawr_ws_exec.py"
  note "cp shingle-workspace/awrawr_ws_exec.py -> bridge/awrawr_ws_exec.py"
else
  log "bridge file already extracted, skipping"
fi

# ---------- Phase 5: scratch consolidation ----------
log "phase 5: consolidate scratch"
if [ -d "$SOV/shingle-workspace/bin" ] && [ ! -L "$SOV/shingle-workspace" ]; then
  for f in "$SOV/shingle-workspace/bin/"*; do
    b=$(basename "$f")
    if [ -e "$SOV/bin/$b" ]; then
      log "WARN: collision, leaving in place: $f (already in sovereign/bin)"
    else
      mv "$f" "$SOV/bin/$b" && note "mv shingle-workspace/bin/$b -> sovereign/bin/$b"
    fi
  done
  rmdir "$SOV/shingle-workspace/bin" 2>/dev/null || true
fi
if [ -d "$SOV/shingle-workspace/bridge-docs" ]; then
  mv "$SOV/shingle-workspace/bridge-docs" "$HATCH/docs/bridge-docs"
  note "mv shingle-workspace/bridge-docs -> hatch/docs/bridge-docs"
fi
# hatch docs: git mv when tracked (keeps history); plain mv + git add when
# untracked (git mv refuses untracked sources — verified 2026-09-20)
mv_doc() { # $1 = repo-relative src, $2 = dest dir
  local src="$SOV/$1" destdir="$2" base
  [ -f "$src" ] || { log "doc not found, skipping: $1"; return 0; }
  mkdir -p "$destdir"; base="$(basename "$src")"
  if git ls-files --error-unmatch "$1" >/dev/null 2>&1; then
    git mv "$src" "$destdir/" && note "git mv $1 -> $destdir"
  else
    mv "$src" "$destdir/" && git add "$destdir/$base" && note "mv+add $1 -> $destdir (was untracked)"
  fi
}
mv_doc "docs/ws-exec-8379-audit-20260914.md" "$HATCH/docs"
mv_doc "docs/connector-bridge-routing-d4734168.md" "$HATCH/docs"
mv_doc "docs/Meta/Muse AI/Jarvis/runtime-cell.md" "$HATCH/docs"
[ -f "$SOV/scratch/README.md" ] || cat > /tmp/scratch-readme.md <<'EOF'
# scratch/ — non-production staging (renamed from shingle-workspace)
One-off scripts, staging dirs, audits, patch harnesses. NOT a service home:
do not add pitchfork daemon `run` paths here. Production files that lived here
were extracted: the exec bridge -> ../bridge/, bin tools -> ../bin/,
bridge docs -> ../hatch/docs/bridge-docs/.
Compat: ../shingle-workspace -> scratch (symlink).
EOF
if [ ! -e "$SOV/scratch" ]; then
  cp /tmp/scratch-readme.md "$SOV/shingle-workspace/README.md" 2>/dev/null || true
  mv "$SOV/shingle-workspace" "$SOV/scratch"
  note "mv shingle-workspace -> scratch"
  mv /tmp/scratch-readme.md "$SOV/scratch/README.md"
else
  log "scratch already exists, skipping rename"
fi
if [ ! -L "$SOV/shingle-workspace" ]; then
  ln -s scratch "$SOV/shingle-workspace"
  note "ln -s scratch shingle-workspace"
fi

# ---------- Phase 6: config updates ----------
log "phase 6: pitchfork.toml + friends"
cp -p "$SOV/pitchfork.toml" "$SOV/pitchfork.toml.pre-reorg-$TS"
note "backup pitchfork.toml.pre-reorg-$TS"
python3 - "$SOV/pitchfork.toml" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p).read()
subs = [
  ('# SOVEREIGN PITCHFORK CONFIG — GENERATED from config/ports.env + service definitions\n# DO NOT EDIT DIRECTLY — Run: bun run scripts/generate.ts',
   '# SOVEREIGN PITCHFORK CONFIG — HAND-EDITED (generator retired 2026-09-14 per sovereign/AGENTS.md;\n# never run bun run scripts/generate.ts — it would destroy live daemons). Port SSOT: config/ports.env.'),
  ('run = "exec /home/toxic/.shingle/squawk-relay/run-feed.sh"',
   'run = "exec /home/toxic/sovereign/hatch/agents/ember/squawk-relay/run-feed.sh"'),
  ('SQUAWK_CHAT_ROOT = "/home/toxic/.shingle/squawk-root"',
   'SQUAWK_CHAT_ROOT = "/home/toxic/sovereign/hatch/agents/ember/squawk-root"'),
  ('/home/toxic/sovereign/shingle-workspace/awrawr_ws_exec.py',
   '/home/toxic/sovereign/bridge/awrawr_ws_exec.py'),
]
for old, new in subs:
    assert old in s, "MISSING expected string: %r" % old[:60]
    s = s.replace(old, new)
open(p, "w").write(s)
import tomllib
tomllib.load(open(p, "rb"))
print("pitchfork.toml updated + TOML valid")
PYEOF
note "pitchfork.toml: 3 path updates + header fix"
# stash-guard exclude list follows the rename (real path is tools/stash-guard/,
# not tools/fleet-ops/ — plan §3 corrected 2026-09-20). Excludes are gitignore-style
# patterns matched against git status paths: after the rename "shingle-workspace/"
# matches nothing and "scratch/" would get guarded, so both the edit AND a daemon
# restart are required (running process has the old list in memory).
SG="$SOV/tools/stash-guard/stash-guard.py"
if [ -f "$SG" ] && grep -q '"shingle-workspace/"' "$SG"; then
  sed -i 's|"shingle-workspace/"|"scratch/",\n    "bridge/"|' "$SG"
  python3 -c "import ast; ast.parse(open('$SG').read())" \
    || die "stash-guard.py edit broke syntax"
  note "stash-guard.py exclude list updated (shingle-workspace/ -> scratch/ + bridge/)"
  "$PITCHFORK_BIN" restart sovereign/stash-guard \
    && log "stash-guard restarted (new excludes live)" \
    || log "WARN: stash-guard restart failed — restart sovereign/stash-guard manually"
else
  log "WARN: stash-guard.py not found or already updated — excludes NOT touched"
fi
# dispatch_fallback default directives path -> canonical
if grep -q 'DEFAULT_DIRECTIVES = "/home/toxic/.shingle/directives.md"' "$SOV/fleet/dispatch_fallback.py"; then
  sed -i 's|DEFAULT_DIRECTIVES = "/home/toxic/.shingle/directives.md"|DEFAULT_DIRECTIVES = "/home/toxic/sovereign/hatch/agents/ember/directives.md"|' \
    "$SOV/fleet/dispatch_fallback.py"
  note "dispatch_fallback.py DEFAULT_DIRECTIVES updated"
fi

log "phase 6b: commit reorg (reorg paths only)"
reorg_add
git commit -m "reorg: shingle->hatch/agents/ember, shingle-workspace->scratch, bridge/ canonical ($TS)

Compat symlinks: /home/toxic/shingle, /home/toxic/sovereign/shingle-workspace.
Bridge cutover: copy-first, delayed restart scheduled separately (zero downtime).
Plan: REORG-PLAN.md"
git push || log "WARN: git push failed — push manually before considering this done"
note "reorg committed $TS"

# ---------- Phase 7: bridge cutover is OPERATOR-DRIVEN ----------
# systemd-run --user is broken on yote (user manager degraded; transient units
# vanish — verified 2026-09-20), so no delayed restart is scheduled here.
# The hatch operator restarts the daemon from hatch AFTER this script's bridge
# call has returned (see the NEXT block below). Copy-first (Phase 4) guarantees
# the toml never points at a missing file in the meantime.
log "phase 7: bridge cutover deferred to the hatch operator (systemd-run --user broken on this host)"
note "bridge cutover deferred: operator runs: $PITCHFORK_BIN restart $DAEMON_ID  (from hatch, after this script returns)"

# ---------- local verification ----------
log "verify: symlink resolution"
[ "$(realpath /home/toxic/shingle)" = "$EMBER" ] || die "shingle symlink wrong"
[ "$(realpath /home/toxic/sovereign/shingle-workspace)" = "$SOV/scratch" ] || die "shingle-workspace symlink wrong"
[ "$(realpath /home/toxic/.shingle/squawk-root)" = "$EMBER/squawk-root" ] || die ".shingle chain broken"
log "verify: pitchfork list"
"$PITCHFORK_BIN" list 2>/dev/null | grep -E 'awrawr-ws-exec|squawk-ws|squawk-feed' || log "WARN: daemon list check inconclusive"

cat <<EOF2

================================================================
REORG STAGED — bridge cutover NOT yet done (operator-driven, see below).
NEXT — from hatch, in this order:
  0. Restart the bridge daemon NOW (this script has returned, so this is safe):
       python3 ~/workspace/awrawr-bridge/exec.py '$PITCHFORK_BIN restart $DAEMON_ID'
     Fire-and-forget: the response dies with the server — EXPECTED. Then poll:
  1. WS handshake to https://github-mcp-host.tailc9ac71.ts.net/exec-ws -> expect 101
  2. exec.py 'echo BRIDGE-LIVE' succeeds (proves the NEW canonical path executes)
  3. exec.py 'md5sum /home/toxic/sovereign/bridge/awrawr_ws_exec.py' matches committed blob
  4. squawk publish round-trip via hatch CLI (proves symlink chain + inotify)
  5. runner-profiles: exec.py '/home/toxic/shingle/bin/squawk profiles' lists 6
     profiles; runners.yml resolves at the canonical ember path (readlink -f);
     FLEET_KEYS_DIR points at the ember-home keys dir
  6. Phase 8 swap (stale copy -> compat symlink), ONLY after 101 verified:
       exec.py 'mv /home/toxic/sovereign/scratch/awrawr_ws_exec.py /home/toxic/sovereign/scratch/awrawr_ws_exec.py.pre-reorg && ln -s ../bridge/awrawr_ws_exec.py /home/toxic/sovereign/scratch/awrawr_ws_exec.py && cd /home/toxic/sovereign && git add -A && git commit -m "reorg: phase 8 bridge compat symlink" && git push'
  7. Full checklist: REORG-PLAN.md §7. Rollback: REORG-PLAN.md §8.
NOTE: pitchfork currently respawns doomed awrawr-ws-exec copies every ~20s
(EADDRINUSE — stale holder). If the restart leaves the port wedged, kill the
stale holder PID via a fresh bridge call; the next respawn binds cleanly.
================================================================
EOF2
