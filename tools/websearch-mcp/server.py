#!/usr/bin/env python3
"""websearch-mcp: stdio MCP server wrapping the websearch-skill CLI.

websearch-skill 0.6.1 ships NO MCP server (README: "There is no MCP server;
use the CLI directly"). This wrapper exposes its agent commands
(web-search, web-fetch, arxiv, github) as MCP tools over stdio using
Content-Length framing, matching the protocol of tools/tmux-mcp/server.ts.

Durable: pure stdlib, no deps beyond `uv`/`uvx` and the websearch-skill
package (fetched by uvx on first run, then cached).
"""
import json
import subprocess
import sys

SERVER_INFO = {"name": "websearch-mcp", "version": "1.0.0"}

TOOLS = [
    {
        "name": "web_search",
        "description": "Keyless multi-engine web search. Returns ranked, deduplicated results with reusable handles.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "default": 10},
                "detail": {"type": "string", "enum": ["concise", "detailed"], "default": "concise"},
                "freshness": {"type": "string", "enum": ["any", "day", "week", "month", "year"], "default": "any"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "web_fetch",
        "description": "Fetch a page as clean Markdown. Takes a search-result handle or a URL.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Result handle from web_search, or a URL"},
                "page": {"type": "integer", "default": 1},
            },
            "required": ["target"],
        },
    },
    {
        "name": "arxiv_search",
        "description": "Search arXiv papers. Returns structured metadata (authors, abstract, categories, links).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "field": {"type": "string", "enum": ["all", "title", "author", "abstract"], "default": "all"},
                "max_results": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "github_search",
        "description": "Search GitHub repositories. Returns typed fields (stars, language, topics).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "language": {"type": "string"},
                "max_results": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
    },
]


def run_cli(args, timeout=120):
    """Run `uvx websearch-skill ... --json`, return (ok, text)."""
    cmd = ["uvx", "websearch-skill"] + args + ["--json"]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, "websearch CLI timed out after %ds" % timeout
    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    if p.returncode != 0 and not out:
        return False, "websearch CLI failed (rc=%d): %s" % (p.returncode, err[-500:])
    return True, out or err


def call_tool(name, args):
    args = args or {}
    if name == "web_search":
        a = [args["query"], "--max-results", str(args.get("max_results", 10)),
             "--detail", args.get("detail", "concise")]
        if args.get("freshness", "any") != "any":
            a += ["--freshness", args["freshness"]]
        return run_cli(["web-search"] + a)
    if name == "web_fetch":
        return run_cli(["web-fetch", args["target"], "--page", str(args.get("page", 1))])
    if name == "arxiv_search":
        return run_cli(["arxiv", args["query"], "--field", args.get("field", "all"),
                        "--max-results", str(args.get("max_results", 10))])
    if name == "github_search":
        a = [args["query"], "--max-results", str(args.get("max_results", 10))]
        if args.get("language"):
            a += ["--language", args["language"]]
        return run_cli(["github"] + a)
    return False, "unknown tool: %s" % name


def read_message():
    """Read one Content-Length-framed JSON-RPC message from stdin."""
    headers = {}
    while True:
        line = sys.stdin.buffer.readline().decode("latin1")
        if not line:
            return None
        line = line.strip()
        if not line:
            break
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None
    return json.loads(sys.stdin.buffer.read(length).decode("utf-8"))


def send_message(obj):
    body = json.dumps(obj).encode("utf-8")
    sys.stdout.buffer.write(b"Content-Length: %d\r\n\r\n" % len(body) + body)
    sys.stdout.buffer.flush()


def main():
    while True:
        msg = read_message()
        if msg is None:
            break
        mid = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params") or {}
        try:
            if method == "initialize":
                result = {"protocolVersion": "2024-11-05",
                          "capabilities": {"tools": {}},
                          "serverInfo": SERVER_INFO}
            elif method.startswith("notifications/"):
                result = {}
            elif method == "tools/list":
                result = {"tools": TOOLS}
            elif method == "tools/call":
                ok, text = call_tool(params.get("name"), params.get("arguments"))
                result = {"content": [{"type": "text", "text": text}],
                          "isError": not ok}
            else:
                send_message({"jsonrpc": "2.0", "id": mid,
                              "error": {"code": -32601, "message": "method not found"}})
                continue
            send_message({"jsonrpc": "2.0", "id": mid, "result": result})
        except Exception as e:  # never die on a bad call
            send_message({"jsonrpc": "2.0", "id": mid,
                          "error": {"code": -32603, "message": str(e)[:500]}})


if __name__ == "__main__":
    main()
