#!/usr/bin/env python3
"""Process management"""
import psutil

def list_sovereign_processes():
    procs = []
    for p in psutil.process_iter(["pid", "name", "cmdline"]):
        cmd = " ".join(p.info["cmdline"] or [])
        if "sovereign" in cmd or "llama" in cmd or "nfcot" in cmd:
            procs.append(p.info)
    return procs

def kill_port(port):
    for conn in psutil.net_connections():
        if conn.laddr.port == port and conn.pid:
            psutil.Process(conn.pid).terminate()
