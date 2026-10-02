# toolcall-agent — OPPORTUNITIES (running list, autonomous posture)

Standing killer-feature hunt for the tool-capable local agent track.
Acted-on items move to README "shipped" section; keep this list live.

## ACTED ON
- [x] Persistent tool-capable local endpoint (pitchfork daemon, :25152) — 2026-09-20
- [x] Validator-first agent harness (agent_loop.py) — 2026-09-20
- [x] HFT lane racing for inference (hft_race.py: direct vs herd, first-valid-wins,
      hot conns, winner ledger, P50/P95/P99 bench) — 2026-09-20
- [x] RACE=1 wiring into agent_loop.py — 2026-09-20

## OPEN — high value
- [ ] **Race log → auto lane-cutting.** Ledger shows direct wins ~80%. Add a
      cron/hook that reads race-winners.jsonl weekly: if a lane wins <5% over
      500 races, alert (or auto-disable the peer in herd.yaml). Doctrine:
      "if one lane always wins, the other is dead weight — cut it or fix it."
- [ ] **Third lane: NIM / kimi.** When a capable cloud key is refreshed
      (Agent 2's NVIDIA key blocker), add it as lane 3 with a tight ceiling —
      free redundancy, first-valid-wins. No code change beyond LANES entry.
- [ ] **Tool-result caching (hft_fetch-style stale_cache).** sysinfo(gpu/cpu/
      hostname) never changes within a session; cache tool results with TTL
      (gpu: 1h, memory/uptime: 60s) and skip the model round-trip. Modeled on
      hft_fetch's cache_first.
- [ ] **Speculative tool prefetch.** The model almost always calls sysinfo
      before calculator in chained prompts; prefetch likely-needed facts while
      the model generates (ToolSpec's retrieval-augmented drafting, applied to
      tool *results* instead of tokens).
- [ ] **Grammar-constrained tool args.** llama-server supports --grammar-file;
      add a strict JSON grammar for the calculator/sysinfo arg schemas so
      malformed args are impossible by construction (not just repaired after).
      Research: ToolSpec (arXiv:2604.13519) treats tool calls as constrained
      decoding — push the constraint into the decoder.
- [ ] **P95 latency SLO + alerting.** Bench weekly via cron; alert if p95
      regresses >20%. Borrow open-llm-benchmarks METHODOLOGY.md format.

## OPEN — speculative
- [ ] **xLAM-2 / Hermes-2-Pro side-by-side.** BFCL shows small specialist
      models (xLAM-2-3b-fc-r 65.7%) beating general 7Bs on single-turn calls.
      Race qwen3.5-9b against a 3B specialist lane; keep whichever the ledger
      favors for tool-call-heavy prompts.
- [ ] **Uncertainty-routed fallback (SLM survey 2510.03847).** Confidence-score
      the tool call; low confidence → escalate that single turn to a bigger
      model instead of failing the whole loop.
- [ ] **MTP draft model for tool calls.** Qwen3.6-27B-MTP weight exists on yote;
      llama.cpp MTP speculative decoding could cut tool-call TTFT. Measure
      before/after with the bench harness.
- [ ] **beellama binary swap-in.** When herd-config worker's rebuild lands,
      benchmark beellama fork vs upstream b11059 on the same model via
      hft_race (add as lane 3 temporarily, read the ledger, keep the winner).
