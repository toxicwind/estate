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
#   3. --register: adds your row to §2 Active Crews (refuses duplicates).
#      --done SHA: marks your row DONE with the final commit SHA.
#   4. Shows you the room: recent fleet voices (who's here, what they're on).
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
  --register         add your row to §2 Active Crews
  --done SHA         mark your §2 row DONE with final commit SHA
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

# --- 3. §2 registration ----------------------------------------------------
kb_is_local=0
case "$KB_FILE" in /tmp/fleet-kb.*) kb_is_local=0;; *) kb_is_local=1;; esac

if [ "$DO_REGISTER" -eq 1 ]; then
  [ -n "$OWNER" ] || { echo "fleet-onboard: --owner is required with --register" >&2; exit 2; }
  [ "$kb_is_local" -eq 1 ] || { echo "fleet-onboard: --register needs a local KB file (use --kb PATH)" >&2; exit 2; }
  if grep -qi "^| *${NAME} *|" "$KB_FILE"; then
    echo "fleet-onboard: '${NAME}' is already registered in §2 — not duplicating."
    grep -i "^| *${NAME} *|" "$KB_FILE"
  else
    today="$(date +%F)"
    scope_short="$(echo "$TASK" | cut -c1-140)"
    newline="| ${NAME} | ${scope_short} | ${OWNER} | RUNNING (${today}) |"
    anchor="$(grep -n "Retired/completed crews stay listed here" "$KB_FILE" | head -1 | cut -d: -f1)"
    [ -n "$anchor" ] || { echo "fleet-onboard: cannot find §2 table anchor in KB" >&2; exit 2; }
    awk -v n="$anchor" -v line="$newline" 'NR==n{print ""; print line; print ""} {print}' "$KB_FILE" > "${KB_FILE}.new" \
      && mv "${KB_FILE}.new" "$KB_FILE"
    echo "fleet-onboard: registered in §2 Active Crews:"
    echo "  $newline"
    echo "  (commit + push the KB per §3 push rules — staleness is a bug)"
  fi
fi

if [ -n "$DONE_SHA" ]; then
  [ "$kb_is_local" -eq 1 ] || { echo "fleet-onboard: --done needs a local KB file (use --kb PATH)" >&2; exit 2; }
  if ! grep -qi "^| *${NAME} *|" "$KB_FILE"; then
    echo "fleet-onboard: '${NAME}' has no §2 row to mark DONE" >&2; exit 2
  fi
  today="$(date +%F)"
  lname="$(echo "$NAME" | tr '[:upper:]' '[:lower:]')"
  awk -v n="$lname" -v d="$today" -v sha="$DONE_SHA" -F'|' '
    BEGIN{OFS="|"}
    /^\|/ {
      c2=$2; gsub(/^ +| +$/,"",c2)
      lc=tolower(c2)
      if (lc==n) { $5=" DONE ("d") — "sha" "; print; next }
    }
    {print}
  ' "$KB_FILE" > "${KB_FILE}.new" && mv "${KB_FILE}.new" "$KB_FILE"
  echo "fleet-onboard: marked DONE in §2:"
  grep -i "^| *${NAME} *|" "$KB_FILE"
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
