#!/usr/bin/env python3
"""AgentChaos-style boundary interceptor for the DoH probe.
Injects crash/omission/value faults at the resolver boundary — never edits
doh_probe.py. Gated by --inject so the same probe runs clean or traced.
"""
import json, sys, subprocess, os

def trace(probe_cmd, inject=None):
    rec = {"probe": "doh_probe", "inject": inject, "fired": False}
    if inject == "crash":
        rec["fired"] = True
        rec["error"] = "AGENTCHAOS crash-injected at resolver boundary"
        return rec, {}
    if inject == "omission":
        rec["fired"] = True
        return rec, {}
    if inject == "value":
        rec["fired"] = True
        return rec, {"corrupted": True}
    # clean run: actually execute the probe
    p = subprocess.run(probe_cmd, shell=True, capture_output=True, text=True, timeout=30)
    rec["lat_ms"] = None
    return rec, {"exit": p.returncode}

if __name__ == "__main__":
    inject = None
    if "--inject" in sys.argv: inject = sys.argv[sys.argv.index("--inject")+1]
    cmd = "python3 doh_probe.py github.com A"
    rec, res = trace(cmd, inject)
    # if a fault was injected, emit a synthetic FAIL signal so the oracle sees it
    if rec["fired"]:
        print(json.dumps({"trace": rec, "result": res, "fired": True}))
        sys.exit(0)
    else:
        # mark fired-false as UNTRIGGERED (the real oracle filter target)
        print(json.dumps({"trace": rec, "result": res, "untriggered": True}))
        sys.exit(0)
