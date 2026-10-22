#!/usr/bin/env python3
"""Semantic-strength oracle for DoH.
Filters UNTRIGGERED tasks (fault never fired) and critiques output strength:
a pass must carry a real numeric artifact (TTL delta, IP set, verdict), not a
token. Scores STRONG/WEAK/FAKE.
"""
import json, subprocess, re

def strength(out):
    s = 0.0
    if "vjTrigger" in out or "discrepancy" in out: s += 0.35
    if "ttl_delta" in out and re.search(r'"ttl_delta"\s*:\s*-?[0-9]+', out): s += 0.3
    if '"ips"' in out and re.search(r'140\.', out): s += 0.25
    if "ip_differ" in out: s += 0.1
    if "untriggered" in out or "fired" not in out: s -= 0.4   # untriggered/fake penalty
    return round(min(max(s,0),1),2)

def main():
    # force the real probe; also feed injected (fired) variants
    r = subprocess.run(["python3","doh_probe.py","github.com","A"], capture_output=True, text=True, timeout=30)
    out = r.stdout
    st = strength(out)
    verdict = "STRONG" if st >= 0.7 else ("WEAK" if 0.4 <= st < 0.7 else "FAKE")
    print(json.dumps({"exit": r.returncode, "strength": st, "verdict": verdict,
                      "untriggered": "untriggered" in out and "fired" not in out}, indent=2))

if __name__ == "__main__":
    main()
