#!/bin/bash
# fleet-watchdog cell-side driver.
# Durable copy: /home/toxic/sovereign/tools/fleet-ops/fleet-watchdog/driver.sh
# The platform scheduler runs THIS (via xfer get + bash); all logic and state
# live on awrawr-pc. Two steps:
#   1. sync the rollover mirror cell -> awrawr-pc (best effort; sweep still
#      runs on the last good mirror if this fails)
#   2. run the awrawr-pc sweep, print its JSON result
set -uo pipefail
AWR="$HOME/workspace/skills/awrawr-mcp/bin"
WD=/home/toxic/sovereign/tools/fleet-ops/fleet-watchdog
if ! "$AWR/xfer.py" put /home/hatch/fleet-rollover.md "$WD/fleet-rollover.md" 2>&1 | tail -1; then
  echo "driver: rollover mirror sync FAILED (continuing on last mirror)" >&2
fi
"$AWR/exec.py" --json --timeout 40 --argv python3 "$WD/sweep.py"
