#!/usr/bin/env python3
"""w4-tripwire: storm tripwire checker + self-test.
Plan: (1) write storm_tripwire.py: reads LATEST.json, exits 2 (TRIPPED) when
storm_active and chat_hits >= threshold (default 10), else 0 (CLEAR);
(2) self-test on synthetic fixtures; (3) run against the real LATEST.json;
(4) RESULT.json.
"""
import json, os, time, subprocess, sys

WORK = os.path.dirname(os.path.abspath(__file__))
SEEDS = "/home/toxic/.shingle/coord/work/seeds"

TRIPWIRE = '''#!/usr/bin/env python3
import json, sys
p, thr = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 10
d = json.load(open(p))
if d.get("storm_active") and int(d.get("chat_hits", 0)) >= thr:
    print(f"TRIPPED storm_active=true chat_hits={d['chat_hits']} thr={thr}")
    sys.exit(2)
print(f"CLEAR storm_active={d.get('storm_active')} chat_hits={d.get('chat_hits')}")
'''
open(os.path.join(WORK, "storm_tripwire.py"), "w").write(TRIPWIRE)

def run(fixture, thr=10):
    p = os.path.join(WORK, fixture)
    r = subprocess.run([sys.executable, os.path.join(WORK, "storm_tripwire.py"), p, str(thr)],
                       capture_output=True, text=True)
    return r.returncode, r.stdout.strip()

# self-test fixtures
json.dump({"storm_active": True, "chat_hits": 74}, open(os.path.join(WORK, "fx_hot.json"), "w"))
json.dump({"storm_active": False, "chat_hits": 0}, open(os.path.join(WORK, "fx_cold.json"), "w"))
json.dump({"storm_active": True, "chat_hits": 3}, open(os.path.join(WORK, "fx_warm.json"), "w"))
t1 = run("fx_hot.json")
t2 = run("fx_cold.json")
t3 = run("fx_warm.json", thr=10)
assert t1[0] == 2 and "TRIPPED" in t1[1], t1
assert t2[0] == 0 and "CLEAR" in t2[1], t2
assert t3[0] == 0, t3  # below threshold -> clear

real = os.path.join(SEEDS, "LATEST.json")
live = run(real) if os.path.exists(real) else ("n/a", "no LATEST.json in seeds")

r = {"lane": "w4-tripwire",
     "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
     "claims": ["tripwire self-test 3/3 pass (hot trips, cold clear, sub-threshold clear)",
                f"live LATEST.json state: {live[1]}"],
     "evidence": {"selftest": {"hot": t1, "cold": t2, "warm": t3}, "live": live},
     "proof_files": ["storm_tripwire.py", "brief.py"]}
json.dump(r, open(os.path.join(WORK, "RESULT.json"), "w"), indent=1)
print(json.dumps(r, indent=1))
