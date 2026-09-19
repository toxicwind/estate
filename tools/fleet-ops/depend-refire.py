#!/usr/bin/env python3
"""depend-refire — bedf89a9: re-fire dependency-blocked pitchfork daemons.

The supervision gap: pitchfork's `depends` blocks a daemon's start while a
dependency is down, but never re-fires the start when the dependency
recovers. The daemon sits in "stopped" forever (this is how yote stayed
down). retry=true only covers crash loops, not dependency-blocked starts.

EVIDENCE GATING (forward fix, 2026-09-19, for the manual-stop resurrection
defect): this watcher re-fires a stopped auto=["start"] daemon ONLY when it
has PERSISTED EVIDENCE that the daemon's stopped state was caused by an
unhealthy dependency — recorded at the moment the watcher first observed it
stopped while a dep was unhealthy. A daemon manually stopped while its deps
were healthy has no such evidence and is NEVER touched (manual-stop
persistence). Evidence lives at
~/.local/state/fleet-ops/depend-refire-evidence.json; a successful refire
clears it, and a daemon observed running clears it too (recovered by other
means).

Caveat (auditable, not hidden): a manual stop issued while a dependency
happens to be down looks identical to a dependency-blocked stop. The
evidence record captures dep_states + timestamps and the refire log line
carries them, so the decision is always auditable.

Safe to run every minute; starting an already-running daemon is a no-op
guarded by the status check.
"""
import json
import os
import re
import subprocess
import sys
import time
import tomllib
from datetime import datetime, timezone
from pathlib import Path

PF = Path("/home/toxic/.local/share/mise/installs/pitchfork/2.25.0/pitchfork")
TOML = Path("/home/toxic/sovereign/pitchfork.toml")
LOG = Path("/home/toxic/sovereign/logs/depend-refire.log")
EVIDENCE = Path("/home/toxic/.local/state/fleet-ops/depend-refire-evidence.json")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def pf(*args: str) -> str:
    # pitchfork resolves daemon config from the project dir (pitchfork.toml);
    # without the right cwd, `start` reports "not found in config or state".
    p = subprocess.run([str(PF), *args], capture_output=True, text=True,
                       timeout=30, cwd="/home/toxic/sovereign")
    return p.stdout + p.stderr


def status_of(daemon: str) -> str:
    out = pf("status", daemon)
    m = re.search(r"^Status:\s*(\S+)", out, re.M)
    return m.group(1).lower() if m else "unknown"


def log_line(msg: str) -> None:
    line = f"{now_iso()} {msg}"
    print(line, flush=True)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a") as f:
            f.write(line + "\n")
    except OSError:
        pass  # stdout (journal) still carries the line


def load_evidence() -> dict:
    try:
        return json.loads(EVIDENCE.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def save_evidence(ev: dict) -> None:
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    tmp = EVIDENCE.with_suffix(".tmp")
    tmp.write_text(json.dumps(ev, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, EVIDENCE)


def wait_running(fqdn: str, timeout_s: int = 15) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if status_of(fqdn) in ("running", "starting"):
            return True
        time.sleep(3)
    return False


def main() -> int:
    cfg = tomllib.loads(TOML.read_text())
    daemons = cfg.get("daemons", {})
    # project prefix: pitchfork.toml at /home/toxic/sovereign -> "sovereign/"
    prefix = "sovereign/"
    evidence = load_evidence()
    fired = []
    skipped_manual = []
    blocked = []
    for name, d in sorted(daemons.items()):
        auto = d.get("auto", [])
        if "start" not in auto:
            continue
        fqdn = prefix + name
        st = status_of(fqdn)
        if st in ("running", "starting"):
            if fqdn in evidence:
                del evidence[fqdn]  # recovered by other means; drop stale evidence
            continue
        if st != "stopped":
            # errored/disabled/unknown: never touched by the refire watcher.
            continue
        deps = d.get("depends", [])
        dep_states = {dep: status_of(prefix + dep) for dep in deps}
        if deps and not all(s == "running" for s in dep_states.values()):
            # Dependency-blocked: persist the evidence (first-seen timestamp
            # kept; last_seen refreshed) and NEVER start while blocked.
            rec = evidence.get(fqdn, {})
            if not rec:
                rec = {"blocked_at": now_iso(), "dep_states": dep_states}
            rec["last_seen"] = now_iso()
            rec["dep_states"] = dep_states
            evidence[fqdn] = rec
            blocked.append(fqdn)
            log_line(f"blocked {fqdn}: stopped, deps={dep_states} — evidence recorded")
            continue
        # Deps healthy (or none): re-fire ONLY with dependency-blocked evidence.
        rec = evidence.get(fqdn)
        if not rec:
            skipped_manual.append(fqdn)
            log_line(f"skip {fqdn}: stopped, deps healthy, no dependency-blocked "
                     f"evidence — manual stop presumed, leaving alone")
            continue
        out = pf("start", fqdn)
        if wait_running(fqdn):
            del evidence[fqdn]
            fired.append(fqdn)
            log_line(f"refire {fqdn} OK (evidence blocked_at={rec.get('blocked_at')}, "
                     f"dep_states={rec.get('dep_states')}): "
                     f"{out.strip().splitlines()[-1] if out.strip() else 'no output'}")
        else:
            log_line(f"refire {fqdn} FAILED (still not running; evidence kept): "
                     f"{out.strip().splitlines()[-1] if out.strip() else 'no output'}")
    save_evidence(evidence)
    if not (fired or blocked or skipped_manual):
        print("depend-refire: no stuck daemons", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
