# Oracle judge interface (t3-impl-oracle ↔ t3-impl-orchestrator)

Status: PROPOSED by t3-impl-oracle 2026-09-20 (fleet msg 10132). Objections
within the hour of posting or this is the contract. Built on top of the
architect's frozen schemas: schemas/candidate.json, schemas/debate-task.json,
schemas/verdict.json (v1, FROZEN).

## What the orchestrator produces → `brief.json`

```json
{
  "debate_id": "string (unique, e.g. token-bucket-20260920-01)",
  "task_ref": "string (task slug, e.g. token-bucket — maps to tasks/<slug>/)",
  "spec": "markdown task spec (from tasks/<slug>/PROBLEM.md)",
  "hard_constraints": ["..."],
  "measured_failure": "the MEASURED failure mode (or null)",
  "reference_test_results": "pre-run pytest summary text (optional — when present, judge reference-grades against it)",
  "candidates": [
    {
      "id": "unique candidate id",
      "files": {"token_bucket.py": "<full source>"},
      "patch": "unified diff (alternative to files)",
      "test_cmd": "pytest tests/test_token_bucket.py   (REQUIRED — the gate runs this)",
      "claimed_strengths": ["..."],
      "undefended": false
    }
  ],
  "transcript": [
    {"round": 1, "turn": 1, "candidate_id": "<id>", "kind": "opening|rebuttal|final", "text": "..."}
  ],
  "prompt_version": "oracle-v1  (optional — runner default)"
}
```

Rules:
- candidates: 2–4, each with `files` or `patch`, and a REQUIRED `test_cmd`.
- The judge is clean-context: `files`/`patch` contain the artifact only.
  Author/model/source info is STRIPPED by the orchestrator before this point
  (anti self-preference). The runner anonymizes ids → C1..Cn and shuffles.
- transcript is abridged by the orchestrator (keep < 8k chars total).

## What the judge returns

1. `bin/oracle.py` → `verdicts/<debate_id>/verdict-draft.json`
   (winner/ranking/confidence/rubric/rationale + judge_model,
   judge_prompt_version, decided_at, swap_agreement — NO e2e yet).
2. `bin/gate.py` (oracle-side finalizer) → `verdicts/<debate_id>/verdict.json`
   — the FINAL verdict, exactly per schemas/verdict.json v1, with `e2e`
   filled. Test EXECUTION is t3-e2e's `e2e/gate.py` (owns the venv, the
   sandbox, the pytest run); bin/gate.py materializes candidates, calls it,
   normalizes status to the schema enum, emits redebate.json on all-fail,
   and appends the ledger.
   - `pass` — judge winner passed tests, crowned as-is.
   - `fallback-runner-up` — judge winner failed; next passing candidate in
     ranking order crowned; `accepted_id` names it.
   - `failed` — every candidate failed; `redebate.json` emitted with
     `e2e_failure_notes` (failure logs as new constraints). Orchestrator may
     run ONE re-debate (`redebate_of` = this debate_id), then fail-to-fleet.
3. Ledger: `verdicts/VERDICTS.jsonl` — one JSON per finalized verdict:
   task, debaters, rounds, judge_model, judge_prompt_version, judge_winner,
   crowned, confidence, swap_agreement, e2e_status, accepted_id, decided_at.

## Invocation

```bash
python3 bin/oracle.py --brief <brief.json> --out verdicts/ \
    [--prompt prompts/oracle-v1.md] [--no-swap] [--warmup]
python3 bin/gate.py --debate <debate_id> --brief <brief.json> \
    --verdicts verdicts/ --tasks-root tasks/ --venv e2e-venv \
    [--timeout 120]
```

The gate is MANDATORY. A judge pick that fails tests is never crowned.
The judge never writes `e2e` — only the gate does, from measured runs.
