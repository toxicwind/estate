#!/usr/bin/env bash
# Gate an inbound connection: admit known-hatch, quarantine unknown.
# Usage: gate_workflow.sh <remote-host>  ; exit 0=admit, 2=quarantine.
set -uo pipefail
cd "$(dirname "$0")"
python3 hatch_gate.py --peer "$1" >/tmp/hatch-gate-last.json
rc=$?
if [ $rc -eq 0 ]; then echo "ADMIT $1"; else echo "QUARANTINE $1"; fi
exit "$rc"
