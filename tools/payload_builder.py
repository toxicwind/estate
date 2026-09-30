"""Build the correct Gemini payload by pulling live gatehouse tools.

Facts learned empirically:
  - Gemini `/v1beta/interactions` REJECTS `type: "mcp_server"` (400).
  - It accepts individual `type: "function"` entries with
    `defer_loading: true` alongside `{"type": "tool_search"}`.
  - The server then performs tool_search against those declarations.

So: fetch tools/list from gatehouse, convert each to a Gemini function
declaration, add tool_search, and let Gemini do its own retrieval.
"""
import json, sys, os
sys.path.insert(0, os.path.expanduser("~/sovereign"))
from tools.mcp_client import connect

SYSTEM_PROMPT = """You call tools through a gatehouse MCP server.

MANDATORY WORKFLOW:
  1. Call retrieve_tools with a query describing what you need.
  2. Pick the exact 'id' from the results. Never invent names.
  3. Call call_tool_read (default) or call_tool_destructive (only if
     the tool name contains: delete, remove, drop, revoke, disable,
     destroy, purge, reset, clear, unsubscribe, cancel, terminate,
     close, archive, ban, block, disconnect, kill, wipe, truncate,
     force, hard).
  4. If sig shows lossy=true, call describe_tool first.

Skipping step 1 fails with 'Missing required parameter name'.
"""

def _fn_from_mcp(tool: dict) -> dict:
    schema = tool.get("inputSchema") or {"type":"object","properties":{}}
    return {
        "type": "function",
        "name": tool["name"],
        "description": (tool.get("description") or "")[:1024],
        "defer_loading": True,
        "parameters": schema,
    }

def build(input_text: str, *, session=None) -> dict:
    s = session or connect()
    tools = s.list_tools()
    if not tools:
        raise RuntimeError("gatehouse returned no tools")
    fns = [_fn_from_mcp(t) for t in tools]
    return {
        "model": "gemini-flash-tool-retrieval",
        "input": input_text,
        "system_instruction": SYSTEM_PROMPT,
        "tools": [{"type":"tool_search"}] + fns,
    }

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "git status"
    print(json.dumps(build(q), indent=2))
