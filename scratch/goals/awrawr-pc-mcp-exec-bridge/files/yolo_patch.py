#!/usr/bin/env python3
"""Add '#yolo ' prefix override to ~/awrawr_mcp.py.

Fail-fast: each target must occur exactly once or we abort with
no changes written.
Usage: yolo_patch.py [path]   (default: /home/toxic/awrawr_mcp.py)
"""
import sys

P = sys.argv[1] if len(sys.argv) > 1 else "/home/toxic/awrawr_mcp.py"
src = open(P).read()
orig = src


def rep(old, new):
    global src
    n = src.count(old)
    if n != 1:
        print(f"FATAL: expected 1 occurrence, found {n}: {old[:70]!r}")
        sys.exit(1)
    src = src.replace(old, new)


# 1. document YOLO in the module docstring
rep(
    '''shell on the box. The token is the real security boundary.
"""''',
    '''shell on the box. The token is the real security boundary.
YOLO: prefix a command with '#yolo ' to bypass the command policy entirely
(still authenticated, still audited - flagged yolo:true).
"""''',
)

# 2. document YOLO in the tool docstring
rep(
    '''    """Run a shell command on awrawr-pc (subject to command policy)."""''',
    '''    """Run a shell command on awrawr-pc (subject to command policy).

    Prefix with '#yolo ' to bypass the policy entirely - only when you
    really mean it. YOLO calls are flagged in the audit log.
    """''',
)

# 3. detect/strip the prefix and skip the policy check
rep(
    '''    t0 = time.monotonic()
    base = {"cmd": cmd[:500], "workdir": workdir}

    denied = _policy_check(cmd)''',
    '''    t0 = time.monotonic()
    orig_cmd = cmd
    yolo = cmd.startswith("#yolo ")
    if yolo:
        cmd = cmd[len("#yolo "):].lstrip()
    base = {"cmd": orig_cmd[:500], "workdir": workdir, "yolo": yolo}

    denied = None if yolo else _policy_check(cmd)''',
)

if src == orig:
    print("FATAL: no changes made")
    sys.exit(1)
open(P, "w").write(src)
print("PATCHED OK")
