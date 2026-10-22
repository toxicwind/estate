#!/usr/bin/env python3
"""Semantic-strength oracle v3.

Scores each suite by inspecting the HARNESS probe's real output (numeric
artifacts), not the thin arm-echo. Filters UNTRIGGERED tasks and weak fakes.
"""
import json, subprocess

PROBES = {
    "socket":  ("python3 lib/sock_stress.py",  ["sent", '"ok": true', "recv"]),
    "tokwalk": ("./poc_token_walk.mjs",        ["Global maxP", "loadBearing=", "P=", "Siphon"]),
}

def strength(out, evidence):
    s = 0.0
    tokhit = any(t in out for t in ("sock_ok", "tokwalk_ok"))
    if tokhit: s += 0.2
    ev = sum(1 for e in evidence if e in out)
    s += 0.25 * ev           # up to 0.75 for real numeric traces
    if "Error" in out or "Traceback" in out: s -= 0.3
    return round(min(max(s, 0), 1), 2)

def untriggered(out):
    # a task that ran but produced no trace changed nothing measurable
    return "Global maxP" not in out and '"ok": true' not in out

def main():
    report = {}
    for suite, (cmd, ev) in PROBES.items():
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        out = r.stdout + "\n" + r.stderr
        st = strength(out, ev)
        report[suite] = {"strength": st, "exit": r.returncode,
                         "untriggered": untriggered(out),
                         "numeric_traces": [e for e in ev if e in out],
                         "verdict": "STRONG" if st >= 0.7 else ("WEAK" if 0.4 <= st < 0.7 else "FAKE")}
    flagged = [k for k, v in report.items() if v["verdict"] in ("WEAK", "FAKE")]
    print(json.dumps({"count": len(report), "flagged": flagged, "report": report}, indent=2))

if __name__ == "__main__":
    main()
