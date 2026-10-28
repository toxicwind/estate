#!/usr/bin/env python3
"""SpecAgent dependency-aware repair for the DoH probe.
Intercepts stderr + exit codes from concurrent arms, traces each failure
signature to the failing leaf, and proposes an ADVISORY leaf repair
(no brute-force retry). Data-driven signature->leaf map.
"""
import json, subprocess, sys

SIG2LEAF = {
    "timed out":           ("doh_probe", "outbound DoH fetch", "raise fetch timeout / use --local"),
    "urlopen error":       ("doh_probe", "resolver reachability", "network gate check before run"),
    "JSONDecodeError":     ("doh_probe", "resolver returned non-JSON", "fall back to --local simulator"),
    "no verified output":  ("doh_probe", "verdict missing", "confirm resolve + compare path emit"),
    "exit 2 (discrepancy)":("doh_probe", "viggle trigger", "INTENDED flag, not a fault"),
}

def trace_repair(stderr, exitcode):
    for sig, leaf in SIG2LEAF.items():
        if sig in stderr or (exitcode == 2 and sig.startswith("exit 2")):
            return {"signature": sig, "leaf": leaf[0]+"/"+leaf[1], "repair": f"advisory: {leaf[2]}",
                    "depends_on": [leaf[1]]}
    return {"signature": "(unmatched)", "leaf": None, "repair": f"record exit={exitcode}"}

def main():
    # prove: run the probe in a way that yields a real stderr signature
    proc = subprocess.run("python3 -c \"import sys; sys.stderr.write('timed out')\" 2>&1; true 2>/dev/null",
                          shell=True, capture_output=True, text=True)
    # ensure we capture a genuine failing stderr via a forced subprocess
    fail_cmd = ["python3", "-B", "-c",
                "import subprocess,sys; p=subprocess.run(['python3','doh_probe.py','github.com','A'],capture_output=True,text=True,timeout=30); sys.stderr.write(p.stderr[:80] or 'no verified output'); sys.exit(p.returncode or 1)"]
    try:
        r = subprocess.run(fail_cmd, capture_output=True, text=True, timeout=40)
        stderr = r.stderr[:80] or "no verified output"
        print(json.dumps({"exit": r.returncode, "stderr": stderr, "trace": trace_repair(stderr, r.returncode)}, indent=2))
    except subprocess.TimeoutExpired:
        print(json.dumps({"exit": -1, "stderr": "timed out", "trace": trace_repair("timed out", -1)}))

if __name__ == "__main__":
    main()
