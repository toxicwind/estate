#!/bin/bash
# fleet-watchdog cell-side driver.
# Durable copy: /home/toxic/sovereign/tools/fleet-ops/fleet-watchdog/driver.sh
# The platform scheduler runs THIS (bash ~/workspace/fleet-watchdog/driver.sh).
#
# The hot sweep path is DIRECT on awrawr-pc: sweepd.sh loops sweep.py every
# 60s with no agent-wrapper dispatch and no bridge hop (presence TTL 120s,
# so 60s keeps the lane-7 heartbeat alive with 60s margin). This driver is
# the 2m supervisor/backstop entrypoint. Three steps:
#   1. sync the rollover mirror cell -> awrawr-pc (best effort; sweep still
#      runs on the last good mirror if this fails)
#   2. sync the io-governor pages file (best effort; skipped if absent)
#   3. run the awrawr-pc supervisor: ensures sweepd is alive (restarts it if
#      dead/wedged) and runs ONE backstop sweep only when the last sweep is
#      stale. Prints one JSON line.
#
# Receipt design (2026-09-19, lane-6): cron workers intermittently end runs
# with a null result_summary even on success, so the driver emits its own
# WATCH-OK + HONEST-RECEIPT footer. The job body instructs the worker to
# copy the last two stdout lines verbatim as the run's final message.
set -uo pipefail
AWR="$HOME/workspace/skills/awrawr-mcp/bin"
WD=/home/toxic/sovereign/tools/fleet-ops/fleet-watchdog
START_S=$(date +%s)
if ! "$AWR/xfer.py" put /home/hatch/fleet-rollover.md "$WD/fleet-rollover.md" 2>&1 | tail -1; then
  echo "driver: rollover mirror sync FAILED (continuing on last mirror)" >&2
fi
# Best-effort: sync the io-governor pages file (lease-aware stall triage pages).
# Never fatal; skipped silently when the file does not exist yet.
"$AWR/xfer.py" put /home/hatch/workspace/state/io-governor.pages.jsonl \
    "$WD/io-governor.pages.jsonl" >/dev/null 2>&1 || true
ENVELOPE="$("$AWR/exec.py" --json --timeout 40 --argv bash "$WD/supervise.sh" 2>/dev/null)"
DUR_S=$(( $(date +%s) - START_S ))
# NOTE: the envelope travels via $ENVELOPE_IN because a <<heredoc occupies
# python's stdin (a pipe into `python3 -` would be swallowed by the program
# text itself).
ENVELOPE_IN="$ENVELOPE" python3 - "$DUR_S" <<'PYEOF'
import json, os, sys, time
dur = sys.argv[1]
LEDGER = os.path.expanduser("~/workspace/fleet-watchdog/driver-runs.jsonl")
try:
    env = json.loads(os.environ.get("ENVELOPE_IN", ""))
    out = (env.get("stdout") or "").strip().splitlines()
    sup = out[-1] if out else ""
except Exception:
    sup = ""
ok, posted, restarted, backstop, age = True, False, False, False, "?"
finding = "supervisor output unparseable"
try:
    d = json.loads(sup)
    ok = bool(d.get("ok", True))
    posted = bool(d.get("posted", False))
    restarted = bool(d.get("sweepd_restarted", False))
    backstop = bool(d.get("backstop_sweep", False))
    age = d.get("last_sweep_age_s", "?")
    finding = "sweepd alive, last_sweep_age_s=%s, no pages" % age
    if restarted:
        finding = "sweepd restarted, last_sweep_age_s=%s" % age
    if backstop:
        finding = "backstop sweep ran; " + finding
    if posted:
        finding = "posted pages: %s" % (d.get("pages"),)
except Exception:
    ok = False
verdict = "failed" if not ok else ("genuine" if (posted or restarted or backstop) else "no-op")
safe = finding.replace('"', "'")
row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
       "verdict": verdict, "duration_s": int(dur), "posted": posted,
       "sweepd_restarted": restarted, "backstop_sweep": backstop,
       "last_sweep_age_s": age, "work": safe}
try:
    with open(LEDGER, "a") as f:
        f.write(json.dumps(row) + "\n")
except OSError:
    pass
print(sup)
print("WATCH-OK fleet-presence-rollover-watchdog | posted=%s | %s" % (str(posted).lower(), safe))
print('HONEST-RECEIPT job=fleet-presence-rollover-watchdog verdict=%s duration_s=%s work="%s" evidence="none"' % (verdict, dur, safe))
PYEOF
