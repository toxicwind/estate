in#!/bin/bash

KEY=${NVIDIA_API_KEY}
BASE="https://integrate.api.nvidia.com/v1"
BIG=$(python3 -c "print('system instruction ' * 300)")

echo "=== GET /v1/models ==="
curl -s $BASE/models -H "Authorization: Bearer $KEY" | zq '.data[] |.id' | grep inkling

echo "=== GET /v1/models/inkling ==="
curl -s $BASE/models/thinkingmachines/inkling -H "Authorization: Bearer $KEY" | zq

echo "=== POST /v1/chat/completions stream:false no tools ==="
curl -s $BASE/chat/completions -H "Content-Type: application/json" -H "Authorization: Bearer $KEY" -d '{"model":"thinkingmachines/inkling","messages":[{"role":"user","content":"hi"}],"max_tokens":20,"stream":false}' | zq .choices[0].finish_reason

echo "=== POST /v1/chat/completions stream:true no tools ==="
curl -s $BASE/chat/completions -H "Content-Type: application/json" -H "Authorization: Bearer $KEY" -d '{"model":"thinkingmachines/inkling","messages":[{"role":"user","content":"hi"}],"max_tokens":20,"stream":true}' | tail -1

echo "=== POST stream:false parallel:true 2 tools (you proved works) ==="
curl -s $BASE/chat/completions -H "Content-Type: application/json" -H "Authorization: Bearer $KEY" -d '{"model":"thinkingmachines/inkling","messages":[{"role":"user","content":"You MUST call list_files for \".\" AND read_file for \"README.md\" in parallel now."}],"stream":false,"parallel_tool_calls":true,"tools":[{"type":"function","function":{"name":"list_files","description":"list","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":[]}}},{"type":"function","function":{"name":"read_file","description":"read","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}}],"tool_choice":"auto"}' | zq '.choices[0].message.tool_calls | length'

echo "=== POST stream:true parallel:true 2 tools - THIS IS WHAT ZED ACTUALLY DOES ==="
curl -s $BASE/chat/completions -H "Content-Type: application/json" -H "Authorization: Bearer $KEY" -d '{"model":"thinkingmachines/inkling","messages":[{"role":"user","content":"You MUST call list_files for \".\" AND read_file for \"README.md\" in parallel now."}],"stream":true,"parallel_tool_calls":true,"tools":[{"type":"function","function":{"name":"list_files","description":"list","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":[]}}},{"type":"function","function":{"name":"read_file","description":"read","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}}],"tool_choice":"auto"}' | grep tool_calls

echo "=== POST stream:false turn 2 with reasoning_content + tool result - THIS IS CONTINUATION ==="
curl -s $BASE/chat/completions -H "Content-Type: application/json" -H "Authorization: Bearer $KEY" -d '{
  "model":"thinkingmachines/inkling",
  "messages":[
    {"role":"user","content":"list files"},
    {"role":"assistant","content":null,"tool_calls":[{"id":"call_123","type":"function","function":{"name":"list_files","arguments":"{\"path\":\".\"}"}}],"reasoning_content":"need to list"},
    {"role":"tool","tool_call_id":"call_123","content":"[\"Cargo.toml\",\"README.md\"]"},
    {"role":"user","content":"now what?"}
  ],
  "stream":false,
  "parallel_tool_calls":true
}' | zq .

echo "=== POST prompt_cache_key test ==="
curl -s $BASE/chat/completions -H "Content-Type: application/json" -H "Authorization: Bearer $KEY" -d "{\"model\":\"thinkingmachines/inkling\",\"messages\":[{\"role\":\"system\",\"content\":\"$BIG\"},{\"role\":\"user\",\"content\":\"hi\"}],\"prompt_cache_key\":\"test123\",\"max_tokens\":10,\"stream\":false}" | zq .usage

echo "=== POST /v1/responses ==="
curl -s -o /dev/null -w "%{http_code}\n" $BASE/responses -H "Content-Type: application/json" -H "Authorization: Bearer $KEY" -d '{"model":"thinkingmachines/inkling","input":"hi"}'

echo "=== POST /v1/messages ==="
curl -s -o /dev/null -w "%{http_code}\n" $BASE/messages -H "Content-Type: application/json" -H "Authorization: Bearer $KEY" -d '{"model":"thinkingmachines/inkling","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'
