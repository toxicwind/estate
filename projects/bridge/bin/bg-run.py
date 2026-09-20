#!/usr/bin/env python3
"""bg-run.py — detached background command runner (bridge-max).

Launched fully detached from the bridge exec lane, e.g.:
    setsid nohup python3 bg-run.py <handle> <cmdb64> >launcher.log 2>&1 < /dev/null &

State dir: /home/toxic/.cache/bridge-bg/<handle>/
    cmd.txt      the decoded command
    status.json  {"state": "running"|"done", "pid", "started", "finished"?, "code"?}
    stdout.log / stderr.log   captured output (unbounded via files, not memory)

The launcher is expected to run with cwd set to the state dir so `&` binds
only to this process (see AGENTS.md: daemon-start `&` scoping). This script
does NOT daemonize itself — detachment is the launcher's job via setsid.

Status writes are atomic (write tmp + os.replace) so readers never see
a torn file. Poll-free: readers just `cat status.json`.
"""

import base64
import json
import os
import re
import subprocess
import sys
import time

BASE = "/home/toxic/.cache/bridge-bg"
HANDLE_RX = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _wjson(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f)
    os.replace(tmp, path)


def main():
    if len(sys.argv) != 3:
        print("usage: bg-run.py <handle> <cmdb64>", file=sys.stderr)
        return 2
    handle, cmdb64 = sys.argv[1], sys.argv[2]
    if not HANDLE_RX.match(handle):
        print("bad handle", file=sys.stderr)
        return 2
    d = os.path.join(BASE, handle)
    os.makedirs(d, exist_ok=True)
    try:
        cmd = base64.b64decode(cmdb64.encode()).decode("utf-8", "replace")
    except Exception as e:
        print("bad cmdb64: %s" % e, file=sys.stderr)
        return 2
    with open(os.path.join(d, "cmd.txt"), "w") as f:
        f.write(cmd)

    st_path = os.path.join(d, "status.json")
    started = time.time()
    _wjson(st_path, {"state": "running", "pid": os.getpid(),
                     "started": started, "cmd": cmd[:500]})

    code = 1
    try:
        with open(os.path.join(d, "stdout.log"), "wb") as out, \
             open(os.path.join(d, "stderr.log"), "wb") as err:
            p = subprocess.run(cmd, shell=True, cwd="/home/toxic",
                               stdout=out, stderr=err)
            code = p.returncode
    except Exception as e:
        with open(os.path.join(d, "stderr.log"), "ab") as err:
            err.write(("bg-run failed: %s: %s\n"
                       % (type(e).__name__, e)).encode())
    finally:
        _wjson(st_path, {"state": "done", "pid": os.getpid(),
                         "started": started, "finished": time.time(),
                         "code": code, "cmd": cmd[:500]})
    return 0


if __name__ == "__main__":
    sys.exit(main())
