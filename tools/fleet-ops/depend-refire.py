#!/usr/bin/env python3
"""depend-refire — bedf89a9: re-fire dependency-blocked pitchfork daemons.

The supervision gap: pitchfork's `depends` blocks a daemon's start while a
dependency is down, but never re-fires the start when the dependency
recovers. The daemon sits in "stopped" forever (this is how yote stayed
down). retry=true only covers crash loops, not dependency-blocked starts.

This watcher closes the loop: every run, for each daemon with
auto=["start"] that is currently "stopped", if all of its `depends` are
"running", it issues `pitchfork start`. Daemons that are disabled,
errored, or manually stopped (no auto=["start"]) are never touched.

Safe to run every minute; starting an already-running daemon is a no-op
guarded by the status check.
"""
import re
import subprocess
import sys
import tomllib
from pathlib import Path

PF = Path("/home/toxic/.local/share/mise/installs/pitchfork/2.25.0/pitchfork")
TOML = Path("/home/toxic/sovereign/pitchfork.toml")
LOG = Path("/home/toxic/sovereign/logs/depend-refire.log")


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


def main() -> int:
    cfg = tomllib.loads(TOML.read_text())
    daemons = cfg.get("daemons", {})
    # project prefix: pitchfork.toml at /home/toxic/sovereign -> "sovereign/"
    prefix = "sovereign/"
    fired = []
    for name, d in sorted(daemons.items()):
        auto = d.get("auto", [])
        if "start" not in auto:
            continue
        fqdn = prefix + name
        st = status_of(fqdn)
        if st != "stopped":
            continue
        deps = d.get("depends", [])
        dep_states = {dep: status_of(prefix + dep) for dep in deps}
        if deps and not all(s == "running" for s in dep_states.values()):
            continue
        out = pf("start", fqdn)
        fired.append(fqdn)
        log_line = (f"refire {fqdn} (was stopped, deps={dep_states}): "
                    f"{out.strip().splitlines()[-1] if out.strip() else 'no output'}")
        print(log_line, flush=True)
        with LOG.open("a") as f:
            f.write(log_line + "\n")
    if not fired:
        print("depend-refire: no stuck daemons", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
