#!/usr/bin/env python3
"""auto-hook-loader.py: Load all auto-hooks from /mnt/agents/dot/hooks/"""
import os, sys, subprocess, json
from pathlib import Path
from datetime import datetime

def ts():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

def load_hooks():
    hooks_dir = Path("/mnt/agents/dot/hooks")
    hooks_dir.mkdir(parents=True, exist_ok=True)
    loaded = []
    for f in sorted(hooks_dir.glob("*.sh")):
        if f.is_file() and not f.is_symlink():
            result = subprocess.run(["bash", "-c", f"source {f}"], capture_output=True, text=True, timeout=5)
            loaded.append(f.name)
            print(f"[{ts()}] Hook loaded: {f.name}")
    for f in sorted(hooks_dir.glob("*.py")):
        if f.is_file() and not f.is_symlink():
            exec(f.read_text(), {"__name__": "__hook__"})
            loaded.append(f.name)
            print(f"[{ts()}] Hook loaded: {f.name}")
    return loaded

if __name__ == "__main__":
    hooks = load_hooks()
    print(f"[{ts()}] Total hooks loaded: {len(hooks)}")
