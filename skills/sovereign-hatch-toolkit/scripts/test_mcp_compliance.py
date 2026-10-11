#!/usr/bin/env python3
"""
Standalone JSON-RPC 2.0 / MCP Protocol Compliance Verification Harness.
Validates stdio framing, handshake initialization, tool enumeration,
tool execution, and error code conformity.
"""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

MCP_SERVER_PATH = Path(__file__).parent.parent / "identity_router" / "mcp_server.py"

def run_compliance_suite() -> bool:
    print("Testing MCP Stdio Server (identity_router/mcp_server.py)...")
    proc = subprocess.Popen(
        [sys.executable, str(MCP_SERVER_PATH)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    test_vectors = [
        # 1. Initialize
        {
            "desc": "initialize request",
            "req": {"jsonrpc": "2.0", "id": "init-1", "method": "initialize", "params": {}},
            "validator": lambda res: res.get("result", {}).get("protocolVersion") == "2024-11-05" and res.get("id") == "init-1"
        },
        # 2. Ping
        {
            "desc": "ping request",
            "req": {"jsonrpc": "2.0", "id": "ping-1", "method": "ping", "params": {}},
            "validator": lambda res: res.get("result") == {} and res.get("id") == "ping-1"
        },
        # 3. Tools List
        {
            "desc": "tools/list enumeration",
            "req": {"jsonrpc": "2.0", "id": "tools-1", "method": "tools/list", "params": {}},
            "validator": lambda res: len(res.get("result", {}).get("tools", [])) >= 4
        },
        # 4. Tools Call - standing_files
        {
            "desc": "tools/call (standing_files)",
            "req": {"jsonrpc": "2.0", "id": "call-1", "method": "tools/call", "params": {"name": "standing_files", "arguments": {}}},
            "validator": lambda res: "SOUL.md" in res.get("result", {}).get("content", [{}])[0].get("text", "")
        },
        # 5. Tools Call - route_lesson
        {
            "desc": "tools/call (route_lesson)",
            "req": {"jsonrpc": "2.0", "id": "call-2", "method": "tools/call", "params": {"name": "route_lesson", "arguments": {"lesson": "Chris lives in Colorado"}}},
            "validator": lambda res: "USER.md" in res.get("result", {}).get("content", [{}])[0].get("text", "")
        },
        # 6. Tools Call - current_identity
        {
            "desc": "tools/call (current_identity)",
            "req": {"jsonrpc": "2.0", "id": "call-3", "method": "tools/call", "params": {"name": "current_identity", "arguments": {}}},
            "validator": lambda res: "Hatch" in res.get("result", {}).get("content", [{}])[0].get("text", "")
        },
        # 7. Method Not Found (-32601)
        {
            "desc": "unknown method error code (-32601)",
            "req": {"jsonrpc": "2.0", "id": "err-1", "method": "unknown/method", "params": {}},
            "validator": lambda res: res.get("error", {}).get("code") == -32601
        }
    ]

    payload = "".join(json.dumps(t["req"]) + "\n" for t in test_vectors)
    stdout, stderr = proc.communicate(input=payload, timeout=5)

    if proc.returncode != 0:
        print(f"  [FAIL] Server exited with non-zero code {proc.returncode}")
        if stderr:
            print(f"  STDERR: {stderr}")
        return False

    responses = [json.loads(line) for line in stdout.strip().splitlines() if line.strip()]
    if len(responses) != len(test_vectors):
        print(f"  [FAIL] Expected {len(test_vectors)} responses, received {len(responses)}")
        return False

    all_passed = True
    for vector, resp in zip(test_vectors, responses):
        passed = vector["validator"](resp)
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {vector['desc']}")
        if not passed:
            all_passed = False
            print(f"         Response: {resp}")

    if all_passed:
        print("\nALL MCP PROTOCOL COMPLIANCE CHECKS PASSED (100%).")
    return all_passed

if __name__ == "__main__":
    ok = run_compliance_suite()
    sys.exit(0 if ok else 1)
