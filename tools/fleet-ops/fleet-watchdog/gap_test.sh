#!/bin/bash
# Forced-gap test: stop the sweeper, wait 135s (> GAP_S=120s) with no
# sweeps, then run supervise.sh. Expect: service DOWN detected, restart via
# systemctl, backstop sweep pages "watchdog gap ... resumed" with
# posted=true. If the platform cron intervenes mid-wait (same code path),
# the log will show it and the test attributes honestly.
WD=/home/toxic/sovereign/tools/fleet-ops/fleet-watchdog
SJ=/home/toxic/sovereign/tools/fleet-ops/fleet-watchdog/state.json
systemctl --user stop fleet-watchdog-sweepd.service
t0=$(python3 -c 'import json; print(json.load(open("/home/toxic/sovereign/tools/fleet-ops/fleet-watchdog/state.json"))["last_sweep_ts"])')
echo "GAP-TEST t0=$t0 service=$(systemctl --user is-active fleet-watchdog-sweepd.service)"
/home/toxic/bin/isleep 135 --name forced-gap-wait --tick 5 >/dev/null 2>&1
t1=$(python3 -c 'import json; print(json.load(open("/home/toxic/sovereign/tools/fleet-ops/fleet-watchdog/state.json"))["last_sweep_ts"])')
if [ "$t0" = "$t1" ]; then
  echo "GAP-TEST confirmed: zero sweeps during 135s wait (t1=$t1)"
else
  echo "GAP-TEST note: state advanced mid-wait (t0=$t0 t1=$t1); cron likely ran supervise"
fi
echo "GAP-TEST supervise output:"
bash "$WD/supervise.sh"
echo "GAP-TEST service now: $(systemctl --user is-active fleet-watchdog-sweepd.service)"
