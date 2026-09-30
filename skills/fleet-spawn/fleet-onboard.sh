#!/usr/bin/env bash
# fleet-onboard.sh — step zero for every new agent in Ember's pack.
#
#   fleet-onboard.sh --name NAME --task "one-line task description" --register
#
# What it does, in order:
#   1. Reads the fleet knowledgebase (local path, or GitHub raw fallback).
#      Fails hard if the KB is unreachable: no KB, no verified start.
#   2. Overlap-checks §2 Active Crews against your task. On overlap it prints
#      the colliding crews and exits 2 — coordinate in fleet BEFORE announcing.
#      (--advisory softens to a warning.)
#   3. --register: creates your per-crew file (docs/fleet/crews/<crew>.md) and
#      regenerates the §2 rollup via `bun projects/ops/bin/kb-rollup.ts`.
#      --done SHA: marks your per-crew file DONE and regenerates §2.
#      §2 Active Crews is a GENERATED rollup (Alternative A, Chris 2026-09-29):
#      never hand-edit the table — the per-crew files are the source of truth.
#   4. Shows you the room: recent fleet voices (who's here, what's on).
#   5. Prints your hello template. It does NOT write your hello for you —
#      your first words in fleet must be your own voice + one genuine question.
#
# Lives in: skills/fleet-spawn/fleet-onboard.sh (toxicwind/sovereign-projects).
# Documented in: skills/fleet-spawn/SKILL.md (the spawn protocol).
set -euo pipefail

KB_DEFAULT="/home/toxic/sovereign/docs/fleet-knowledgebase.md"
KB_RAW_URL="https://raw.githubusercontent.com/toxicwind/sovereign-projects/main/docs/fleet-knowledgebase.md"
SQUAWK_ROOT_DEFAULT="/home/toxic/.shingle/squawk-root"

NAME=""; TASK=""; KB=""; OWNER=""; DONE_SHA=""; ADVISORY=0; DO_REGISTER=0; FLEET_N=10

usage() {
  cat <<'EOF'
usage: fleet-onboard.sh --name NAME --task "task description" [options]
  --name NAME        agent name (one word, lowercase, unique)
  --task "DESC"      one-line task description (used for overlap check + scope)
  --kb PATH|URL      knowledgebase path (default: yote canonical path,
                     then GitHub raw fallback)
  --owner OWNER       crew owner/coordinator (required with --register)
  --register         create your per-crew file + regenerate the §2 rollup
  --done SHA         mark your per-crew file DONE with final commit SHA
  --advisory         overlap check warns instead of exiting 2
  --fleet-n N        recent fleet messages to show (default 10)
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --name) NAME="$2"; shift 2;;
    --task) TASK="$2"; shift 2;;
    --kb) KB="$2"; shift 2;;
    --owner) OWNER="$2"; shift 2;;
    --register) DO_REGISTER=1; shift;;
    --done) DONE_SHA="$2"; shift 2;;
    --advisory) ADVISORY=1; shift;;
    --fleet-n) FLEET_N="$2"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "unknown arg: $1" >&2; usage >&2; exit 2;;
  esac
done

[ -n "$NAME" ] || { echo "fleet-onboard: --name is required" >&2; exit 2; }
[ -n "$TASK" ] || { echo "fleet-onboard: --task is required" >&2; exit 2; }

# --- 1. read the knowledgebase -------------------------------------------
KB_FILE=""; KB_TMP=""
kb_from_url() {
  KB_TMP="$(mktemp /tmp/fleet-kb.XXXXXX.md)"
  if curl -fsSL --max-time 20 "$KB_RAW_URL" -o "$KB_TMP"; then
    KB_FILE="$KB_TMP"
  else
    rm -f "$KB_TMP"; KB_TMP=""
    return 1
  fi
}
if [ -n "$KB" ]; then
  case "$KB" in
    http*|https*) KB_TMP="$(mktemp /tmp/fleet-kb.XXXXXX.md)"
      curl -fsSL --max-time 20 "$KB" -o "$KB_TMP" || { echo "fleet-onboard: cannot fetch KB from $KB" >&2; exit 2; }
      KB_FILE="$KB_TMP";;
    *) [ -f "$KB" ] || { echo "fleet-onboard: KB not found at $KB" >&2; exit 2; }
      KB_FILE="$KB";;
  esac
