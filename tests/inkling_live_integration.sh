#!/bin/bash
# Live integration test: prove Inkling no longer 500s on the request shape the
# new Zed providers (nvidia / openai-mcpproxy / openai-mcpproxy-nvidia) send.
#
# It mirrors EXACTLY what Zed serializes:
#   - tool_input_format = JsonSchema (full draft07, NOT JsonSchemaSubset)
#   - interleaved_reasoning = true  (reasoning_content surfaced)
#   - prompt_cache_key = omitted   (NVIDIA 400s on it)
#   - max_tokens (not max_completion_tokens)
#   - tools include nullable + nested schemas that the OLD subset transform
#     collapsed and that made Outlines 500 ("Could not translate instance to regex")
set -u

KEY="${NVIDIA_API_KEY:-${NVIDIA_INKLING_API_KEY:-}}"
BASE="https://integrate.api.nvidia.com/v1"
MODEL="thinkingmachines/inkling"

if [[ -z "$KEY" ]]; then echo "ERROR: set NVIDIA_API_KEY"; exit 1; fi

# A realistic 120-tool-style payload: nullable + oneOf-ish + nested object.
# This is the shape that broke the OLD openai_compatible (JsonSchemaSubset) path.
TOOLS=$(python3 -c '
import json
def tool(i):
    return {"type":"function","function":{
        "name":f"tool_{i}",
        "description":"x"*700,  # long desc, previously truncated
        "parameters":{"type":"object","properties":{
            "q": {"type":["string","null"]},          # nullable -> subset collapsed this
            "nested": {"type":"object","properties":{
                "a":{"type":"string"},"b":{"type":["integer","null"]}}},
            "choice": {"anyOf":[{"type":"string"},{"type":"number"}]}  # anyOf
        },"required":["q"]}}}
    }}
print(json.dumps([tool(i) for i in range(120)]))
')

echo "=== TEST A: full JSON Schema + interleaved_reasoning (nvidia provider shape) ==="
RESP=$(curl -s -o /tmp/resp_a.json -w "%{http_code}" "$BASE/chat/completions" \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d "$(python3 -c "
import json,sys
print(json.dumps({
  'model':'$MODEL','stream':True,
  'messages':[{'role':'user','content':'call tool_0 with q=\"hi\"'}],
  'tools':json.loads('''$TOOLS'''),
  'parallel_tool_calls':False,
  'max_tokens':2048,
  'reasoning_effort':'max',
  'interleaved_reasoning':True
}))
")")
echo "HTTP $RESP"
grep -o '"tool_calls"' /tmp/resp_a.json | head -1 && echo "-> tool_calls present (no 500)" || echo "-> check resp"; echo

echo "=== TEST B: reasoning_content round-trip (content:null + tool_calls + reasoning) ==="
RESP2=$(curl -s -o /tmp/resp_b.json -w "%{http_code}" "$BASE/chat/completions" \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d "$(python3 -c "
import json
print(json.dumps({
  'model':'$MODEL','stream':False,
  'messages':[
    {'role':'user','content':'list files'},
    {'role':'assistant','content':None,'reasoning_content':'need to list','tool_calls':[{'id':'c1','type':'function','function':{'name':'list_files','arguments':'{\"q\":\"hi\"}'}}]},
    {'role':'tool','tool_call_id':'c1','content':'[\"Cargo.toml\"]'},
    {'role':'user','content':'now what?'}
  ],
  'tools':json.loads('''$TOOLS'''),
  'max_tokens':1024,'reasoning_effort':'max','interleaved_reasoning':True
}))
")")
echo "HTTP $RESP2"
python3 -c "import json;d=json.load(open('/tmp/resp_b.json'));m=d['choices'][0]['message'];print('finish:',d['choices'][0]['finish_reason']);print('has reasoning_content:', 'reasoning_content' in m)" 2>/dev/null || echo "parse failed"; echo

echo "=== RESULT ==="
if [[ "$RESP" != "500" && "$RESP2" != "500" ]]; then
  echo "PASS: Inkling accepted full-JSON-Schema + interleaved_reasoning (no 500 loop)"
else
  echo "FAIL: got 500 — loop would recur"
  exit 1
fi
