# Bid-Market Repos (t2-repos, 2026-09-20)

Broad GitHub search (5 queries: "contract net protocol multi agent", "auction task allocation agents", "market based task allocation", "multi-agent auction python", "agent task marketplace") -> ~60 candidates. 3 cloned to vendor/, rest evaluated by README+layout.

## CLONED (vendor/)

### 1. auction-agent11 -- wushuchris/11-distributed-auction-task-allocation-agent (MIT)
**What:** Complete distributed typed-auction task allocator. Peers decide BID or ABSTAIN; deterministic scoring: 45% capability + 25% confidence + 20% availability + 10% cost efficiency; deterministic tie-breaks (score, capability, cost, lexical agent_id). Bounded reauction lifecycle: ANNOUNCED -> BIDDING -> AWARDED -> IN_PROGRESS -> COMPLETED / FAILED -> REAUCTIONING -> BIDDING -> COMPLETED/ESCALATED. Append-only protocol events; 150 tests; py3.11.
**Layout:** `src/auction_coordination/`: auction.py (auctioneer/scoring), bidding.py (BidAction, PeerBidSettings), models.py (Bid/BidAbstention/TaskAnnouncement), registry.py (PeerRegistry -- capability authority), settlement.py, reauction.py, runtime.py, evaluation.py; `tests/`: 18 test files.
**Reusable:** the whole core -- auctioneer, bidder-side policy, settlement, reauction, audit events. Closest shape to our bid-market (auctioneer + bidders + deterministic winner + audit).
**Invoke:** `python3 -c "import sys; sys.path.insert(0, 'vendor/auction-agent11/src'); import auction_coordination"`; `pytest` in repo root.
**Caveat:** assumes shared deterministic utility policy; no Byzantine/malicious-bid handling by design.

### 2. agora -- KAIJUJO/Agora (research preview, ACL paper: "Agora: Enhancing LLM Agent Reasoning Via Auction-Based Task Allocation")
**What:** Confidence-calibrated auction allocation for LLM agents. Request -> TaskUnit dependency graph -> per-agent raw confidence -> calibrator (CalibratorBank, OnlineLogitCalibrator) -> bid = calibrated_confidence^gamma - beta*normalized_cost -> execute winner -> compose. Provider-agnostic via small Python callables (FunctionAgent).
**Layout:** `src/agora/`: auction.py, calibration.py, pipeline.py, agents.py, task_units.py, planning.py, interfaces.py, types.py; `examples/minimal.py`.
**Reusable:** bidder-side logic: confidence collection + per-agent calibration over time (online refinement when a verifier exists) and the confidence-vs-cost bid formula. Our bidders can report confidence that the auctioneer calibrates per agent.
**Caveat:** clean framework preview only; no datasets/checkpoints/experiments bundled.

### 3. contract-net-router -- M00C1FER/contract-net-router (MIT, pure stdlib)
**What:** FIPA Contract Net Protocol as a protocol-level primitive for LLM agent dispatch: broadcast -> bid (with confidence) -> award; YAML agent registry (name/tier/specialties/keywords/autonomy/deny_tools); tier weights command 1.30 / strategic 1.15 / tactical 1.00 / rapid 0.80; deny-list enforcement; contract lifecycle PENDING -> AWARDED -> {FULFILLED, VIOLATED, EXPIRED, TERMINATED}; budget envelopes {tokens, dollars} with VIOLATED on overspend; queryable SQLite audit trail; CLI `cnr route`; adapters (AutoGen/CrewAI full; LangGraph/OpenAI/SK/Haystack/DSPy/LlamaIndex stubs).
**Layout:** `src/contract_net_router/`: router.py (bidding engine), contract.py (lifecycle+budgets), `__main__.py`, adapters/; `examples/demo.py`, `examples/agents.yaml`.
**Reusable:** agents.yaml registry format for our fleet bidder registry; budget conservation + SQLite audit for spend-bounded contracts; deterministic tie-break pattern (alphabetical).
**Invoke:** `cnr route --task "..."`, `ContractNetRouter.from_yaml("agents.yaml").route(task)`.

## EVALUATED, NOT CLONED (reuse by reference)
- ArtemisWolf45/dynamic-swarm-coordination -- stdlib-only reverse-auction sim: streaming task arrivals, worker failure + auto re-auction after reassignment delay, task dependencies, capacity constraints, deadline-aware scheduling, metrics. Reauction-pattern reference.
- MartinBraquet/task-allocation-auctions (144 stars, MECC 2021 paper) -- greedy decentralized auction algorithms; `pip install gcaa`; research-grade but robotics-flavored.
- alizangeneh/multi-agent-auction-task-allocation -- clean modular Python sim: CFP/BID/AWARD message schemas, Agent/Task/World/Message split. Message-schema reference for our protocol.
- anneschuth/pinchwork -- **DEPRECATED/archived** (hosted service shut down) but MIT: task post -> pickup -> deliver with credit escrow, smart matching, timeouts, SSE events, CLI. Escrow/settlement design reference only; do not depend on hosted API.
- Dymsia/CNP_CBBA- -- R code only; skipped (no Python).
- Yvan-Dumas/CBAA-Algorithm -- Consensus-Based Auction (centralized+decentralized); secondary consensus approach.
- alphaparkinc/genpark-multi-agent-task-auction-bidding-orchestrator-skill -- skill-flavored task auction orchestrator; secondary.

## REUSE RECOMMENDATIONS (for t2-architect / t2-impl-auctioneer / t2-impl-bidder)
- **t2-impl-auctioneer:** build on auction-agent11 `auction.py` + `settlement.py` + `runtime.py` -- steal deterministic scoring policy, lifecycle states, append-only protocol events; adapt announcements to squawk/fleet channels.
- **t2-impl-bidder:** build on contract-net-router `agents.yaml` registry + Agora confidence bid formula (calibrated_confidence^gamma - beta*cost) + agent11 `bidding.py` PeerBidSettings / BID-ABSTAIN policy.
- **Budgets/audit:** contract-net-router contract lifecycle + budget envelopes + SQLite audit schema.
- **Failure policy:** agent11 bounded reauction (one extra round, failed worker excluded by protocol admission) OR dynamic-swarm reassignment-delay pattern; do not invent new semantics.
- **Message schemas:** start from alizangeneh CFP/BID/AWARD + pinchwork post/pickup/deliver escrow shape.

## SMOKE CHECK
All three vendor repos byte-compile clean under python3 on yote (2026-09-20). Do not push from yote (GitHub push broken) -- local/vendor use only.
