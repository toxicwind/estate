# Pika's Model Assignment Map — 2026-09-30
## Ending same-model-everywhere with benchmark evidence

### Sweep method
- 108 live probes through herd :25100 (hyper-raced, 6 workers, 45s ceilings)
- 4 task types: chat / code / reasoning / triage, scored 2/1/0 + latency
- 22 models across openrouter-free, gemini, mistral, pollinations-free

### Key findings
- **gemini/gemini-3-flash-preview**: ONLY model reliable across all 4 tasks (2/1/2/2). The reliability anchor.
- **openrouter-free/nvidia/nemotron-3-super-120b-a12b:free**: best free all-rounder when alive (2/2/2/2 first pass) but FLAKY (502s on retry).
- Free tier is inherently flaky: 36x 404, 14x 502, 12x empty across the sweep.
- pollinations-free: 401 (dead keys — flagged, not touched). mistral: 404/400 (dead routes).

### Strategy: specialist primary + gemini fallback chain
Each agent gets its task-best model as primary; gemini-3-flash-preview as fallback.
If primary 502s/404s, the chain fails over automatically. Diversity with a safety net.

| Agent | Lane | Primary (evidence) | Fallback |
|---|---|---|---|
| coyote | reasoning/orchestration | nemotron-3-nano-omni-30b (reasoning=2) | gemini-3-flash-preview |
| assistant | chat | lfm-2.5-2.6b (chat=2) | gemini-3-flash-preview |
| squawk-relay | triage | laguna-s-2.1 (triage=2, 542ms) | gemini-3-flash-preview |
| kimiclaw-1 | code worker | gemma-4-26b-a4b-it (code=2) | gemini-3-flash-preview |
| kimiclaw-2 | code worker | north-mini-code (code specialist) | gemini-3-flash-preview |
| oracle-market | reasoning/judge | nemotron-3-nano-omni-30b (reasoning=2) | gemini-3-flash-preview |
| weaver | reasoning/triage | nemotron-3-super-120b (2/2/2/2) | gemini-3-flash-preview |
| dediops | triage/ops | dots-3-note-preview (triage=2) | gemini-3-flash-preview |
| trailboss | code/patches | gemma-4-26b-a4b-it (code=2) | gemini-3-flash-preview |
