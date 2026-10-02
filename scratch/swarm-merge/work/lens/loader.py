#!/usr/bin/env python3.12
"""
lens_loader.py — Dynamic Lens Profile Loader
Discovers and loads all lens_*.py modules in the current directory.
No hardcoded list; scans at runtime.
"""
import os, sys, importlib.util, json, time
from pathlib import Path

def ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")

def discover_lenses(directory: str = ".") -> list:
    lenses = []
    for f in sorted(Path(directory).glob("lens_*.py")):
        if f.name == "lens_loader.py":
            continue
        spec = importlib.util.spec_from_file_location(f.stem, f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for attr in dir(mod):
            cls = getattr(mod, attr)
            if isinstance(cls, type) and hasattr(cls, 'name') and hasattr(cls, 'analyze'):
                lenses.append(cls())
    return lenses

def load_lens_module(path: str):
    """Load a single lens_*.py module by path; returns the module object."""
    f = Path(path)
    spec = importlib.util.spec_from_file_location(f.stem, f)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def apply_all(data: dict, directory: str = ".") -> dict:
    lenses = discover_lenses(directory)
    print(f"[{ts()}] Discovered {len(lenses)} lens profiles")
    results = {}
    for lens in lenses:
        try:
            results[lens.name] = lens.analyze(data)
        except Exception as e:
            results[lens.name] = {"error": str(e)}
    return results

def main():
    sample = {"text": "The star people came from the sky. Contact: test@kimi.ai"}
    print(json.dumps(apply_all(sample), indent=2))

if __name__ == "__main__":
    main()
