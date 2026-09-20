#!/usr/bin/env bash
# runner-inventory.sh — hatch-side task-runner + watchdog inventory.
#
# Reads the cell's cron.d definitions (user, goal-owned, archive) and emits a
# markdown table: id | title | enabled | schedule | runs/day | owner | flags.
#
# Heuristic flags (all verifiable from the local filesystem):
#   disabled          — enabled: false in the def
#   orphan-owner      — goal-owned def whose goal dir has no GOAL.md
#   duplicate-id      — the same id defined in more than one def file
#   missing-script    — body references ~/workspace/bin/<tool> that isn't executable
#   canary-idle       — canary runlog tail shows repeated idle/no-op ticks
#   system-readonly   — runtime-managed system job (cannot be edited/removed)
#
# Archived defs (cron.d/_archive/) are reported in a separate "Trashed /
# history" section — they are not scheduled and are not flagged as duplicates.
#
# Usage: runner-inventory.sh [--markdown|--tsv]   (default: markdown on stdout)
# Run on the hatch cell (HATCH_WS defaults to /home/hatch/workspace).
# Internal field separator is \x1f (unit separator); never a whitespace char,
# because bash collapses IFS-whitespace and drops empty fields.

set -u
US=$'\x1f'

WS="${HATCH_WS:-/home/hatch/workspace}"
FMT="${1:---markdown}"

fail() { echo "ERROR: $*" >&2; exit 1; }
[ -d "$WS/cron.d" ] || fail "no cron.d under $WS"

