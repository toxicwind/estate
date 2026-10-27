# Recursive AGENTS.md / emergent-agent organization — 5+ repo comparison

Recovered alongside the GitHub sort algorithm (`docs/github-search-sort-algorithm.md`).
Research method: broad gh search (sorted by `updated`, NOT stars) → shallow README/
tree dig → deep read of each. All candidates are emergent/low-star, not the obvious
darlings, so they represent real, recent practitioner patterns.

## The repos

| #   | repo                                      | what it does                                                                                            | recursive mechanism                                                                                                     | standout idea                                                                                                                                                                                                                                |
| --- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `ztxtech/light-rsi`                       | lightweight recursive self-improvement (RSI) loop, no SDK/deploy                                        | `goal→diagnose→independent diagnosis→gated brainstorm→external evidence→implement→independent evaluation→iterate→close` | **independent/blank-context evaluator** (judges without inheriting the main agent's reasoning) + **mandatory gate before every decomposition** (choose serial vs parallel isolation); a discrete web-research agent injects outside evidence |
| 2   | `antonio-ivanovski/agents-recursive-init` | skill that recursively **initializes/updates** `AGENTS.md` for every first-level package dir (monorepo) | dispatches subagents per package to write a concise AGENTS.md; warns to use a **low-cost subagent model**               | per-package AGENTS.md for monorepos; cost-aware subagent dispatch                                                                                                                                                                            |
| 3   | `originalankur/GenerateAgents.md`         | auto-generates AGENTS.md for any repo                                                                   | **dspy.RLM (Recursive Language Models)** + deep codebase exploration + **git-history anti-pattern deduction**           | long-context recursion; Strict vs Comprehensive output styles; 100+ providers via LiteLLM                                                                                                                                                    |
| 4   | `payneio/agent-context`                   | assembles project agent context as JSON; walks **up** the tree collecting `AGENTS.md`                   | **recursively dereferences every `@mention`** inside the files into concrete attachments                                | solves the practical gap: runtimes read the nearest AGENTS.md but don't resolve its references                                                                                                                                               |
| 5   | `EthanThatOneKid/zocomputer-agents.md`    | design proposal: derive scoped, inspectable "Zo Rules" from recursive AGENTS.md                         | AGENTS.md = **portable source**; a derived Rule = **compiled, task-scoped output**                                      | treats AGENTS.md as compile-time source vs runtime-compiled task scope (no duplication)                                                                                                                                                      |
| 6   | `Jeremiahhamilton/Sentient-Swarm`         | self-contained swarm CLI (Python)                                                                       | CLI-driven multi-agent swarm                                                                                            | emergent swarm harness; low tooling                                                                                                                                                                                                          |

## Cross-cutting patterns (how people organize recursive agents)

1. **Isolated / blank-context evaluators** (light-rsi): the "judge" must NOT share the
   main agent's reasoning, or self-improvement collapses into self-confirmation.
2. **Explicit decomposition gate** (light-rsi): before every brainstorm/decompose,
   a gate picks serial (cheap/linear) vs parallel (concurrency-isolated) — recursion
   is bounded by isolation, not unbounded spawning.
3. **AGENTS.md as hierarchy, recursed**: two distinct recursions —
   (a) _discovery-up_ (agent-context walks up and dereferences @mentions), and
   (b) _generation-down_ (agents-recursive-init / GenerateAgents.md write/refresh
   per-subsystem AGENTS.md).
4. **Agent instructions are compile-time, not ambient**: zocomputer compiles scoped
   AGENTS.md → task-limited rules, avoiding runtimes re-reading/re-resolving refs.
5. **Cost discipline on recursion**: recursive subagent spawning must pin a cheap
   model and bound fan-out (agents-recursive-init's explicit warning; light-rsi's gate).
6. **External evidence injection**: self-improving agents pull outside info via a
   dedicated research agent rather than only introspecting their own repo
   (light-rsi's web-research agent; GenerateAgents.md's git-History deduction).

## Estate relevance

The estate already embodies several of these (estate-brain personas with per-agent
AGENTS.md; `delendai recurse` "next six emergent tasks"; agent-orchestration-derived
roster). The recovered pattern to borrow most directly: **blank-context independent
evaluators + a bounded decomposition gate** in our recursive delendai/emergent loops,
and **recursive `@mention` dereference up the tree** (agent-context) so instructions
resolve their references once instead of per-runtime.
