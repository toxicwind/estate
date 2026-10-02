#!/bin/bash
# Watch the skills root and touch a marker on change.
#
# This lives in skills/lib/ because it *manages* the skills tier — it used to
# hang off ~/bin/ as a stray script and hardcoded /home/toxic/sovereign/skills,
# which dangled the moment the estate moved to /home/toxic/estate.
#
# Consumers poll the marker to know when to pull; nothing here pulls or writes.
# To learn the skills root the same way every other skill does, source the
# shared resolver instead of guessing a path.
set -uo pipefail

MARKER="${SKILLS_MARKER:-/tmp/skills-yote-marker}"
SKILLS_LIB="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "$SKILLS_LIB/estate.sh"
SKILLS="${SKILLS_HOME:?SKILLS_HOME unresolved}"

if [[ ! -d "$SKILLS" ]]; then
  echo "skills-watch: SKILLS_HOME does not exist: $SKILLS" >&2
  exit 1
fi

touch "$MARKER"

# Recursive, no shell globbing: skill payloads contain spaces (Chromium profiles
# under omp.browser.headless.profile). inotifywait needs -r to descend.
exec inotifywait -m -r -e modify,create,delete,move \
  --format "%w%f %e" \
  --exclude "__pycache__" \
  --exclude ".git" \
  "$SKILLS" 2>/dev/null | while read -r filepath event; do
  case "$filepath" in
    *.tmp|*~|*.pyc) continue ;;
  esac
  touch "$MARKER"
done