# defrow: print one def's frontmatter as US-separated fields:
#   id title enabled sched rpd owner file sys
defrow() { # $1=file $2=sys
  awk -v file="$1" -v sys="$2" '
    BEGIN{ id=""; title=""; enabled="true"; owner=""; kind="?"; every="?"; time=""; inb=0 }
    NR==1 && /^---$/{ inb=1; next }
    inb && /^---$/{ inb=0; next }
    inb && /^id:/      { id=substr($0,5) }
    inb && /^title:/   { title=substr($0,8) }
    inb && /^enabled:/ { enabled=substr($0,10) }
    inb && /^owner:/   { owner=substr($0,8) }
    inb && /^  kind:/  { kind=substr($0,9) }
    inb && /^  every:/ { every=substr($0,10) }
    inb && /^  time:/  { time=substr($0,9) }
    END{
      gsub(/^[ \t]+|[ \t]+$/, "", id); gsub(/^[ \t]+|[ \t]+$/, "", title);
      gsub(/^[ \t]+|[ \t]+$/, "", enabled); gsub(/^[ \t]+|[ \t]+$/, "", owner);
      gsub(/^[ \t]+|[ \t]+$/, "", kind); gsub(/^[ \t]+|[ \t]+$/, "", every);
      gsub(/^[ \t]+|[ \t]+$/, "", time);
      if (id==""){ n=file; sub(/.*\//,"",n); sub(/\..*/,"",n); id=n }
      if (every=="?" && time!="") every=time
      sched=""; rpd="?"
      if (kind=="interval"){ sched="every " every;
        if      (every ~ /s$/){ n=every; sub(/s$/,"",n); if (n>0) rpd=int(86400/n) }
        else if (every ~ /m$/){ n=every; sub(/m$/,"",n); if (n>0) rpd=int(1440/n) }
        else if (every ~ /h$/){ n=every; sub(/h$/,"",n); if (n>0) rpd=int(24/n) }
      } else if (kind=="daily"){ sched="daily " every; rpd=1 }
      else if (kind=="weekly"){ sched="weekly"; rpd="0.14" }
      else if (kind=="monthly"){ sched="monthly"; rpd="0.03" }
      else { sched=kind }
      printf "%s\x1f%s\x1f%s\x1f%s\x1f%s\x1f%s\x1f%s\x1f%s\n", id, title, enabled, sched, rpd, owner, file, sys
    }' "$1"
}

TMPD="$(mktemp -d)"; trap 'rm -rf "$TMPD"' EXIT
DEFS="$TMPD/defs"   # US-separated: id title enabled sched rpd owner file sys
GOALS="$WS/goals"
: > "$DEFS"
find "$WS/cron.d" -name '*.md' -not -path '*_invalid*' | while IFS= read -r f; do
  defrow "$f" "user" >> "$DEFS"
done
if [ -d "$WS/system-cron.d" ]; then
  find "$WS/system-cron.d" -name '*.md' -not -path '*_invalid*' | while IFS= read -r f; do
    defrow "$f" "system" >> "$DEFS"
  done
else
  SYSNOTE="system-cron.d not visible from this cell — system jobs (feed pulses, deterministic-doctor) exist in the scheduler but are runtime-managed and read-only; not enumerated here."
fi
if [ -d "$GOALS" ]; then
  find "$GOALS" -path '*/crons/*.md' | while IFS= read -r f; do
    grep -qF "$f" "$DEFS" 2>/dev/null && continue
    defrow "$f" "user" >> "$DEFS"
  done
fi

# duplicate-id detection (field 1), live defs only — _archive is history
awk -F"$US" -v OFS="$US" '$7 !~ /_archive\// {print}' "$DEFS" > "$TMPD/live"
cut -d "$US" -f1 "$TMPD/live" | sort | uniq -d > "$TMPD/dups" || true

# canary idle heuristic (hatch-local runlog tail)
CANARY_FLAG=""
RUNLOG="$WS/canary/runlog.md"
if [ -f "$RUNLOG" ]; then
  TAILN=$(tail -20 "$RUNLOG" | grep -ciE 'idle|no action|hold — no active' || true)
  [ "${TAILN:-0}" -ge 15 ] && CANARY_FLAG="canary-idle(runlog: ${TAILN}/20 idle ticks)"
fi

emit_row() { # id title enabled sched rpd owner flags
  if [ "$FMT" = "--tsv" ]; then printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$@";
  else printf '| %s | %s | %s | %s | %s | %s | %s |\n' "$@"; fi
}

normdash() { # $1=var name; "-" when blank
  local v="${!1}"; v="${v// /}"
  [ -z "$v" ] && printf -v "$1" '%s' "-"
}

if [ "$FMT" != "--tsv" ]; then
  echo "# Hatch runner inventory — $(date -u +%FT%TZ)"
  echo
  echo "| id | title | enabled | schedule | runs/day | owner | flags |"
  echo "|----|-------|---------|----------|----------|-------|-------|"
fi

sort -t "$US" -k1,1 "$DEFS" | while IFS="$US" read -r id title enabled sched rpd owner file sys; do
  [ -z "$id" ] && continue
  case "$file" in */_archive/*) continue ;; esac   # history lives in its own section
  flags=""
  [ "$enabled" = "false" ] && flags="${flags}disabled "
  case "$owner" in goal:*)
    gslug="${owner#goal:}"; [ -f "$GOALS/$gslug/GOAL.md" ] || flags="${flags}orphan-owner "
  esac
  grep -qx "$id" "$TMPD/dups" 2>/dev/null && flags="${flags}duplicate-id "
  [ "$sys" = "system" ] && flags="${flags}system-readonly "
  refs=$(sed -n '/^---$/,$p' "$file" 2>/dev/null | grep -oE '(~/workspace|/home/hatch/workspace)/bin/[A-Za-z0-9._-]+' | sed 's#.*/##' | sort -u)
  for r in $refs; do
    [ -x "$WS/bin/$r" ] || flags="${flags}missing-script:$r "
  done
  [ "$id" = "kimi-auto-canary-judge" ] && [ -n "$CANARY_FLAG" ] && flags="${flags}${CANARY_FLAG} "
  normdash title; normdash owner; normdash flags
  emit_row "$id" "$title" "$enabled" "$sched" "$rpd" "$owner" "$flags"
done

# --- trashed / history section (defs the scheduler moved to _archive) ---
if [ -d "$WS/cron.d/_archive" ]; then
  arch_n=$(find "$WS/cron.d/_archive" -name '*.md' | wc -l)
  if [ "$arch_n" -gt 0 ]; then
    if [ "$FMT" != "--tsv" ]; then
      echo; echo "## Trashed / history — not scheduled"
      echo
      echo "| id | archived def | mtime |"
      echo "|----|----------------|-------|"
    fi
    find "$WS/cron.d/_archive" -name '*.md' | sort | while IFS= read -r f; do
      aid="$(basename "$f" | sed 's/__.*//')"
      if [ "$FMT" = "--tsv" ]; then
        printf 'ARCHIVE\t%s\t%s\t%s\n' "$aid" "$f" "$(date -r "$f" +%F\ %T 2>/dev/null || stat -c %y "$f" 2>/dev/null | cut -d. -f1)"
      else
        printf '| %s | `%s` | %s |\n' "$aid" "$f" "$(date -r "$f" +%F\ %T 2>/dev/null || stat -c %y "$f" 2>/dev/null | cut -d. -f1)"
      fi
    done
  fi
fi

if [ "$FMT" != "--tsv" ]; then
  echo
  echo "_Flags: disabled / orphan-owner (goal dir has no GOAL.md) / duplicate-id /"
  echo "missing-script:<tool> (body refs a non-executable ~/workspace/bin/<tool>) /"
  echo "canary-idle (runlog tail shows repeated idle ticks) / system-readonly._"
  echo
  echo "Disabled defs are listed, not hidden: a disabled job still owns its"
  echo "definition file but does not run. The scheduler's live view (cron.list)"
  echo "is the authority for what is actually scheduled — a def on disk whose id"
  echo "is absent there is not running."
  [ -n "$SYSNOTE" ] && { echo; echo "_Note: $SYSNOTE"; }
fi
