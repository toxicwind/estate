# estate.sh — canonical path resolution for shell-based skills.
#
# No skill hardcodes an estate path. They source this and ask it.
#
#   . /home/toxic/.tau/skills/lib/estate.sh
#   echo "$ESTATE" "$RANCH" "$PORTS_ENV"
#
# Overrides: ESTATE_HOME, RANCH_HOME, VENDORED_HOME, MANOR_HOME, SKILLS_HOME, TAU_HOME

_estate_first_existing() {
  for candidate in "$@"; do
    [ -e "$candidate" ] && { readlink -f "$candidate"; return 0; }
  done
  readlink -f "$1"
}

# Resolve the skills root from this file's own location, walking up.
_estate_self="${BASH_SOURCE[0]}"
while [ -n "$_estate_self" ] && [ "$_estate_self" != "/" ]; do
  if [ -d "$_estate_self/lib" ] || [ -d "$_estate_self/pattern-forge" ]; then
    _estate_guess="$_estate_self"
    break
  fi
  _estate_self="$(dirname "$_estate_self")"
done
SKILLS_HOME="${SKILLS_HOME:-${_estate_guess:-$HOME/.tau/skills}}"
SKILLS_HOME="$(readlink -f "$SKILLS_HOME")"

ESTATE_HOME="${ESTATE_HOME:-$(_estate_first_existing "$SKILLS_HOME/../estate" "$HOME/estate" "$HOME/sovereign")}"
RANCH_HOME="${RANCH_HOME:-$(_estate_first_existing "$ESTATE_HOME/ranch" "$HOME/ranch" "$HOME/projects")}"
VENDORED_HOME="${VENDORED_HOME:-$(_estate_first_existing "$ESTATE_HOME/vendored")}"
MANOR_HOME="${MANOR_HOME:-$(_estate_first_existing "$ESTATE_HOME/manor")}"
VAR_HOME="${VAR_HOME:-$ESTATE_HOME/var}"
TAU_HOME="${TAU_HOME:-$(_estate_first_existing "$RANCH_HOME/tau")}"

ESTATE="$ESTATE_HOME"
RANCH="$RANCH_HOME"
VENDORED="$VENDORED_HOME"
MANOR="$MANOR_HOME"
VAR="$VAR_HOME"
TAU="$TAU_HOME"
PORTS_ENV="$ESTATE_HOME/config/ports.env"
KNOWLEDGEBASE="$ESTATE_HOME/docs/fleet-knowledgebase.md"

export SKILLS_HOME ESTATE_HOME RANCH_HOME VENDORED_HOME MANOR_HOME VAR_HOME TAU_HOME
export ESTATE RANCH VENDORED MANOR VAR TAU PORTS_ENV KNOWLEDGEBASE