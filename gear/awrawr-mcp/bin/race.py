#!/usr/bin/env python3
"""race.py — race the awrawr-pc bridge transports head to head.

Transports:
  ws    persistent wss:// connection via local ws_daemon (streaming)
  https MCP streamable-HTTP with cached session id (buffered)

For each command, runs 3 iterations per transport and reports median wall
time plus median time-to-first-byte (TTFB). TTFB shows the streaming win:
HTTPS buffers the whole command; WS prints chunks as they arrive.
"""
import os
import statistics
import subprocess
import sys
import time

SKILL_BIN = os.path.dirname(os.path.abspath(__file__))
EXEC = os.path.join(SKILL_BIN, "exec.py")

COMMANDS = [
    ("tiny", "echo quick"),
    ("early-output", "echo start; sleep 3; echo end"),
    ("throughput", "seq 1 200000 | md5sum"),
    ("realistic", "fd --version && rg --version | head -1"),
]


def run_once(cmd, transport):
    env = dict(os.environ, AWRAWR_TRANSPORT=transport)
    t0 = time.monotonic()
    p = subprocess.Popen([sys.executable, EXEC, cmd, "/home/toxic"],
                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                         env=env)
    first = None
    # read a byte at a time until first output, then drain
    out = b""
    while True:
        blk = p.stdout.read(1)
        if not blk:
            break
        if first is None:
            first = time.monotonic() - t0
        out += blk
        if len(out) > 65536:
            out += p.stdout.read()
            break
    p.wait()
    wall = time.monotonic() - t0
    return wall, first if first is not None else wall, p.returncode


def main():
    print(f"{'command':<14}{'transport':<8}{'wall med':<10}{'ttfb med':<10}rc")
    for name, cmd in COMMANDS:
        for transport in ("ws", "https"):
            walls, tfbs, rcs = [], [], []
            for _ in range(3):
                w, f, rc = run_once(cmd, transport)
                walls.append(w)
                tfbs.append(f)
                rcs.append(rc)
            print(f"{name:<14}{transport:<8}"
                  f"{statistics.median(walls):<10.3f}"
                  f"{statistics.median(tfbs):<10.3f}{rcs[0]}")


if __name__ == "__main__":
    main()
