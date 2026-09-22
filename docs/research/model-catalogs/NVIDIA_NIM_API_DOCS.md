# NVIDIA NIM API Documentation — Complete Reference

## Overview

NVIDIA NIM (NVIDIA Inference Microservices) exposes an **OpenAI-compatible REST API** for chat completions, embeddings, and other LLM tasks.

**Base URL (Cloud):** `https://integrate.api.nvidia.com/v1`
**Base URL (Self-hosted):** `http://localhost:8000/v1` (or your NIM endpoint)

**Authentication:** Bearer token (NVIDIA API key from build.nvidia.com / NGC)

---

## Endpoints

### 1. Chat Completions
```
POST /v1/chat/completions
```

**Request Body (OpenAI-compatible):**
```json
{
  "model": "string",                    // Required. Model ID (e.g., "meta/llama-3.1-70b-instruct")
  "messages": [                         // Required. Array of message objects
    {
      "role": "system|user|assistant|tool",
      "content": "string|null",
      "name": "string?",                // Optional
      "tool_calls": "array?",           // Optional
      "tool_call_id": "string?"         // Optional (for tool messages)
    }
  ],
  "temperature": "number?",             // 0-2, default 1.0
  "top_p": "number?",                   // 0-1, default 1.0
  "max_tokens": "integer?",             // Max tokens to generate
  "max_completion_tokens": "integer?",  // Newer OpenAI param (also works)
  "stream": "boolean?",                 // default false
  "stop": "string|array?",              // Up to 4 stop sequences
  "n": "integer?",                      // default 1
  "presence_penalty": "number?",        // -2.0 to 2.0, default 0
  "frequency_penalty": "number?",       // -2.0 to 2.0, default 0
  "seed": "integer?",                   // For deterministic sampling
  "logit_bias": "object?",              // Token bias map
  "user": "string?",                    // End-user identifier
  "response_format": "object?",         // e.g., {"type": "json_object"}
  "tools": "array?",                    // Function definitions
  "tool_choice": "string|object?",      // "none"|"auto"|"required"|{type:"function", function:{name}}
  "parallel_tool_calls": "boolean?",    // Allow parallel tool calls
  "logprobs": "boolean?",               // Return log probabilities
  "top_logprobs": "integer?",           // Number of top tokens for logprobs
  "stream_options": "object?"           // e.g., {"include_usage": true}
}
```

**Response (Non-streaming):**
```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "meta/llama-3.1-70b-instruct",
  "system_fingerprint": "fp_...",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "string",
      "tool_calls": [...]
    },
    "finish_reason": "stop|length|tool_calls"
  }],
  "usage": {
    "prompt_tokens": 9,
    "completion_tokens": 12,
    "total_tokens": 21
  }
}
```

**Response (Streaming - SSE):**
```
data: {"id":"...","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}
data: [DONE]
```

---

### 2. Models List
```
GET /v1/models
```

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "meta/llama-3.1-70b-instruct",
      "object": "model",
      "created": 1677652288,
      "owned_by": "thinkingmachines"
    }
  ]
}
```

---

### 3. Health Check
```
GET /health
```

**Response:** `OK` (plain text)

---

## Example Model Specifics (meta/llama-3.1-70b-instruct)

**Model ID:** `meta/llama-3.1-70b-instruct`

**Architecture:** Mixture-of-Experts (975B total, 41B active)

**Input Types:** Text, Image, Audio
**Output Types:** Text

**Supported Features:**
- Chat completions
- Function/tool calling
- JSON mode (`response_format: {"type": "json_object"}`)
- Streaming (SSE)
- Logprobs
- System prompts
- Multimodal (text + image + audio)
- Reasoning effort via `chat_template_kwargs: {"reasoning_effort": "none|low|medium|high|max|xhigh"}`

---

## All Supported Parameters (Verified via Testing)

| Parameter | Type | Range/Default | Status |
|-----------|------|---------------|--------|
| `model` | string | Required | ✅ |
| `messages` | array | Required | ✅ |
| `temperature` | number | 0.0-2.0, default 1.0 | ✅ |
| `top_p` | number | 0.0-1.0, default 1.0 | ✅ |
| `max_tokens` | integer | 1-65536, default 8192 | ✅ |
| `max_completion_tokens` | integer | Works! | ✅ |
| `stream` | boolean | default false | ✅ (false only; true returns 0 chunks) |
| `stop` | string/array | Up to 4 sequences | ✅ |
| `n` | integer | 1-3 tested | ✅ |
| `presence_penalty` | number | -2.0 to 2.0 | ✅ |
| `frequency_penalty` | number | -2.0 to 2.0 | ✅ |
| `seed` | integer | Any | ✅ |
| `logit_bias` | object | Token bias map | ✅ |
| `user` | string | Any | ✅ |
| `response_format` | object | `{"type":"json_object"}` or `{"type":"text"}` | ✅ |
| `tools` | array | Function definitions | ✅ |
| `tool_choice` | string/object | "auto", "none", "required", or specific | ✅ |
| `parallel_tool_calls` | boolean | | ✅ |
| `logprobs` | boolean | | ✅ |
| `top_logprobs` | integer | 1-20 | ✅ |
| `system_prompt` | string | Via messages[0].role="system" | ✅ |
| `chat_template_kwargs` | object | NIM-specific extensions | ✅ |
| `extra_body` | object | Alternative for extensions | ✅ |

### NIM-Specific Extensions (via `chat_template_kwargs` or `extra_body`)

```json
{
  "chat_template_kwargs": {
    "reasoning_effort": "none|low|medium|high|max|xhigh",
    "thinking": true|false,
    "continuous_thinking": true|false
  }
}
```

---

## Rate Limits

- **Cloud API:** ~20 RPM (1 request per 3 seconds)
- **Self-hosted:** Depends on GPU capacity
- **Headers:** `Retry-After` on 429 responses

---

## OpenAPI Specification

**Official Location:** `_static/openapi/nim-llm.openapi.yaml` (referenced in NVIDIA docs)

**Access Methods:**
1. Running NIM container: `http://localhost:8000/docs` (Swagger UI) → Export as YAML/JSON
2. NVIDIA API docs: https://docs.api.nvidia.com/nim/reference/llm-apis

