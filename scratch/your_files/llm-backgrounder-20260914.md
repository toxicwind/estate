# LLM Landscape Backgrounder — September 14, 2026

Researched 2026-09-14 via arXiv (arxiv-mcp skill), multi-source paper router
(emergent-enrich: arXiv + OpenAlex + HF Papers + alphaXiv), and live web search.
**Recency convention:** items marked **[Sep 2026]** / **[Aug 2026]** are
current-month; **[Summer 2026]** = last 60 days; **[Background]** = pre-summer,
still structurally true but verify before acting. No Exa credits spent.

---

## 1. Frontier labs + flagship models

The last two weeks were the busiest release window of the year. Three
frontier vendors shipped in the same week (week of Aug 31), and on
**Sep 3 all of ChatGPT, Claude, and Grok went down within hours of each
other** — the industry's multi-vendor "resilience" story failed its first
real test the same week it was most needed.

**[Sep 2026]**
- **GPT-6 Astra** (OpenAI, Sep 3) — "generational leap" framing, saturates
  frontier benchmarks, first model ever rated **Critical for cybersecurity**.
  Built for operating software with minimal supervision.
  ([memeburn timeline](https://memeburn.com/every-major-ai-model-that-shipped-in-six-weeks-from-kimi-k3-to-gpt-6-astra/))
- **Claude Fable 5.1 + Mythos 5.1** (Anthropic, Sep 1) — outperforms Opus 5;
  **cache pricing cut 75%** (matters enormously for agent workloads with
  repeated context). Claude Opus 5 (Jul 24) sits at $5/$25 per 1M.
  ([softwarereviews](https://www.softwarereviews.com/vendor-technology-notes/big-5-ai-vendor-roundup-week-of-august-31-2026))
- **Gemini 3.8 Flash + Flash Cyber** (Google, Sep 2) — third Flash in six
  weeks; **Gemini 4 Pro still unreleased**, and the Gemini community is
  openly anxious it never ships. Google is ceding the "frontier" narrative
  to OpenAI/Anthropic while winning on value.
  ([techradar](https://www.techradar.com/ai-platforms-assistants/i-also-want-to-feel-the-frontier-gemini-users-are-starting-to-think-that-gemini-pro-4-wont-ever-see-the-light-of-day-thanks-to-the-release-of-chatgpt-6-astra-and-claude-fable-5-1))
- **ValueRank v1.5.0** (Sep 6, independent, 21 models × DeepSWE agent score +
  cost): #1 **Gemini 3.8 Flash** on value; GPT-6 Astra top raw quality
  (75.3); **GLM-5.3 Flash** the cost king; Kimi K3 ranks #8 overall.
  Pareto frontier: GPT-6 Astra, Gemini 3.8 Flash, GPT-5.6 Sol,
  Gemini 3.7 Flash, GLM-5.3 Flash.
  ([github.com/alo-labs/valuerank](https://github.com/alo-labs/valuerank))

**[Aug 2026]**
- **Grok 4.6** (xAI, Aug 12) — 500K context, $2/$6, reasoning-effort toggle.
- **Qwen3.8-Max-0902** (Alibaba, Sep 2) — tops Code Arena WebDev over
  Claude Opus 5.

**[Background — structural, still true]**
- Model generations now turn over in **weeks, not quarters**. The Kimi K3
  paper (arXiv:2607.24653) names the then-frontier as "Claude Fable 5 and
  GPT-5.6 Sol" — both already superseded by Sep 2026 (.1/Astra). Any
  hard-coded model list older than ~60 days is stale.
- Geopolitics is now a model-selection input: the US government withdrew
  Anthropic's Fable/Mythos for ~a month on security concerns, and the White
  House publicly accused Moonshot of distilling Fable to build Kimi K3
  (Moonshot denies; Treasury threatened sanctions; China mulling export
  controls on weight downloads). **The open-weight window may not stay open.**

---

## 2. Open-weight landscape — what's actually good and runnable

Summer 2026 belonged to Chinese labs: **four frontier-class open models in
30 days** (Jul 27–Aug 25), with a deliberate licensing split — MIT-licensed
Flash models for adoption, custom "Max" licenses for enterprise capture.

| Model | Release | Size | License | Notes |
|---|---|---|---|---|
| **Kimi K3** (Moonshot) | [Jul 2026] | 2.8T / 104B act | Moonshot custom | Largest open weights ever; 1M ctx; frontier coding/agentic; arXiv:2607.24653 |
| **DeepSeek V4 Pro** | [Aug 2026] GA | 1.6T / 49B act | **MIT** | Tops open SWE-bench Verified; 1M ctx; datacenter-only in practice |
| **DeepSeek V4-Flash** | [Jul 2026] | 304B | **MIT** | The runnable DeepSeek |
| **Qwen3.8-Max** | [Aug 2026] | 2.4T / 95B act | Alibaba Max | -0902 tops Code Arena WebDev |
| **Qwen3-Coder 480B-A35B** | [Summer 2026] | 480B / 35B act | **Apache-2.0** | Best coder you can fully own commercially |
| **Qwen3-Coder 30B-A3B** | [Summer 2026] | 30B / 3B act | Apache-2.0 | **Best coder fitting one 24GB GPU** |
| **GLM-5.3-Flash** (Zhipu) | [Aug 2026] | 320B / 18B act | **MIT** | $0.15/$0.50 API; coding-agent favorite |
| **Devstral 2** (Mistral) | [Summer 2026] | — | Apache-2.0 family | Purpose-built to *be* a coding agent |
| Llama 4 (Meta) | [Background] | — | Custom | Broad tooling, but **excludes EU developers from multimodal grant** — license trap |

Architecture notes (Kimi K3 paper, arXiv:2607.24653): Kimi Delta Attention +
Attention Residuals, Stable LatentMoE (16 of 896 experts/token), ~2.5×
scaling efficiency over K2, RL across "multiple reasoning-effort levels."
The MoE + reasoning-effort-tiers pattern is now standard at the frontier.

**Self-host reality check (Sep 2026):** the 1T+ models (K3, V4 Pro,
Qwen3.8-Max) are API-or-datacenter-only for mortals. The runnable tier is
30B–320B: Qwen3-Coder 30B-A3B (single 3090-class GPU), GLM-5.3-Flash /
DeepSeek V4-Flash (multi-GPU workstation). Sources:
[wavect.io](https://wavect.io/blog/open-weight-llm-comparison-2026/) (reviewed
Sep 2),
[dreaming.press](https://dreaming.press/posts/open-source-llm-for-coding-september-2026.html)
(Sep 8),
[intelligibberish.com](https://intelligibberish.com/articles/how-to-choose-an-open-weight-model-family/)
(Sep 14).

---

## 3. Inference providers + pricing reality

**[Sep 2026] pricing (per 1M tokens, in/out):**
- Frontier API: Claude Opus 5 **$5/$25** · Grok 4.6 **$2/$6** · Gemini 3.7
  Flash **$0.75/$3.75** · GLM-5.3-Flash **$0.15/$0.50** · Claude Sonnet 4.5
  **$3/$15** (the coding-agent default, see §4)
- **DeepSeek official is the price floor: $0.435/$0.87**, with cached input
  at **$0.0036/M** (100×+ discount, automatic prefix caching, ~90% hit
  rates). Aggregators are *more* expensive: OpenRouter routed adds **45%**;
  Together/Fireworks ~**4×** official — you pay for US hosting, compliance,
  and better TTFT, not tokens.
  ([intelligentliving.co](https://www.intelligentliving.co/deepseek-price-increase-alternatives/),
  Sep 12)
- Open-weight serving: Fireworks $0.10–$1.74 in (LoRA deploy, fine-tune to
  1T params) · Together $0.10–$9 · DeepInfra from $0.02/$0.05 (8B turbo) ·
  Groq LPU $0.04–$0.79 in (lowest latency, 30 req/min free tier).
  ([digitalocean.com](https://www.digitalocean.com/resources/articles/llm-api-providers))
- **Prompt caching is the real pricing lever.** Fable 5.1's 75% cache-price
  cut + DeepSeek's near-free cached input mean agent workloads (repeated
  system prompts, repo context) cost 5–50× less than sticker price suggests.
  Price your router on *effective* cost with caching, not list price.

**NVIDIA NIM [Sep 2026]:**
- **NIM 2.0.12 → 2.5× throughput on Nemotron 3 Ultra** (4× B200, 718 →
  1,997 tok/s) via precision tuning, MoE tensor-parallel speculative
  decoding, targeting agentic workloads with long context reuse.
  ([blockchain.news](https://blockchain.news/news/nvidia-nim-nemotron-3-ultra-boost),
  Sep 10)
- **Rubin CPX** (announced, ships end of 2026): GPU designed specifically
  for massive-context inference — NVIDIA is betting the next bottleneck is
  1M-token serving cost.
- Note: one aggregator report claims "NIM deprecation March 18, 2026,
  migrate to Hugging Face" — this reads as garbled (NIM 2.0.12 shipped
  *September* 2026 and Rubin CPX bundles NIM microservices); treat as
  unverified noise.

---

## 4. Agent / coding models — Chris's world

**Tool landscape [Sep 2026]** — three settled categories
([aiweekly.co](https://aiweekly.co/learning-ai/generative-ai/best-ai-coding-tools-compared),
verified Sep 3):
1. **Terminal-first agents** (Claude Code) — deepest refactors, highest
   token burn, no IDE layer.
2. **Agentic IDEs** (Cursor $20/mo, 800K MAU; Kiro) — best daily-driver UX;
   Cursor's Background Agents + BugBot + Plan Mode lead the category.
3. **IDE plugins** (Copilot $10/mo — now on AI-credit billing) — cheapest,
   GitHub-native issue→PR flow.
- **Dead/walking-dead:** Amazon Q Developer closed signups May 2026,
  sunsets Apr 2027 · Google killed individual Gemini Code Assist Jun 2026.
- **Open-source lane:** **Cline** (VS Code ext, BYO key, Plan/Act modes) is
  the serious open agent harness; **OpenCode**, **Aider** round out the
  field. This is tau's competitive set.
- **The model that matters most for agents isn't the smartest — it's the
  most reliable tool-caller.** Creative-Tim's Sep 7 ranking names
  **Claude Sonnet 4.5 ($3/$15, 200K)** "the default coding agent brain":
  *"It just calls tools correctly… best tool-calling reliability per dollar."*
  Cost-per-*completed-task* beats cost-per-token.
  ([creative-tim.com](https://www.creative-tim.com/blog/ai-agent/the-best-ai-models-for-coding-ranked-with-real-prices/))
- **Caution — vendor benchmarks:** Kimi K2.7 Code entered Copilot GA on
  Moonshot's *own* benchmarks only — as of Jul 2026, zero independent
  results on SWE-bench Verified/Pro, Terminal-Bench, or LiveCodeBench.
  Treat single-vendor numbers as directional.
  ([techtimes.com](https://www.techtimes.com/articles/319556/20260702/open-weight-ai-enters-github-copilot-kimi-k27-code-costs-less-audits-differently.htm))

**Research threads (arXiv, 2026):**
- **Routing** (directly relevant to kimi-auto): "The Routing Plateau"
  (May 2026) — accuracy limits of routers and how to break them;
  **RLCascadeRouter** (arXiv:2608.15817, Aug 16) — RL cascade routing *without*
  a quality estimator; **LLMRouter** (Aug 6) — unified infra for building/eval/
  deploying routers; TwinRouterBench (May); full survey arXiv:2603.04445
  (updated Aug 30). The field is converging on **cascades** (cheap model
  first, escalate on uncertainty — UCCI, arXiv:2605.18796) over single-shot
  classification.
- **Inference**: FASER (arXiv:2604.20503) and SPECTRE (arXiv:2605.08151) push
  speculative decoding into dynamic serving; SPEED-Bench standardizes
  spec-decoding eval; "Speculative Decoding: Performance or Illusion?"
  (Mar 2026) is the skeptical counterweight worth reading before investing.

---

## 5. Eval / benchmark state — what's credible late 2026

- **The single most important eval paper of the summer:**
  *"Position: Coding Benchmarks Are Misaligned with Agentic Software
  Engineering"* (arXiv:2606.17799, Jul 18). Core argument: current coding
  benchmarks **conflate model + harness + environment into one end-to-end
  score**; any single component can swing results by margins comparable to
  *adjacent model generations*. Single-reference grading penalizes equally
  valid solutions. **A coding agent is a system, not a model** — benchmark
  the harness components separately.
- **Benchmark zoo (all 2026):** SWE-Bench ProMax (large-scale multilingual
  refactoring), RigorBench (engineering *process* discipline),
  Dialogue SWE-Bench, OmniCode, REAP (curating benchmarks from production
  usage), ProjDevBench (end-to-end project dev), Terminal-Bench 4.0,
  LiveBench, **DeepSWE Best** (the agent ranking ValueRank builds on).
- **Assume a ~37% lab-to-production gap.** Enterprise eval firm Kili finds
  production agentic systems underperform lab benchmark scores by 37% on
  average — and the gap is sharpest when all numbers come from one vendor.
- **What's gamed:** anything with a public test set and vendor-reported
  numbers (see Kimi K2.7 Code above); single-reference code benchmarks;
  "saturates frontier benchmarks" as a claim (GPT-6 Astra) — saturation
  means the *benchmark* is exhausted, not that the model is perfect.

---

## 6. Practical takeaways — for Chris's stack

1. **kimi-auto's Kimi-only bet looks increasingly right.** Kimi K3 is the
   strongest open agentic/coding model, Moonshot's API is live, and the
   router literature is converging on cascades: cheap tier
   (GLM-5.3-Flash at $0.15/$0.50, or DeepSeek cached at ~$0.004/M input)
   → escalate to K3/frontier on uncertainty. The Routing Plateau paper is
   your required reading before tuning thresholds. Still missing: the
   rotated Kimi API key.
2. **Price on effective cost, not list.** With Fable 5.1's cache cut and
   DeepSeek-style prefix caching, a router that maximizes cache hits beats
   one that minimizes sticker price. kimi-auto should track
   cost-per-completed-task (the Sonnet 4.5 lesson), not cost-per-token.
3. **tau: benchmark the harness, not just the model.** The 2606.17799
   position paper is an architectural directive: separate scores for
   model / prompt-harness / tool-environment / iteration policy, or your
   evals will lie to you every time you change a system prompt. Also —
   tool-call reliability is the #1 model-selection metric for agents;
   evaluate candidate models on 80-step tool-use traces, not MMLU.
4. **NIM: upgrade to 2.0.12+ and watch Rubin CPX.** 2.5× throughput on
   Nemotron-class models via MoE-aware spec decoding is free performance;
   Rubin CPX (end of 2026) is explicitly built for the 1M-context serving
   your agent workloads want. Nemotron 3 Ultra is the reference NIM model
   family now.
5. **Self-host tier that fits a 3090:** Qwen3-Coder 30B-A3B today;
   GLM-5.3-Flash / DeepSeek V4-Flash with a second GPU. The 1T+ club
   (K3, V4 Pro, Qwen3.8-Max) stays API-only — but their *APIs* are cheap
   enough ($0.15–$0.87/M in) that self-hosting is a sovereignty play, not
   a cost play.
6. **Resilience is now a routing feature.** Sep 3 proved single-vendor and
   even multi-vendor-naive setups fail together. kimi-auto's multi-provider
   failover isn't cost optimization — it's the continuity plan. Test it
   with a simulated provider outage, not just price tables.
7. **Clock speed warning:** model IDs go stale in weeks. Anything in tau /
   kimi-auto that hard-codes a model list needs a refresh cadence (or
   better: resolve "best Kimi coder" dynamically at runtime, which is
   already kimi-auto's design).

---
*Sources: arXiv via arxiv-mcp + emergent-enrich paper router (credits_spent:
false); web via live search 2026-09-14. Model prices are point-in-time and
move fast — re-verify at deploy time.*
