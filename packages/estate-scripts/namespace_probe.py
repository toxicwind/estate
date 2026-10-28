#!/usr/bin/env python3
"""
namespace_probe.py: Linux namespace & capability audit tool.
"""
import os, ctypes, json
from pathlib import Path

def probe():
    data = {
        "uid": os.getuid(),
        "gid": os.getgid(),
        "pid": os.getpid(),
        "uname": os.uname()._asdict(),
        "namespaces": {},
        "capabilities": {},
    }
    ns_dir = Path("/proc/self/ns")
    if ns_dir.exists():
        for ns in ns_dir.iterdir():
            data["namespaces"][ns.name] = os.readlink(ns)

    with open("/proc/self/status") as f:
        for line in f:
            if line.startswith(("Cap", "Seccomp", "NoNewPrivs")):
                k, v = line.strip().split(":", 1)
                data["capabilities"][k.strip()] = v.strip()

    return data

if __name__ == "__main__":
    print(json.dumps(probe(), indent=2))
