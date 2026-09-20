#!/usr/bin/env python3
"""Apply the mcp-smith MCP patch block to /home/toxic/awrawr_mcp.py.
Idempotent: refuses if already patched. Backs up the original first.
Same pattern as bridge-max's apply_mcp_patch.py.
"""
import sys

TARGET = "/home/toxic/awrawr_mcp.py"
ANCHOR = "# --- hft race tool ---"
MARKER = "mcp-smith: fleet / introspection / bg tools"
BLOCK_SRC = "/home/toxic/sovereign/projects/bridge/yote/mcp_patch_block_mcp_smith.py"


def main():
    orig = open(TARGET).read()
    if MARKER in orig:
        print("ALREADY_PATCHED")
        return 0
    if ANCHOR not in orig:
        print("ANCHOR_MISSING", file=sys.stderr)
        return 1
    block = open(BLOCK_SRC).read()
    open(TARGET + ".bak-20260920-mcpsmith", "w").write(orig)
    patched = orig.replace(ANCHOR, block + "\n" + ANCHOR, 1)
    open(TARGET, "w").write(patched)
    print("PATCHED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
