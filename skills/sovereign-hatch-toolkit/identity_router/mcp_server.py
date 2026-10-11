#!/usr/bin/env python3
"""
Zero-dependency stdlib Model Context Protocol (MCP) stdio Server.
Complies strictly with JSON-RPC 2.0 and MCP specification (2024-11-05).
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Local package imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from identity_router.identity_parser import parse_identity_file
from identity_router.router import LessonRouter, OWNERSHIP_TABLE

SERVER_NAME = "sovereign-identity-router"
SERVER_VERSION = "1.0.0"
PROTOCOL_VERSION = "2024-11-05"

TOOLS = [
    {
        "name": "current_identity",
        "description": "Returns current agent identity (name, character, vibe, emoji, posture).",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "route_lesson",
        "description": "Scores a durable lesson against the six standing files and recommends destination.",
        "inputSchema": {
            "type": "object",
            "properties": {"lesson": {"type": "string", "description": "The durable lesson text"}},
            "required": ["lesson"],
            "additionalProperties": False,
        },
    },
    {
        "name": "standing_files",
        "description": "Returns the standing files ownership mapping table.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "hatch_gateway_status",
        "description": "Returns active Hatch/Noise gateway telemetry parameters.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    }
]

router = LessonRouter()


def handle_tool_call(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Executes a tool call and returns MCP content structure."""
    if name == "current_identity":
        content = json.dumps(parse_identity_file(), indent=2)
        return {"content": [{"type": "text", "text": content}]}
    elif name == "route_lesson":
        lesson = args.get("lesson", "")
        if not lesson:
            return {"content": [{"type": "text", "text": "error: 'lesson' argument is required"}], "isError": True}
        content = json.dumps(router.route(lesson), indent=2)
        return {"content": [{"type": "text", "text": content}]}
    elif name == "standing_files":
        content = json.dumps(OWNERSHIP_TABLE, indent=2)
        return {"content": [{"type": "text", "text": content}]}
    elif name == "hatch_gateway_status":
        cfg_path = Path(__file__).parent.parent / "config" / "gateway_config.json"
        if cfg_path.exists():
            content = cfg_path.read_text(encoding="utf-8")
        else:
            content = json.dumps({"status": "active", "transport": "noise"})
        return {"content": [{"type": "text", "text": content}]}
    return {"content": [{"type": "text", "text": f"error: unknown tool '{name}'"}], "isError": True}


def process_message(raw_line: str) -> Optional[str]:
    """Processes a single JSON-RPC line and returns serialized response (if applicable)."""
    line = raw_line.strip()
    if not line:
        return None

    try:
        req = json.loads(line)
    except json.JSONDecodeError as jde:
        return json.dumps({
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32700, "message": f"Parse error: {jde}"}
        })

    if not isinstance(req, dict):
        return json.dumps({
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32600, "message": "Invalid Request: expected JSON object"}
        })

    req_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {}) or {}

    # Handle notifications (no id)
    if req_id is None:
        if method == "notifications/initialized":
            # Handshake complete notification
            return None
        return None

    if method == "initialize":
        res = {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {
                "tools": {
                    "listChanged": False
                }
            },
            "serverInfo": {
                "name": SERVER_NAME,
                "version": SERVER_VERSION
            }
        }
        return json.dumps({"jsonrpc": "2.0", "id": req_id, "result": res})

    elif method == "ping":
        return json.dumps({"jsonrpc": "2.0", "id": req_id, "result": {}})

    elif method == "tools/list":
        return json.dumps({"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}})

    elif method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})
        call_res = handle_tool_call(tool_name, tool_args)
        return json.dumps({"jsonrpc": "2.0", "id": req_id, "result": call_res})

    else:
        return json.dumps({
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method '{method}' not found"}
        })


def main():
    """Stdio loop reading lines and dispatching JSON-RPC frames."""
    for line in sys.stdin:
        resp = process_message(line)
        if resp is not None:
            sys.stdout.write(resp + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
