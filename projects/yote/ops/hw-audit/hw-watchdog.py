#!/usr/bin/env python3
"""hw-watchdog.py — post-audit health watchdog (runs as hw-audit.service ExecStart #2).

Reads the newest /var/lib/hw-audit/audit-*.jsonl, extracts disk_health,
compares against watchdog-state.json, and appends alerts to alerts.log on:
  - SMART overall-health now failing
  - drive temp >= 60 C (warn) / >= 70 C (critical)
  - power-on-hours jumping backwards (drive replaced) or wear pct_used rising fast
  - newly failed systemd units
  - new pacman orphans

State file schema (watchdog-state.json):
  {"/dev/sda": {"hours": 46417, "passed": true, "temp": 26}, ...,
   "failed": ["dnsmasq.service", ...], "orphans": [...],
   "last_run": "2026-09-14T03:58:07-06:00"}

MASTER: toxicwind/sovereign-projects projects/yote/ops/hw-audit/
Live copy deployed to /home/toxic/hw-watchdog.py (see hw-audit.service).
"""
import glob
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

STATE_DIR = "/var/lib/hw-audit"
STATE_FILE = os.path.join(STATE_DIR, "watchdog-state.json")
ALERTS_LOG = os.path.join(STATE_DIR, "alerts.log")
TEMP_WARN = 60
TEMP_CRIT = 70


def sh(*args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return ""


def latest_audit():
    files = sorted(glob.glob(os.path.join(STATE_DIR, "audit-*.jsonl")))
    return files[-1] if files else None


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_state(state):
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STATE_FILE)


def alert(msg):
    ts = datetime.now(timezone.utc).astimezone().isoformat()
    line = f"{ts} {msg}\n"
    with open(ALERTS_LOG, "a") as f:
        f.write(line)
    print("ALERT:", msg)


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main():
    audit = latest_audit()
    if not audit:
        print("no audit-*.jsonl found; nothing to check", file=sys.stderr)
        return 1

    health = {}
    for line in open(audit):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if rec.get("section") == "disk_health":
            dev = rec.get("dev")
            if dev:
                health[dev] = rec

    state = load_state()
    new_state = dict(state)

    for dev, rec in sorted(health.items()):
        prev = state.get(dev, {})
        entry = {"hours": num(rec.get("power_on_hours")) or 0,
                 "passed": bool(rec.get("passed")),
                 "temp": num(rec.get("temp_c")) or 0}
        new_state[dev] = entry

        if not entry["passed"]:
            alert(f"{dev} SMART overall-health FAILED (model {rec.get('model')})")
        t = entry["temp"]
        if t >= TEMP_CRIT:
            alert(f"{dev} temp CRITICAL: {t}C")
        elif t >= TEMP_WARN:
            alert(f"{dev} temp warning: {t}C")
        ph = prev.get("hours")
        if ph and entry["hours"] and entry["hours"] < ph - 24:
            alert(f"{dev} power-on-hours went backwards ({ph} -> {entry['hours']}): drive replaced?")
        pp, cp = num(prev.get("pct_used")), num(rec.get("pct_used"))
        if pp is not None and cp is not None and cp - pp >= 5:
            alert(f"{dev} wear jumped {pp}% -> {cp}% in one audit")

    # failed systemd units
    failed = sorted(u for u in sh("systemctl", "--failed", "--no-legend", "--plain").splitlines()
                    if u.strip() and not u.startswith("0 loaded"))
    failed = sorted({u.split()[0] for u in failed if u.split()})
    prev_failed = set(state.get("failed", []))
    for u in sorted(set(failed) - prev_failed):
        alert(f"new failed unit: {u}")
    new_state["failed"] = failed

    # pacman orphans
    orphans = sorted(o for o in sh("pacman", "-Qtdq").split() if o)
    prev_orphans = set(state.get("orphans", []))
    for o in sorted(set(orphans) - prev_orphans):
        alert(f"new pacman orphan: {o}")
    new_state["orphans"] = orphans

    new_state["last_run"] = datetime.now(timezone.utc).astimezone().isoformat()
    save_state(new_state)
    print(f"watchdog ok: {len(health)} drives, {len(failed)} failed units, "
          f"{len(orphans)} orphans (audit: {os.path.basename(audit)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
