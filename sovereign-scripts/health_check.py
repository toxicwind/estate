#!/usr/bin/env python3
"""Health check for sovereign environment."""
import os, json, sys, socket, subprocess
from pathlib import Path

def check_port(host, port, timeout=2):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        return True
    except:
        return False

def main():
    results = {
        "timestamp": subprocess.check_output(["date", "-Iseconds"]).decode().strip(),
        "services": {},
        "files": {},
        "env": {},
    }

    # Service checks
    services = [("kernel-server", 8888), ("portal", 8080), ("envd", 49983), ("cdp", 9222), ("vnc", 6080)]
    for name, port in services:
        results["services"][name] = "up" if check_port("127.0.0.1", port) else "down"

    # File checks
    results["files"][".env"] = Path("/mnt/agents/.env").exists()
    results["files"]["dot"] = Path("/mnt/agents/dot").exists()
    results["files"]["mitm-proxy"] = Path("/mnt/agents/mitm-proxy").exists()

    # Env checks
    results["env"]["GITHUB_TOKEN"] = bool(os.environ.get("GITHUB_TOKEN"))
    results["env"]["PATH_HAS_AGENTS"] = "/mnt/agents/bin" in os.environ.get("PATH", "")

    print(json.dumps(results, indent=2))
    return 0 if all(results["services"].values()) else 1

if __name__ == "__main__":
    sys.exit(main())
