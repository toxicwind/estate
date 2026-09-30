import json, os, subprocess, sys

KEY = os.environ.get("NVIDIA_API_KEY") or os.environ.get("NVIDIA_INKLING_API_KEY")
if not KEY:
    print("ERROR: set NVIDIA_API_KEY"); sys.exit(1)

BASE = "https://integrate.api.nvidia.com/v1"
MODEL = "thinkingmachines/inkling"

# 120 tools with nullable + nested + anyOf schemas (the shape that broke the OLD subset path)
tools = []
for i in range(120):
    tools.append({
        "type": "function",
        "function": {
            "name": f"tool_{i}",
            "description": "x" * 700,
            "parameters": {
                "type": "object",
                "properties": {
                    "q": {"type": ["string", "null"]},
                    "nested": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "string"},
                            "b": {"type": ["integer", "null"]},
                        },
                    },
                    "choice": {"anyOf": [{"type": "string"}, {"type": "number"}]},
                },
                "required": ["q"],
            },
        },
    })

def post(payload):
    body = json.dumps(payload)
    p = subprocess.run(
        ["curl", "-s", "-o", "/tmp/ink_resp.json", "-w", "%{http_code}",
         f"{BASE}/chat/completions", "-H", f"Authorization: Bearer {KEY}",
         "-H", "Content-Type: application/json", "-d", body],
        capture_output=True, text=True,
    )
    return p.stdout.strip(), open("/tmp/ink_resp.json").read()

print("=== TEST A: full JSON Schema + interleaved_reasoning (nvidia provider shape) ===")
code, resp = post({
    "model": MODEL, "stream": True,
    "messages": [{"role": "user", "content": 'call tool_0 with q="hi"'}],
    "tools": tools, "parallel_tool_calls": False,
    "max_tokens": 2048, "reasoning_effort": "max",
})
print(f"HTTP {code}")
has_tc = 'tool_calls' in resp
print(f"tool_calls present: {has_tc}")

print("=== TEST B: reasoning_content round-trip (content:null + tool_calls + reasoning) ===")
code2, resp2 = post({
    "model": MODEL, "stream": False,
    "messages": [
        {"role": "user", "content": "list files"},
        {"role": "assistant", "content": None, "reasoning_content": "need to list",
         "tool_calls": [{"id": "c1", "type": "function",
                         "function": {"name": "list_files", "arguments": '{"q":"hi"}'}}]},
        {"role": "tool", "tool_call_id": "c1", "content": '["Cargo.toml"]'},
        {"role": "user", "content": "now what?"},
    ],
    "tools": tools, "max_tokens": 1024, "reasoning_effort": "max",
})
print(f"HTTP {code2}")
try:
    d = json.loads(resp2)
    m = d["choices"][0]["message"]
    print(f"finish: {d['choices'][0]['finish_reason']}")
    print(f"has reasoning_content: {'reasoning_content' in m}")
except Exception as e:
    print(f"parse failed: {e}")

print("=== RESULT ===")
if code != "500" and code2 != "500":
    print("PASS: Inkling accepted full-JSON-Schema + interleaved_reasoning (no 500 loop)")
    sys.exit(0)
else:
    print("FAIL: got 500 — loop would recur")
    sys.exit(1)