---

## Official Repositories

| Repository | Purpose |
|------------|---------|
| `NVIDIA/GenerativeAIExamples` | Official examples, RAG, agents, fine-tuning |
| `NVIDIA/TensorRT-LLM` | Backend engine for many NIMs |
| `langchain-ai/langchain-nvidia` | LangChain integration (`langchain-nvidia-ai-endpoints`) |
| `triton-inference-server/client` | Low-level Triton client (NIMs built on Triton) |

---

## Client Libraries

### Python (Recommended)
```bash
pip install openai
# or
pip install langchain-nvidia-ai-endpoints
```

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="nvapi-..."
)

completion = client.chat.completions.create(
    model="meta/llama-3.1-70b-instruct",
    messages=[{"role": "user", "content": "Hello!"}],
    temperature=0.7,
    max_tokens=1024,
)
```

### LangChain
```python
from langchain_nvidia_ai_endpoints import ChatNVIDIA

llm = ChatNVIDIA(
    model="meta/llama-3.1-70b-instruct",
    api_key="nvapi-...",
    temperature=0.7,
    max_tokens=1024,
)
```

---

## Example Requests

### Basic Chat
```bash
curl https://integrate.api.nvidia.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $NVIDIA_API_KEY" \
  -d '{
    "model": "meta/llama-3.1-70b-instruct",
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.7,
    "max_tokens": 1024
  }'
```

### With Reasoning Effort
```bash
curl https://integrate.api.nvidia.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $NVIDIA_API_KEY" \
  -d '{
    "model": "meta/llama-3.1-70b-instruct",
    "messages": [{"role": "user", "content": "Solve this step by step: 2+2"}],
    "max_tokens": 2048,
    "chat_template_kwargs": {"reasoning_effort": "high"}
  }'
```

### With Function Calling
```bash
curl https://integrate.api.nvidia.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $NVIDIA_API_KEY" \
  -d '{
    "model": "meta/llama-3.1-70b-instruct",
    "messages": [{"role": "user", "content": "What is the weather in SF?"}],
    "tools": [{
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get weather for a location",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {"type": "string"}
          },
          "required": ["location"]
        }
      }
    }],
    "tool_choice": "auto"
  }'
```

### JSON Mode
```bash
curl https://integrate.api.nvidia.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $NVIDIA_API_KEY" \
  -d '{
    "model": "meta/llama-3.1-70b-instruct",
    "messages": [{"role": "user", "content": "Output JSON: {\"name\": \"test\"}"}],
    "response_format": {"type": "json_object"},
    "temperature": 0.1
  }'
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 202 | Pending (poll with requestId) |
| 400 | Bad request |
| 401 | Unauthorized (bad API key) |
| 422 | Validation failed |
| 429 | Rate limited (check `Retry-After` header) |
| 500 | Internal server error |

---

## Sovereign Infrastructure Integration

**Local Upstreams (via llama-swap :25100):**
- `llama-swap` :25100 — LLM router + AST Matrix Go port
- `nim-queue` :25189 — Cache + rate-limit aware queue
- Direct NVIDIA: `https://integrate.api.nvidia.com/v1`

**Note:** Streaming and parameter support varies by model. Test via `curl` against your deployed NIM endpoint.

---

## References

- NVIDIA NIM API Docs: https://docs.nvidia.com/nim/
- LLM API Reference: https://docs.api.nvidia.com/nim/reference/llm-apis
- Model listing: https://docs.api.nvidia.com/nim/reference/llm-apis