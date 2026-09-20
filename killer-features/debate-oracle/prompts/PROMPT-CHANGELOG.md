# Oracle judge prompt changelog

Versioned prompt files. The runner (`bin/oracle.py`) takes `--prompt` and
records `judge_prompt_version` in the verdict, so every verdict is traceable
to the exact prompt text that produced it. Prompt tuning must never break
schemas/verdict.json v1 shape.

## oracle-v1 (2026-09-20, t3-impl-oracle)

Lineage: t3-architect `prompts/judge.md` HARDENED v1.

Changes vs judge.md:
- reason-before-verdict: per-candidate independent 5-axis scoring must precede
  ranking (was "evaluate independently then rank"; now explicit that the JSON
  is emitted only after per-axis reasoning — llm_debate <thinking> lineage).
- `reference_test_results` slot: when the brief carries pre-run pytest output,
  it outranks rhetoric (Zheng-style reference grading, t3-papers TOP-3 #1).
- Output keys restricted to verdict.json v1 fields (winner, ranking,
  confidence, rubric, rationale, optional synthesis_map). Extra keys
  (`undefended_penalty_applied`) are stripped by the runner; keep the prompt
  honest about what survives.
- Position-swap note: runner executes the prompt twice with candidate order
  shuffled; the prompt now instructs order-invariance explicitly and the
  runner checks agreement (Zheng position-bias / llm_debate swap lineage).
- New anti-failure rule 11: EXECUTION BEATS ELOQUENCE — code text and test
  results are facts; debater claims about code behavior are hypotheses.

Provenance of mechanisms:
- swap + <thinking> + "Answer:" final-line discipline: ucl-dark/llm_debate
  (vendor/llm_debate/core/config/experiment/judge/debate/default.yaml)
- position/verbosity/self-preference bias taxonomy + swap + reference grading:
  Zheng et al. "Judging LLM-as-a-Judge" (2306.05685), via t3-papers PAPERS.md
- rubric weights + clean-context blindness + synthesis rules: t3-architect
  prompts/judge.md (kept verbatim where intact)

## oracle-v2 (planned — after prompt audit)

STILL OPEN. Audit v1 (2026-09-20) results:
- winner CORRECT (tb-c1), swap_agreement=true, 10 evidence citations, strawman
  rebuttal correctly discarded, verbosity trap (eloquent C2) resisted.
- F0 FIXED in runner (not prompt): rationale cited [C1 L<n>] line numbers that
  the brief never defined (render_brief emitted unnumbered code). Runner now
  emits line-numbered code blocks (`   1| ...`), making citations verifiable.
  Prompt text unchanged by this fix.
- Audit harness bug fixed: ground_truth used bare `pytest` (cwd not on
  sys.path) so all three candidates spuriously FAILED. Now uses
  `python -m pytest` (t3-e2e's gate already does this correctly).

Candidate hardenings pending further audits:
- If audit shows confidence inflation (0.9+ on weak fields): add calibration
  examples — few-shot anchor verdicts with known outcomes.
- If audit shows rationale citation drift (cites lines that don't exist):
  require citations in [Cx-kind Ln] format and have the runner VERIFY every
  citation against the brief; unverifiable citations → confidence -0.15.
- If audit shows synthesis over-use: tighten rule 7 to require the runner's
  conflict check (synthesis_map elements must reference disjoint code regions).
