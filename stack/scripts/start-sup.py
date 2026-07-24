#!/usr/bin/env python3
import subprocess, os, sys

os.chdir('/home/toxic/sovereign')

# Clean state
state_file = os.path.expanduser('~/.local/state/pitchfork/state.toml')
if os.path.exists(state_file):
    os.remove(state_file)

sock_dir = os.path.expanduser('~/.local/state/pitchfork/sock')
if os.path.isdir(sock_dir):
    for f in os.listdir(sock_dir):
        os.remove(os.path.join(sock_dir, f))

# Start supervisor
r = subprocess.run(
    ['/home/toxic/.local/bin/pitchfork', 'supervisor', 'start'],
    stdin=subprocess.DEVNULL,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    timeout=15
)

import time
time.sleep(2)

# Check status
r2 = subprocess.run(
    ['/home/toxic/.local/bin/pitchfork', 'supervisor', 'status'],
    capture_output=True, text=True, timeout=10
)

# Write results to file
with open('/tmp/pf_results.txt', 'w') as f:
    f.write(f"supervisor_start_rc={r.returncode}\n")
    f.write(f"supervisor_status_rc={r2.returncode}\n")
    f.write(f"status_stdout={r2.stdout[:500]}\n")
    f.write(f"status_stderr={r2.stderr[:500]}\n")

print("DONE")
