#!/usr/bin/env python3
"""Apply the bridge-max MCP patch block to /home/toxic/awrawr_mcp.py.
Idempotent: refuses if already patched. Backs up the original first.
"""
import sys

TARGET = "/home/toxic/awrawr_mcp.py"
ANCHOR = "# --- hft race tool ---"
MARKER = "bridge-max: multitask + background dispatch"
BLOCK_SRC = "/home/toxic/sovereign/projects/bridge/yote/mcp_patch_block.py"


def main():
    orig = open(TARGET).read()
    if MARKER in orig:
        print("ALREADY_PATCHED")
        return 0
    if ANCHOR not in orig:
        print("ANCHOR_MISSING", file=sys.stderr)
        return 1
    block = open(BLOCK_SRC).read()
    open(TARGET + ".bak-20260920-bridgemax", "w").write(orig)
    patched = orig.replace(ANCHOR, block + "\n" + ANCHOR, 1)
    open(TARGET, "w").write(patched)
    print("PATCHED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
