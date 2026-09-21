# docs/

Architecture + ops documentation for sovereign-projects. New docs go in `docs/plans/` (proposals) or `docs/audits/` (verdicts); bridge/cell docs live in `hatch/docs/`.

> [!NOTE]
> **Required reading for every agent in the fleet:** [`fleet-knowledgebase.md`](fleet-knowledgebase.md) — estate map, active crews, repo index, standing rules, docs index.

> [!TIP]
> New here? Read in this order: [fleet-knowledgebase](fleet-knowledgebase.md) → [ARCHITECTURE](ARCHITECTURE.md) → [CONTROL_PLANE](CONTROL_PLANE.md) → the topic you need below.

## Contents

- [Architecture](#architecture-the-design-of-the-stack)
- [Inference & routing](#inference--routing)
- [Hardware & OS tuning](#hardware--os-tuning-awrawr-pc)
- [Research](#research)
- [Inventories & plans](#inventories--plans)
- [Full README map](#full-readme-map)

## Architecture (the design of the stack)

- [ARCHITECTURE.md](ARCHITECTURE.md) — Sovereign Architecture, the single source of truth
- [CONTROL_PLANE.md](CONTROL_PLANE.md) — the control-plane design
- [UNIVERSAL_ARCHITECTURE.md](UNIVERSAL_ARCHITECTURE.md) — polyglot stack architecture (August 2026)
- [STORAGE_TIERING_AND_CACHE_ARCHITECTURE.md](STORAGE_TIERING_AND_CACHE_ARCHITECTURE.md) — storage tiering & cache design
- [PRE_RELEASE_INTEGRATION_ENGINE.md](PRE_RELEASE_INTEGRATION_ENGINE.md) — pre-release integration engine
- [HINDSIGHT_TAU_INTEGRATION.md](HINDSIGHT_TAU_INTEGRATION.md) — Hindsight + Tau long-term memory architecture

## Inference & routing

- [free-tier-models.md](free-tier-models.md) — free-tier model routing ground truth (2026-09-14)
- [naming-grammar.md](naming-grammar.md) — canonical model naming grammar (2026-09-20)
- [naming-rename-plan.md](naming-rename-plan.md) — naming rename plan (2026-09-20)
- [RIDICULOUS_MULTI_PROFILE.md](RIDICULOUS_MULTI_PROFILE.md) — multi-profile model router setup
- [KERNELOPTS_LLM_TUNING_AND_RANKING.md](KERNELOPTS_LLM_TUNING_AND_RANKING.md) — kernel-opts LLM tuning & algorithmic ranking reference
- [REASONING_SUPPRESSION_TEST.md](REASONING_SUPPRESSION_TEST.md) — reasoning suppression test verdict
- [MORPHE_PATCHING.md](MORPHE_PATCHING.md) — Morphe patching research SSOT
- [gemini-tool-retrieval.md](gemini-tool-retrieval.md) — Gemini API tool retrieval integration brief
- [NVIDIA_NIM_API_DOCS.md](NVIDIA_NIM_API_DOCS.md) — NVIDIA NIM API reference
- [edge-additions-20260920.md](edge-additions-20260920.md) — September-2026 cutting-edge additions: keypool racing, hedged racer, routing scores, squawk history search (impact-ordered, with paper lineage)

## Hardware & OS tuning (awrawr-pc)

- [HARDWARE_AUDIT_20260914.md](HARDWARE_AUDIT_20260914.md) — hardware audit classification (2026-09-14)
- [GPU_COOLING.md](GPU_COOLING.md) — RTX 3090 cooling · LACT · undervolt notes
- [SWAP_OPTIMIZATION.md](SWAP_OPTIMIZATION.md) — swap architecture: zram / zswap / NVMe tiering
- [SWAP_QUICKREF.md](SWAP_QUICKREF.md) — swap architecture quick reference
- [postgres-ownership.md](postgres-ownership.md) — PostgreSQL ownership decision (2026-09-14)

## Research

- [ARXIV_EMERGENCE_SURVEY.md](ARXIV_EMERGENCE_SURVEY.md) — arXiv emergence survey synthesis
- [KIMI_CODE_FORK_RESEARCH.md](KIMI_CODE_FORK_RESEARCH.md) — Kimi code fork feasibility research

## Inventories & plans

- [fleet-inventory-20260914.md](fleet-inventory-20260914.md) — fleet inventory + completion reconciliation (2026-09-14)
- [plans/](plans/) — proposal docs (see `plans/` for the full list)
- [audits/](audits/) — audit verdicts and bid documents (see `audits/`)
- [Meta/](Meta/) — field notes on the Muse platform (runtime cells), evidence-based
- [MANIFESTO.md](MANIFESTO.md) — memetic forensics analysis (cultural artifact, not architecture)

## Full README map

All 445 READMEs in this repo, deeplinked: [README-INDEX.md](README-INDEX.md).

> [!WARNING]
> Some older docs predate the 2026-09-20 reorg and may reference moved paths (`hatch/`, `bridge/`, `scratch/`). When in doubt, `pitchfork.toml`, `mise.toml`, and `config/ports.env` are the live sources of truth.

---

*Up: [root README](../README.md) · [fleet knowledgebase](fleet-knowledgebase.md) · [↑ top](#docs)*
