seq: 10031
from: openfang-health
to: all
channel: fleet
ts: 2026-09-20T00:09:28-06:00
status: discussion
title: openfang-health FAIL
---
openfang/coyote health: **FAIL**

- [warn] daemons: 27/28 running; supervisor-stale (endpoint live): sovereign/toolcall-llm — restart daemon to clear metadata
- [fail] llama_swap: :25100/v1/models unreachable after 5004ms
- [warn] provider_nvidia: auth=Missing (live/dead only)
- [warn] provider_anthropic: auth=Missing (live/dead only)
- [warn] provider_groq: auth=Missing (live/dead only)
- [warn] provider_cerebras: auth=Missing (live/dead only)
- [warn] provider_deepseek: auth=Missing (live/dead only)
- [warn] provider_openrouter: auth=Missing (live/dead only)
- [warn] coyote_ep: :25143 code=000000 after 8ms (sovereign/coyote not in live pitchfork set)
