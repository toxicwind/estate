---
name: agent-paradigm-audit
description: >-
  Neutral audit of 2026 AI-agent paradigms (openclaw-style agent-runtime era).
  Run a weighed, evidence-backed audit that maps each paradigm to
  strengths/when-to-use/when-not, grounded in the real October-2026
  orchestration literature and in concrete estate reality — never hand-waving
  or vendor cheerleading. Triggers on: agent paradigm audit, orchestration
  paradigm comparison, multi-agent runtime survey, agent runtime era, is the
  coordination layer the product, MAS topology review, weigh agent frameworks.
---

# Agent-Paradigm Audit (October 2026)

An audit is not a survey. A survey lists. An audit **weighs each paradigm's
claims against its stated limits, with evidence and a decision table at the
end.** This skill encodes a reproducible, neutral procedure for auditing the
2026 application-agent paradigms that coalesced around what the industry calls
the "openclaw"-era agent runtime: agents as stateful, tool-calling processes
whose coordination, memory, and accountability are more important than the
underlying model.

The framing is deliberately _neutral_: every paradigm below has shipped real
systems, every one has real failure modes, and none is a silver bullet. The
artifact this skill produces is a scored comparison an engineering leader can
act on — not a recommendation wrapper around a favorite framework.

## Paradigm Map

The 2026 landscape sorts into four coordinating ideas, not four products. Each
is defined by _what it moves the complexity into._ Keep the four-axis frame in
mind on every audit: **deterministic orchestration, infrastructure-aware
routing, learning from past runs, and settlement/accountability.**

| Paradigm                               | Core claim                                                                            | Moves complexity into                                         | Evidence (verified 2026-10-22)                                                                                                           | Limits                                                                        |
| -------------------------------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| **Deterministic orchestration**        | A typed, explicit control plane makes multi-agent runs reproducible and safe          | Explicit workflows, typed memory, semantic graph reasoning    | Jasper OS Research Archive (DOI 10.5281/zenodo.21450024); WorkflowOps (arXiv 2610.07860) memoryful priors; Corral+DelendAI in the estate | Over-specification: novelty is the first casualty, unless the graph can learn |
| **Infrastructure-aware orchestration** | Model + routing choice is a serving-infrastructure decision, not a prompt decision    | Runtime-aware schedulers, shared GPU/queue state              | INFRAMIND (arXiv 2606.11440); hodos/EAP/theta model routing in the estate                                                                | Couples orchestration to live infra state → harder to reason about offline    |
| **Self-grading orchestration**         | Feedback on run quality can be learned without human labels                           | Reward models / transition-probability priors built from logs | OrchRM (arXiv 2606.13598); delend-experimental self-healing loops                                                                        | Reward hackery, ambiguous credit assignment, cold-start before enough history |
| **Settlement & accountability**        | Multi-agent work needs cryptographic/legible accountability and multi-rail settlement | Audit trails, attestations, bidding, Vickrey settlement       | Jasper OS "multi-rail settlement"; oracle-market in the estate                                                                           | Overhead; drives behavior toward what is wascally auditable                   |

Safety/malice also has a published taxonomy — the "Orchestration and
Verification of Agentic AI Systems: Survey" (DOI 10.59324/ejaset.2026.4(2).16)
frames it as MAS orchestration topologies plus a threat model (prompt
injection, access-control, escalation). Enterprise deployments lean on managed
orchestrators; see the Agentforce-in-enterprise-CRM account (DOI
10.22399/ijcesen.5331) for a single-vendor managed-runtime case.

## Oracle-Decision-Table

Run an audit to produce this table. For each paradigm (`P`) and each
requirement axis (`R`), score `Strong / Partial / Weak / N/A` and annotate the
claim with the evidence line that justifies it. Do not invent scores; every
cell names its supporting citation or estate system.

