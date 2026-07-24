#!/usr/bin/env python3
"""Start pitchfork supervisor with complete FD isolation."""

import os
import subprocess
import sys
import time

os.chdir("/home/toxic/sovereign")

# Clean stale state
state_file = os.path.expanduser("~/.local/state/pitchfork/state.toml")
if os.path.exists(state_file):
    os.remove(state_file)
sock_dir = os.path.expanduser("~/.local/state/pitchfork/sock")
if os.path.isdir(sock_dir):
    for f in os.listdir(sock_dir):
        try:
            os.remove(os.path.join(sock_dir, f))
        except:
            pass

# Create /dev/null and /dev/urandom FDs for pitchfork
devnull_fd = os.open(os.devnull, os.O_RDWR)
devurand_fd = os.open("/dev/urandom", os.O_RDONLY)

# Fork to completely detach from TTY
pid = os.fork()
if pid > 0:
    # Parent waits and reports
    os.waitpid(pid, 0)
    time.sleep(2)
    with open("/tmp/pf_results.txt", "w") as f:
        f.write(f"child_done\n")
    sys.exit(0)
else:
    # Child - completely detach
    os.setsid()
    os.dup2(devnull_fd, 0)  # stdin -> /dev/null
    os.dup2(devnull_fd, 1)  # stdout -> /dev/null
    os.dup2(devnull_fd, 2)  # stderr -> /dev/null
    os.close(devnull_fd)
    os.close(devurand_fd)

    # Now exec pitchfork
    os.execvp(
        "/home/toxic/.local/bin/pitchfork",
        ["/home/toxic/.local/bin/pitchfork", "supervisor", "start"],
    )
