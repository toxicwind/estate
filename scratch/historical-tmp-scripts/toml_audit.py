#!/usr/bin/env python3
"""Audit ${VAR} references in pitchfork.toml run/probe lines vs defined vars."""
import re, sys

toml_path = "/home/toxic/sovereign/pitchfork.toml"
ports_path = "/home/toxic/sovereign/config/ports.env"

text = open(toml_path).read()

# global vars from ports.env
gvars = set()
for line in open(ports_path):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        gvars.add(line.split("=", 1)[0].strip())

# parse daemon sections: name -> {env vars, run line, probe lines}
daemons = {}
cur = None
for line in text.splitlines():
    m = re.match(r'^\[daemons\.([^\]]+)\]', line)
    if m:
        cur = m.group(1)
        daemons[cur] = {"env": set(), "run": "", "probes": []}
        continue
    if cur is None:
        continue
    m = re.match(r'^env\s*=\s*\{(.*)\}', line)
    if m:
        for kv in m.group(1).split(","):
            if "=" in kv:
                daemons[cur]["env"].add(kv.split("=", 1)[0].strip())
    m = re.match(r'^run\s*=\s*"(.*)"\s*$', line)
    if m:
        daemons[cur]["run"] = m.group(1)
    if re.match(r'^(ready_|health_)', line.strip()):
        daemons[cur]["probes"].append(line.strip())

ref_re = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
print("=== run-line ${VAR} refs and whether VAR is defined ===")
for name, d in sorted(daemons.items()):
    for var in sorted(set(ref_re.findall(d["run"]))):
        defined = var in d["env"] or var in gvars
        print(f"{name}: run ${{{var}}} defined={defined}")
print()
print("=== probe-line (ready_/health_) ${VAR} refs — these NEVER expand ===")
for name, d in sorted(daemons.items()):
    for probe in d["probes"]:
        for var in sorted(set(ref_re.findall(probe))):
            print(f"{name}: {probe[:90]} -> ${{{var}}}")
print()
print("done")