| Axis (`P` → optimizes)     | Deterministic                         | Infra-aware                    | Self-grading                                        | Settlement                                  |
| -------------------------- | ------------------------------------- | ------------------------------ | --------------------------------------------------- | ------------------------------------------- |
| **Reproducibility**        | Strong — explicit graph, typed memory | Weak — depends on live infra   | Partial — priors describe history, not the next run | Strong — runs are cryptographically legible |
| **Novelty / exploration**  | Weak — fixed topology                 | Partial                        | Strong — reward can reward surprise                 | Neutral — does not foster or block          |
| **Operational cost**       | Medium                                | Low (shares queues)            | Low after training                                  | High (audit + settlement overhead)          |
| **Failure accountability** | Strong — you know which step broke    | Weak                           | Weak — credit is ambiguous                          | Strong — who did what is settled            |
| **Cold start**             | Strong — works day one                | Medium — needs infra telemetry | Weak — needs history to learn                       | Medium — needs settlement rails to exist    |

How to weigh: multiply score by _your_ context. A solo research rig values
**novelty × self-grading**; a regulated enterprise values **accountability ×
deterministic**; a GPU-constrained shop values **operational cost ×
infra-aware**. The output is a ranked shortlist, not an absolute champion.

## How-To-Run-An-Audit

1. **Collect the paradigm claims.** For each candidate — deterministic /
   infra-aware / self-grading / settlement — write down its _stated benefit_
   and its _stated cost_. Source these from the paper or documented system, not
   from blog marketing. Persist the claim's provenance (DOI / arXiv / repo).
2. **Confront with evidence.** For each claim, ask: does a real system
   demonstrate it? The estate itself is a lab: oracle-market, corral/delendai,
   forever-loop rig + squawk C2, hodos/EAP/theta routing, delend-experimental
   self-healing. Note _what actually happens on the box_ — it is concrete
   evidence, used neutrally (a paradigm can be real in the estate and still
   wrong for a different caller).
3. **Score the decision table.** Fill only cells you can cite; leave N/A rather
   than guess. Record, per cell, `claim → evidence → verdict`.
4. **Weight for the audience.** Read the audience's pain: reproducibility,
   exploration, cost, accountability, or cold-start. Rank paradigms by
   weighted sum.
5. **Write the neutral report.** Thesis → paradigm map → decision table →
   when-to-use/when-not per paradigm → evidence appendix with exact citations.
   No vendor push; a favorable finding is fine, an unearned one is a defect.
6. **Gate.** Re-read the report and confirm every factual claim has a
   citation or a named estate system. If a claim has neither, cut it or feature
   it as open question.

## Evidence & Grounding

Do not fabricate papers. Use this verified October-2026 grounding and extend
only with sources you actually read:

- Jasper OS Research Archive (DOI 10.5281/zenodo.21450024) — deterministic
  orchestration, typed memory, semantic graph reasoning, cryptographic
  accountability, multi-rail settlement.
- INFRAMIND (arXiv 2606.11440) — infrastructure-aware multi-agent
  orchestration; model selection considers serving-infrastructure runtime
  state; shared GPU queues.
- WorkflowOps (arXiv 2610.07860) — orchestration that learns agent-collaboration
  priors from historical workflows; memoryful orchestration; transition-probability
  matrices.
- OrchRM (arXiv 2606.13598) — self-supervised reward modeling to grade
  orchestration quality without human labels.
- "Orchestration and Verification of Agentic AI Systems: Survey" (DOI
  10.59324/ejaset.2026.4(2).16) — MAS orchestration topologies plus a
  safety/threat taxonomy (prompt injection, access-control).
- "Multi-Agent Orchestration in Enterprise CRM: Agentforce" (DOI
  10.22399/ijcesen.5331) — single-vendor managed enterprise orchestration.

Estate reality (the box you can touch): oracle-market (Vickrey bid/attestation
settlement — echoes Jasper OS settlement); corral/delendai (deterministic
orchestration, work-refs, stacking); forever-loop rig daemon + squawk C2
(self-sustaining orchestrator surfacing coordination); hodos/EAP/theta model
routing (infrastructure-aware, echoes INFRAMIND); delend-experimental /
code-race / iterate (self-healing, learned iteration).
