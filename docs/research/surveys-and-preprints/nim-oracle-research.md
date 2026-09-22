# NVIDIA NIM Model Research for Super-Ralph Oracle
Date: 2026-09-19
Purpose: Benchmark-backed model selection for the oracle that will replace human oracle (lane-3) in super-ralph

## Sources
- NIMStats (MauroDruwel): 22 models, hourly benchmarks — https://github.com/MauroDruwel/NIMStats
- ai-coding-stack-omniroute (stocknewsbr): 8 verified free models, lab smoke tests 3/3 — https://github.com/stocknewsbr/ai-coding-stack-omniroute-nvidia-opencode/blob/HEAD/docs/14-verified-free-models.md
- nvidia_nim_model (dhruvkachhela): coding/math/writing/tool-calling benchmarks — https://github.com/dhruvkachhela/nvidia_nim_model
- nim-skill-test (polats): 27-model skill-following benchmark — https://github.com/polats/nim-skill-test

## Oracle requirements
1. Structured JSON output (rubric-scored bids)
2. Strong reasoning (debate judging, evidence evaluation)
3. Tool use (research grounding verification)
4. Low latency (oracle must be responsive)
5. Long context (debate ledgers, bid bodies)

## Top candidates

### 1. GLM-5.2 (`nvidia/z-ai/glm-5.2`)
- 753B params, 1M context, tool use, free endpoint
- Ranked #1 in ai-coding-stack for: coding, architecture, long audits, agentic work
- Lab smoke test: 3/3
- Best all-rounder for oracle workload

### 2. Nemotron 3 Ultra 550B (`nvidia/nvidia/nemotron-3-ultra-550b-a55b`)
- 550B total / 55B active, 1M context
- Deep reasoning, long-context audit
- Lab smoke test: 3/3
- Best for complex debate judging

### 3. Mistral Small 4 119B (`mistralai/mistral-small-4-119b-2603`)
- Coding benchmark: task fit 1.00, latency 1.37s (ranked #1)
- Fastest high-quality option
- Good for latency-sensitive oracle calls

### 4. Nemotron 3 Super 120B (`nvidia/nvidia/nemotron-3-super-120b-a12b`)
- 120B total / 12B active, 1M context
- Agent/worker pool, high-volume tasks
- Good balance of capability and speed

## Recommendation
**Primary: GLM-5.2** — best fit for oracle (reasoning + structured output + tool use + 1M context + free tier)
**Fallback: Nemotron 3 Super 120B** — faster, still capable, for high-volume bid scoring
**Deep reasoning: Nemotron 3 Ultra 550B** — for complex multi-slice debates requiring careful judgment

## Next steps
1. Inspect super-ralph integration (model/provider path, request schema, oracle intake)
2. Test structured JSON output on each candidate
3. Benchmark latency on oracle-style prompts (bid scoring)
4. Build the durable oracle path with the winner
