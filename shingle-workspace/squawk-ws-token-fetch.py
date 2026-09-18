#!/usr/bin/env python3
"""Fetch the squawk-ws bearer token from awrawr-pc via the MCP bridge and
write it to ~/hooks/state/squawk-ws.token (0600). The token value is never
printed; only the character count is reported."""
import os
import subprocess
import sys
from pathlib import Path

BRIDGE = os.path.expanduser("~/workspace/skills/awrawr-mcp/bin/exec.py")
REMOTE_TOKEN = "/home/toxic/.squawk-ws-token"
DEST = Path(os.path.expanduser("~/hooks/state/squawk-ws.token"))


def main():
    cmd = "printf 'TOK_BEGIN\\n'; cat " + REMOTE_TOKEN + "; printf '\\nTOK_END\\n'"
    p = subprocess.run([sys.executable, BRIDGE, cmd],
                       capture_output=True, text=True, timeout=120)
    out = p.stdout
    try:
        token = out.split("TOK_BEGIN\n", 1)[1].split("\nTOK_END", 1)[0].strip()
    except IndexError:
        print("token fetch failed: markers missing", file=sys.stderr)
        print("bridge stderr: %.200s" % p.stderr, file=sys.stderr)
        return 1
    if len(token) < 16 or any(c.isspace() for c in token):
        print("token fetch failed: malformed token", file=sys.stderr)
        return 1
    DEST.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(DEST, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(token + "\n")
    print("wrote %d chars to %s (0600)" % (len(token), DEST))
    return 0


if __name__ == "__main__":
    sys.exit(main())
