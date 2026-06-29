#!/usr/bin/env python3
"""Log aggregation"""
import glob
import os

LOG_DIR = "/home/toxic/sovereign/logs"

def tail_log(name, lines=50):
    path = os.path.join(LOG_DIR, f"{name}.log")
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return f.readlines()[-lines:]

def list_logs():
    return glob.glob(f"{LOG_DIR}/*.log")
