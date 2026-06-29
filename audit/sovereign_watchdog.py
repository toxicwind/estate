#!/usr/bin/env python3
"""Sovereign Watchdog — Monitors stack health"""

import json
import os
import time
from datetime import datetime

CHECK_INTERVAL = 30
LOG_FILE = "/home/toxic/sovereign/logs/watchdog.log"
STATUS_FILE = "/home/toxic/sovereign/logs/watchdog_status.json"

PROCESSES = {
    "llama-server": {"port": 25001, "health": "/health"},
    "nfcot-proxy": {"port": 25008, "health": "/v1/models"},
    "openfang": {"port": 25004, "health": None},
}

def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def check_port(port):
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except:
        return False

def main():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    log("Watchdog started")
    while True:
        status = {}
        for name, cfg in PROCESSES.items():
            ok = check_port(cfg["port"]) if cfg["health"] else True
            status[name] = "healthy" if ok else "down"
            if not ok:
                log(f"ALERT: {name} on port {cfg['port']} is DOWN")
        with open(STATUS_FILE, "w") as f:
            json.dump(status, f, indent=2)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