elif [ -f "$KB_DEFAULT" ]; then
  KB_FILE="$KB_DEFAULT"
else
  kb_from_url || { echo "fleet-onboard: KB unreachable (no $KB_DEFAULT, GitHub raw failed). No KB, no verified start." >&2; exit 2; }
fi
echo "fleet-onboard: knowledgebase OK ($KB_FILE)"
trap '[ -n "$KB_TMP" ] && rm -f "$KB_TMP"' EXIT

# --- 2. overlap check against §2 Active Crews -------------------------------
STOP=" the a an and or of to in for on with from into over under that this these those then than as at by be is are was were will would should could can has have had do does did not no its it you your we our they their he she his her them us i me my all any each every some other more most such only also just very too so but if when where what which who whom how why while about after before between during through across per via new old one two first last work working task tasks agent agents fleet pack ember make making using use used get getting set run running via "

tokenize() {
  # lowercase, keep alnum, one word per line, len>=3, drop stopwords
  echo "$1" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '\n' \
    | awk 'length($0)>=3' | sort -u \
    | while read -r w; do case "$STOP" in *" $w "*) ;; *) echo "$w";; esac; done
}

CREWS="$(sed -n '/^## 2\. Active crews/,/^## 3\./p' "$KB_FILE" | grep '^| ' | grep -v '^| *Crew' | grep -v '^|---')"
TASK_TOKENS="$(tokenize "$TASK")"

OVERLAPS=""
while IFS= read -r row; do
  crew="$(echo "$row" | awk -F'|' '{gsub(/^ +| +$/,"",$2); print $2}')"
  scope="$(echo "$row" | awk -F'|' '{gsub(/^ +| +$/,"",$3); print $3}')"
  owner="$(echo "$row" | awk -F'|' '{gsub(/^ +| +$/,"",$4); print $4}')"
  status="$(echo "$row" | awk -F'|' '{gsub(/^ +| +$/,"",$5); print $5}')"
  # skip this agent's own (re)registration
  [ "$(echo "$crew" | tr '[:upper:]' '[:lower:]')" = "$(echo "$NAME" | tr '[:upper:]' '[:lower:]')" ] && continue
  score=0
  while IFS= read -r tok; do
    [ -n "$tok" ] || continue
    if echo " $crew $scope " | tr '[:upper:]' '[:lower:]' | grep -qw "$tok"; then
      score=$((score+1))
    fi
  done <<< "$TASK_TOKENS"
  if [ "$score" -ge 2 ]; then
    OVERLAPS="${OVERLAPS}${crew} :: ${scope:0:110} [owner: ${owner}; ${status}]\n"
  fi
done <<< "$CREWS"

if [ -n "$OVERLAPS" ]; then
  echo ""
  echo "=================================================================="
  echo "OVERLAP DETECTED — your task collides with live crews:"
  echo "=================================================================="
  printf "%b" "$OVERLAPS"
  echo "------------------------------------------------------------------"
  echo "Do NOT announce yet. Coordinate in fleet first: name the overlap,"
  echo "agree who owns what (or merge), THEN proceed."
  echo "=================================================================="
  echo ""
  if [ "$ADVISORY" -eq 0 ]; then
    exit 2
  fi
else
  echo "fleet-onboard: no §2 overlap detected for this task."
fi

