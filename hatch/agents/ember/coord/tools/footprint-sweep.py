#!/usr/bin/env python3
"""Cinder footprint-sweep: derive each live lane's shared-resource footprint and flag overlaps.

Read-only analyzer. Rationale (borrowed from the sheaf-agreement literature):
lanes are overlapping local views of the fleet; deconfliction is checking
agreement on the resources they share (ports, claims, declared items).
A shared port/claim touched by two non-done lanes is a candidate conflict.

Usage: footprint-sweep.py [coord_dir]
Output: JSON {footprints: {lane: {ports, claims_held, explicit}}, overlaps: {kind: {key: [lanes]}}}
"""
import json
import os
import re
import sys

COORD = sys.argv[1] if len(sys.argv) > 1 else "/home/toxic/sovereign/hatch/agents/ember/coord"
PORT_RE = re.compile(r":(\d{4,5})\b")
LIVE = {"active", "in-progress", "blocked", "running"}


def load_dir(d):
    out = {}
    if not os.path.isdir(d):
        return out
    for f in sorted(os.listdir(d)):
        if f.endswith(".json"):
            with open(os.path.join(d, f)) as fh:
                try:
                    out[f[:-5]] = json.load(fh)
                except json.JSONDecodeError:
                    out[f[:-5]] = {"_parse_error": True}
    return out


lanes = load_dir(os.path.join(COORD, "lanes"))
claims = load_dir(os.path.join(COORD, "claims"))
now = os.path.getmtime  # placeholder, unused

# live claims: claimed_at + ttl_s > now (epoch); fall back to listing all with holder
import time
live_claims = {}
for cname, c in claims.items():
    try:
        live = c.get("claimed_at", 0) + c.get("ttl_s", 0) > time.time()
    except TypeError:
        live = None
    live_claims[cname] = {"claimed_by": c.get("claimed_by"), "live": live,
                          "note": c.get("note", "")[:80]}

footprints = {}
for name, lane in lanes.items():
    status = str(lane.get("status", "")).lower()
    if status == "done":
        continue
    text = json.dumps(lane)
    ports = sorted(set(PORT_RE.findall(text)))
    fp = {"status": status, "ports": ports, "claims_held": [],
          "explicit": lane.get("shared", {}) or {}}
    holder_names = {name, lane.get("owner", ""), lane.get("agent_id", "")}
    for cname, c in live_claims.items():
        if c["claimed_by"] and any(h and h in str(c["claimed_by"]) for h in holder_names if h):
            fp["claims_held"].append(cname)
    footprints[name] = fp

res2lanes = {}
for lname, fp in footprints.items():
    for p in fp["ports"]:
        res2lanes.setdefault(("port", p), set()).add(lname)
    for cl in fp["claims_held"]:
        res2lanes.setdefault(("claim", cl), set()).add(lname)
    for k, v in fp["explicit"].items():
        vals = v if isinstance(v, list) else [v]
        for val in vals:
            res2lanes.setdefault(("explicit:" + k, str(val)), set()).add(lname)

overlaps = {}
for (kind, key), owners in sorted(res2lanes.items(), key=lambda x: (x[0][0], x[0][1])):
    if len(owners) > 1:
        overlaps.setdefault(kind, {})[key] = sorted(owners)

print(json.dumps({
    "live_lanes": sorted(footprints),
    "footprints": footprints,
    "live_claims": live_claims,
    "overlaps": overlaps,
}, indent=2))
