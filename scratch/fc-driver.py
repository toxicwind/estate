#!/usr/bin/env python3
"""Local driver: ship the README-fix script to awrawr-pc via the bridge, run it, commit, push."""
import base64, subprocess, sys

sys.path.insert(0, "/home/hatch/workspace/skills/awrawr-mcp/bin")
import importlib.util
spec = importlib.util.spec_from_file_location("bridge", "/home/hatch/workspace/skills/awrawr-mcp/bin/exec.py")
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)

def run(cmd, workdir="/home/toxic"):
    init = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                       "clientInfo": {"name": "awrawr-mcp-skill", "version": "1.0"}}}
    _, sid = bridge._post(init, None)
    bridge._post({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
    call = {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": "exec", "arguments": {"cmd": cmd, "workdir": workdir}}}
    result, _ = bridge._post(call, sid)
    if "error" in result:
        raise RuntimeError(f"RPC error: {result['error']}")
    res = result.get("result", {})
    out = "\n".join(b.get("text", "") for b in res.get("content", []) if isinstance(b, dict))
    if res.get("isError"):
        raise RuntimeError(f"remote command failed:\n{out}")
    return out

# 1. ship the apply script (base64 alphabet has no shell-special chars)
src = open("/home/hatch/workspace/readme-fix-fleet-chat-apply.py", "rb").read()
blob = base64.b64encode(src).decode()
print(run("python3 -c \"import base64;open('/home/toxic/fc-apply.py','w').write(base64.b64decode('"
          + blob + "').decode())\""))

# 2. run it
print(run("cd /home/toxic/readme-fix-fleetchat-47097 && python3 /home/toxic/fc-apply.py"))

# 3. verify + commit + push
print(run("cd /home/toxic/readme-fix-fleetchat-47097 && git diff --stat && python3 -c \"import ast; ast.parse(open('chat.py').read()); print('chat.py parses')\" && grep -c cryptography pyproject.toml"))

print(run("cd /home/toxic/readme-fix-fleetchat-47097 && git add -A && git -c user.name=shingle -c user.email=shingle@local commit -m 'docs: bruteforce-fix README against source (presence dirs, crypto prereq, donor paths, paper counts)' && git log --oneline -1"))

print(run("cd /home/toxic/readme-fix-fleetchat-47097 && git push origin HEAD:main && git log --oneline -1 origin/main 2>/dev/null || git rev-parse HEAD"))