# --- 3. registration: per-crew file + generated §2 rollup ------------------
# §2 Active Crews is a GENERATED rollup (Alternative A, Chris 2026-09-29).
# Source of truth: docs/fleet/crews/<crew>.md — one file per crew, frontmatter
# (crew/scope/owner/status). kb-rollup.ts writes the file and regenerates §2
# under flock, so concurrent registrations can't clobber each other.
# Never hand-edit the §2 table.
kb_is_local=0
case "$KB_FILE" in /tmp/fleet-kb.*) kb_is_local=0;; *) kb_is_local=1;; esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ROLLUP="$REPO_ROOT/projects/ops/bin/kb-rollup.ts"
if [ ! -f "$ROLLUP" ] && [ "$kb_is_local" -eq 1 ]; then
  # Deployed copy (e.g. /home/toxic/.local/bin/fleet-onboard): the script no
  # longer sits inside the repo, so resolve the rollup from the KB file's own
  # repo instead of the script location.
  kb_dir="$(dirname "$KB_FILE")"
  KB_REPO_ROOT="$(git -C "$kb_dir" rev-parse --show-toplevel 2>/dev/null || (cd "$kb_dir/.." && pwd))"
  if [ -f "$KB_REPO_ROOT/projects/ops/bin/kb-rollup.ts" ]; then
    ROLLUP="$KB_REPO_ROOT/projects/ops/bin/kb-rollup.ts"
  fi
fi
BUN_BIN="$(command -v bun || true)"
[ -n "$BUN_BIN" ] || BUN_BIN="$HOME/.bun/bin/bun"
[ -x "$BUN_BIN" ] || { echo "fleet-onboard: bun not found (need bun for kb-rollup.ts)" >&2; exit 2; }
[ -f "$ROLLUP" ] || { echo "fleet-onboard: kb-rollup.ts not found at $ROLLUP" >&2; exit 2; }

if [ "$DO_REGISTER" -eq 1 ]; then
  [ -n "$OWNER" ] || { echo "fleet-onboard: --owner is required with --register" >&2; exit 2; }
  [ "$kb_is_local" -eq 1 ] || { echo "fleet-onboard: --register needs a local KB file (use --kb PATH)" >&2; exit 2; }
  "$BUN_BIN" "$ROLLUP" register --name "$NAME" --scope "$TASK" --owner "$OWNER" --kb "$KB_FILE"
  echo "  (commit + push the per-crew file AND the KB per §3 push rules — staleness is a bug)"
fi

if [ -n "$DONE_SHA" ]; then
  [ "$kb_is_local" -eq 1 ] || { echo "fleet-onboard: --done needs a local KB file (use --kb PATH)" >&2; exit 2; }
  "$BUN_BIN" "$ROLLUP" done --name "$NAME" --sha "$DONE_SHA" --kb "$KB_FILE"
fi

# --- 4. show the room -------------------------------------------------------
SQROOT="${SQUAWK_ROOT:-$SQUAWK_ROOT_DEFAULT}"
if [ -d "$SQROOT/fleet" ]; then
  echo ""
  echo "--- recent fleet voices (last ${FLEET_N}) ---"
  for f in $(ls -t "$SQROOT"/fleet/*.md 2>/dev/null | head -"$FLEET_N"); do
    seq="$(sed -n 's/^seq: //p' "$f" | head -1)"
    from="$(sed -n 's/^from: //p' "$f" | head -1)"
    title="$(sed -n 's/^title: //p' "$f" | head -1)"
    echo "  [$seq] $from: ${title:0:70}"
  done
else
  echo ""
  echo "(no local squawk root at $SQROOT — run: squawk read fleet --n 25)"
fi

# --- 5. your hello ----------------------------------------------------------
echo ""
echo "--- step zero complete. now speak for yourself ---"
echo "Post YOUR OWN hello in fleet, in YOUR OWN voice, with ONE genuine"
echo "question to the fleet or a named agent. Template, not a script —"
echo "the words must be yours:"
echo ""
echo "  SQUAWK_SENDER=\"${NAME} (ember's pack)\" squawk send fleet \"<your hello + one genuine question>\""
echo ""
echo "Then narrate as you work. Squawk is a chat, not a log."
