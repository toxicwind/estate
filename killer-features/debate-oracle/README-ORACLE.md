# debate-oracle — oracle judge (t3-impl-oracle)

The oracle judge picks the winning code candidate from a debate, then a
MANDATORY e2e gate crowns only what passes the real acceptance tests.

## Pipeline

```
brief.json ──▶ bin/oracle.py ──▶ verdict-draft.json
                                        │
                                        ▼
                                   bin/gate.py ──▶ e2e/gate.py (t3-e2e owns tests)
                                        │
                                        ▼
                                  verdict.json (schemas/verdict.json v1)
                                  + redebate.json (if all fail)
                                  + VERDICTS.jsonl (ledger)
```

## Judge (bin/oracle.py)

- Consumes the brief per INTERFACE.md (task spec + anonymized candidates +
  abridged transcript + optional reference test results).
- Renders prompts/oracle-v1.md (versioned; see prompts/PROMPT-CHANGELOG.md).
- Model cascade (probed live 2026-09-20): kimi-k3-nim @ :25100 (primary,
  staggered), kimi-k2 @ :25100 (fallback if no valid verdict in 20s).
  Fail-fast ceilings, temperature 0, strict JSON output contract.
- Position-swap check: re-judges with reversed candidate order; disagreement
  costs 0.2 confidence and is recorded (`swap_agreement`).
- The judge NEVER writes `e2e`. A pick that fails tests is never crowned.

## Gate (bin/gate.py)

- Materializes candidates from the brief, runs t3-e2e's e2e/gate.py
  (walks winner → ranking order; first pytest pass wins).
- `pass`: judge winner crowned. `fallback-runner-up`: judge winner failed,
  next passing candidate crowned, rationale annotated.
- `failed`: verdict.json e2e.status=failed + redebate.json with
  e2e_failure_notes (failure logs as new constraints for the single allowed
  re-debate; then fail-to-fleet — orchestrator's trigger).

## Prompt audit (audit/)

audit/audit_v1.py builds a realistic token-bucket brief with hand-written
candidates (correct / subtle-bug-with-eloquent-champion / wrong), grounds
truth against the real hidden tests, runs the judge, and records failure
modes in audit/FINDINGS-v1.md → feeds prompts/oracle-v2.md.

## Lineage

- Rubric + blinded clean-context + synthesis rules: t3-architect
  prompts/judge.md (HARDENED v1).
- swap + <thinking> + strict final-line: ucl-dark/llm_debate
  (vendor/llm_debate/core/config/experiment/judge/debate/default.yaml).
- position/verbosity/self-preference biases + reference grading:
  Zheng et al. 2306.05685 via t3-papers PAPERS.md.
- verdict.json v1 shape: frozen schema, never broken by prompt tuning.
- Extends (not forks) coordinator-1's tools/fleet-ops/oracle-judge concept
  into --mode code: brief/render/readiness + resolve contract preserved.
