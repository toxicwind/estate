# yote-maximal: paper research — LLM serving throughput + task scheduling
Track: herd throughput on yote (llama-swap :25100, RTX 3090 24GB). 2026-09-20.

## Serving throughput

1. **Orca** — Yu et al., OSDI 2022. arXiv:2206.01288
   Iteration-level scheduling: reschedule the batch every decode step instead of
   waiting for a static batch to finish; selective batching applies batching only
   where legal. 36.9x vs FasterTransformer on GPT-3 175B. This is the "continuous
   batching" all modern engines inherit.
   Yote mapping: llama.cpp `--parallel N` slots are the in-server version of this;
   we run N=1 everywhere (bump to 4 on tiny hot models = change B).

2. **Efficient Memory Management for LLM Serving with PagedAttention (vLLM)** —
   Kwon et al., SOSP 2023. arXiv:2309.06180
   KV cache as virtual memory: non-contiguous block allocation kills fragmentation,
   2-4x throughput at equal latency. Copy-on-write prefix sharing across requests.
   Yote mapping: llama.cpp has no paged KV; our equivalent lever is right-sizing
   `--ctx-size` per model (already done via CTX_* macros) and not over-provisioning
   parallel slots (KV per slot is the binding constraint on change B).

3. **Sarathi-Serve: Taming Throughput-Latency Tradeoff** — Agrawal et al., 2024.
   arXiv:2403.02310
   Chunked prefill: split long prefills into ~512-token chunks interleaved with
   decode steps; decode-prioritized, stall-free; 2.6x capacity vs vLLM, P99 TTFT
   6.8x better under mixed workloads. Merged into vLLM/SGLang.
   Yote mapping: not available in llama.cpp; our analogue is keeping long-context
   monsters (256k) out of the hot path and preloading the short-context fast
   models (change A).

4. **SGLang: Efficient Programming of LLM Applications (RadixAttention)** —
   Zheng et al., 2024. arXiv:2312.07104
   Radix-tree prefix cache + cache-aware scheduling: shared system prompts and
   few-shot prefixes skip recompute across requests.
   Yote mapping: llama.cpp `--cache-prompt` exists but unused in herd cmds;
   candidate follow-up: enable prompt caching on the preloaded hot models whose
   traffic shares system prompts (agent workloads do).

5. **Fast Inference from Transformers via Speculative Decoding** —
   Leviathan et al., 2022. arXiv:2211.17192
   Draft-then-verify with a small drafter; exact target distribution preserved;
   2-3x decode speedup when acceptance is high.
6. **Accelerating LLM Decoding with Speculative Sampling** — Chen et al., 2023.
   arXiv:2302.01318 (DeepMind, same idea, sampling-correct acceptance rule).
7. **Medusa** — Cai et al., 2024. arXiv:2401.10774 — extra decoding heads predict
   t+2..t+k, tree attention verifies in one pass; 2.2-3.6x, no separate drafter.
8. **SpecInfer** — Miao et al., 2023. arXiv:2305.09781 — token-tree verification.
   Yote mapping: ALREADY PARTIALLY EXPLOITED — herd ships MTP variants
   (qwen-flash-mtp-*, gemma-mtp-*) and DFlash drafter pairs
   (QWEN36_27B_DFLASH_DRAFTER); the `-mtp`/`-dflash` model entries are this
   technique in production. Do not duplicate; measure their acceptance via
   draft_tokens/draft_acc_tokens in the activity table.

9. **SplitWise** — Patel et al., 2024. arXiv:2311.18677 — disaggregate prefill
   and decode onto different machines; each phase has different bottlenecks.
10. **DistServe** — Zhong et al., 2024. arXiv:2401.09670 — disaggregated serving
    with placement/search for prefill/decode.
    Yote mapping: single-GPU box; disaggregation across machines is out of scope,
    but the *phase* insight applies: our P50 (72ms) vs P99 (7.7s) gap is a
    prefill/cold-load problem, attacked via preload (change A), not decode.

11. **Prompt Cache** — Gim et al., 2023. arXiv:2311.04934 — cache attention
    states of reusable text spans; 90% cheaper on repeated context.
    Yote mapping: same as (4); agent system prompts are the reuse vector.

## Task scheduling (fifo vs alternatives)

12. **Scheduling Multithreaded Computations by Work Stealing** —
    Blumofe & Leiserson, JACM 1999. The classic: idle workers steal from busy
    workers deques; provably near-optimal for DAG-structured parallel work.
    Yote mapping: llama-swap fifo is INHERENT (binary: "Only fifo is currently
    supported"). Work-stealing cannot replace it inside the binary; the place it
    CAN live is one layer up: the herd-ranker/probe workers, the burst harness,
    and any agent-side fan-out (kimi-auto resolver already does provider-aware
    raced dispatch, which is work-stealing in spirit: race freely across
    providers, 2s min-interval per provider).

## Scheduler-design references (GitHub, cloned ideas not code)
- vllm-project/vllm v1 scheduler: token-budget loop, running-first then waiting,
  preempt-lowest-priority on KV pressure.
- SGLang scheduler: waiting/running lists, one-kind batch per step by default,
  chunked prefill as bounded mixing.
- mostlygeek/llama-swap: fifo scheduler + matrix router (exclusive sets,
  evict_costs) + selectors (warm/pin/spillover) + hooks.preload + ttl:0 =
  resident. Warm selectors are the closest available thing to work-stealing at
  the front door: route to whichever family member is already loaded.
