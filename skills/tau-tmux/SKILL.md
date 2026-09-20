# tau-tmux Skill: Audit NVIDIA Unlock Configuration

## Purpose

Audit the maximal NVIDIA unlock configuration for the Tau agent. Verifies all patches are correctly applied and reports status.

## When to Use

- After applying NVIDIA config patches to confirm they took effect
- Before running Tau with NVIDIA model to ensure correct setup
- As part of routine Sovereign ecosystem health check

## How to Use via TMUX

```bash
# 1. Ensure tmux session is running tau
tmux new-session -d -s tau "bash"

# 2. Run the audit skill
tau --profile audit

# 3. Or send directly via tmux
tmux send-keys -t tau "tau --profile audit" C-m
```

## Verification Checks

The skill checks the following and reports PASS/FAIL:

### 1. nvidia.json

- `contextWindow == 1048576` (1M context)
- `maxTokens == 32768` (32k output)
- `cost all zeros` (free tier)
- `reasoningEffortMap present` with map: minimal→low, low→low, medium→medium, high→high, xhigh→max, max→max
- `thinkingFormat == "openai"`
- `supportsReasoningEffort == 1`

### 2. nvidia.ts

- `const DEFAULT_MODEL = "nvidia/nemotron-3-ultra-550b-a55b"` exists
- `defaultModel: DEFAULT_MODEL` present in nvidiaProvider object

### 3. cascade.json

- `models == 9` (9 models total)
- `effective_rpm == 360` (free tier limit)
- `tier3_heavy contains nvidia/nemotron-3-ultra-550b-a55b`
- `fallback == "meta/llama-3.1-70b-instruct"`

### 4. .env

- `PI_NVIDIA_DEFAULT_MODEL == "nvidia/nemotron-3-ultra-550b-a55b"`
- `PI_NVIDIA_CONTEXT_WINDOW == 1048576`
- `PI_NVIDIA_MAX_TOKENS == 32768`
- `PI_CASCADE_MODELS == 9`
- `PI_CASCADE_RPM == 360`
- `PI_OPENROUTER_SESSION == "exploit-forever"`
- `PI_GROQ_HEALING_PATTERN == "thinking"`
- `PI_SANDBOX_ALLOW_UNSAFE == true`
- `PI_SANDBOX_DANGEROUSLY_DISABLE == true`
- No duplicate lines

## Exit Codes

- `0` - All checks PASS
- `1` - Any check FAIL (report which ones)

## Example

```bash
# Run audit in tmux
tmux new-session -d -s tau "bash"
tau --profile audit

# Expected output (all PASS):
[nvidia.json] contextWindow: PASS (1048576)
[nvidia.json] maxTokens: PASS (32768)
[nvidia.json] cost: PASS (all zeros)
[nvidia.json] reasoning: PASS (enabled, thinkingFormat: openai)
[nvidia.ts] DEFAULT_MODEL: PASS
[nvidia.ts] defaultModel: PASS
[cascade.json] models: PASS (9)
[cascade.json] RPM: PASS (360)
[cascade.json] tier3: PASS (nvidia/nemotron-3-ultra-550b-a55b)
.env] all vars: PASS (deduplicated, correct values)

# Exit code 0 means all good!
```
