#!/usr/bin/env python3
"""Call the awrawr-pc MCP exec bridge (Shingle's side).

SETUP (paste once):
  pip install "mcp<2"      # v1 API; v2 renamed the client entry point

USE:
  MCP_URL='https://<your-funnel-url>/mcp' MCP_TOKEN='<token>' \\
      python3 awrawr_mcp_client.py "echo ok && whoami"
  # optional 2nd arg: workdir, e.g. ... "ls -la" "/home/toxic/projects"

NOTE: the tool path is <funnel-url> + /mcp (FastMCP's default mount).
"""
import asyncio
import os
import sys

from mcp import ClientSession  # needs mcp<2
from mcp.client.streamable_http import streamablehttp_client


def _sanitize_no_proxy() -> None:
    # httpx crashes on bracketed IPv6 literals (e.g. "[::1]") in no_proxy
    # ("Invalid port: ':1]'"). The unbracketed forms are listed too, so
    # dropping the bracketed ones loses nothing.
    for var in ("no_proxy", "NO_PROXY"):
        val = os.environ.get(var)
        if val:
            os.environ[var] = ",".join(
                p for p in val.split(",") if not p.strip().startswith("[")
            )


_sanitize_no_proxy()


async def main() -> None:
    url = os.environ.get("MCP_URL")
    if not url:
        sys.exit("MCP_URL env var required, e.g. https://<machine>.<tailnet>.ts.net/mcp")
    token = os.environ.get("MCP_TOKEN")
    if not token:
        sys.exit("MCP_TOKEN env var required")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "echo ok"
    workdir = sys.argv[2] if len(sys.argv) > 2 else "/home/toxic"

    async with streamablehttp_client(url) as (read, write, _get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()
            res = await session.call_tool(
                "exec", {"token": token, "cmd": cmd, "workdir": workdir}
            )
            for block in res.content:
                print(getattr(block, "text", str(block)))


if __name__ == "__main__":
    asyncio.run(main())
