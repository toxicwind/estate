#!/usr/bin/env python3
"""Launch the secrets sweep on awrawr-pc: ship payload, clone, run detached."""
import subprocess
import sys

B64 = open("/tmp/sweep_all.b64").read().strip()

REMOTE = """mkdir -p /home/toxic/sweep-fleetchat-20260914 /home/toxic/sweep-openfang-20260914 /home/toxic/sweep-payload && cat > /home/toxic/sweep-payload/sweep_all.b64 <<'SWEEP_EOF'
""" + B64 + """
SWEEP_EOF
base64 -d /home/toxic/sweep-payload/sweep_all.b64 > /home/toxic/sweep-payload/sweep_all.py && rm -f /home/toxic/sweep-payload/sweep_all.b64 && chmod +x /home/toxic/sweep-payload/sweep_all.py && nohup bash -c 'echo CLONE_START >> /home/toxic/sweep-payload/run.log; gh repo clone toxicwind/fleet-chat /home/toxic/sweep-fleetchat-20260914/fleet-chat >> /home/toxic/sweep-payload/run.log 2>&1; echo FLEETCHAT_CLONED rc=$? >> /home/toxic/sweep-payload/run.log; gh repo clone toxicwind/openfang /home/toxic/sweep-openfang-20260914/openfang >> /home/toxic/sweep-payload/run.log 2>&1; echo OPENFANG_CLONED rc=$? >> /home/toxic/sweep-payload/run.log; python3 /home/toxic/sweep-payload/sweep_all.py /home/toxic/sweep-fleetchat-20260914/fleet-chat /home/toxic/sweep-openfang-20260914/openfang > /home/toxic/sweep-payload/sweep-results.json 2>> /home/toxic/sweep-payload/run.log; echo SWEEP_DONE rc=$? >> /home/toxic/sweep-payload/run.log' > /dev/null 2>&1 & echo LAUNCHED"""

r = subprocess.run(
    ["python3", "/home/hatch/workspace/skills/awrawr-mcp/bin/exec.py",
     REMOTE, "/home/toxic"],
    capture_output=True, text=True, timeout=600)
print("RC:", r.returncode)
print("OUT:", r.stdout[-2000:])
print("ERR:", r.stderr[-2000:])
