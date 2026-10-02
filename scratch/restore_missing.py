#!/usr/bin/env python3
"""Restore the 696 missing files from stash@{2} into the working tree."""
import json, subprocess

ROOT = "/home/toxic/sovereign"
r = json.load(open("/home/toxic/stash-merge-20260914/stash2-audit.json"))
missing = r["missing"]
print("missing count:", len(missing))

CHUNK = 100
restored, failed = 0, []
for i in range(0, len(missing), CHUNK):
    chunk = missing[i:i + CHUNK]
    p = subprocess.run(["git", "checkout", "stash@{2}", "--"] + chunk,
                       cwd=ROOT, capture_output=True, text=True)
    if p.returncode == 0:
        restored += len(chunk)
    else:
        failed.append((chunk, p.stderr.strip()[:200]))

print("restored:", restored)
print("failed chunks:", len(failed))
for chunk, err in failed[:5]:
    print("FAIL:", chunk[:3], err[:150])

# verify
import os
still_missing = [p for p in missing if not os.path.lexists(os.path.join(ROOT, p))]
print("still missing after restore:", len(still_missing))
json.dump(still_missing, open("/home/toxic/stash-merge-20260914/still-missing.json", "w"))
