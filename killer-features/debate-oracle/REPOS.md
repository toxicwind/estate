# REPOS.md — debate-oracle vendored repos (t3-repos)

Cloned 2026-09-20 to `/home/toxic/sovereign/killer-features/debate-oracle/vendor/`.
All repos public GitHub, `--depth 1` clones. License check before shipping: llm_debate (Instadeep, check LICENSE), ChatEval (Apache-2.0, THUNLP), debate-or-vote (paper repo, check LICENSE), argus-ai-debate (check LICENSE).
Reuse doctrine: borrow protocol mechanics + prompt skeletons, do NOT inherit their deps (hydra, FastChat, agentverse, pandas DataFrame batch runners are overkill for our oracle).

## 1. `vendor/llm_debate/` — ucl-dark/llm_debate ⭐132 — HIGHEST REUSE
Code for "Debating with More Persuasive LLMs Leads to More Truthful Answers" (Khan et al., UCL/DARK).

**What it implements:** correct-vs-incorrect debater over a reading question; optional cross-examiner; judge picks answer A/B after transcript. Supports sequential and simultaneous rounds, Best-of-N (BoN) debater sampling with a preference model, swap-debating (position-bias control), cached/resumable rollouts, Swiss tournaments, TrueSkill scoring.

**Reusable pieces:**
- `core/rollouts/quality_seq.py` — **round management pattern**: `debate_turn()` per step, sim-round-0 then seq rounds, cross-examiner question before each round's arguments, transcript object carried through rounds, resume-from-cache via `CacheManager`. Direct template for our orchestrator's round loop (3 rounds <=5min).
- `core/agents/judge_quality.py` — **judge mechanics**: `get_transcript()` renders the transcript to judge-visible text with anonymized names ("Debater A"/"Debater B", never real identities — matches our blinded-judge requirement); `fill_in_content()` template-placeholder substitution (`<QUESTION>`, `<ANSWER_A>`, `<ANSWER_B>`, `<TRANSCRIPT>`); **transcript swapping for position-bias control** (`swap_transcript()` swaps correct/incorrect identities so the judge sees both orderings — exactly what PAPERS.md calls for; verdict is the aggregate of both passes).
- `core/config/experiment/judge/debate/default.yaml` — **judge prompt skeleton** (already in our tree; verify against our hardened `prompts/judge.md`): quote-verification system (`<v_quote>` verified vs `<u_quote>` unverified — a quote system is the evidence-checking analogue of our execution-gated judging; debater claims about code must be backed by pytest output, same shape), `<thinking></thinking>` then `Answer: <A|B>`.
- `core/agents/debater_base.py` + `core/config/experiment/debaters/` — debater prompt scaffolding with BoN support.
- `core/rollouts/utils.py` — `TranscriptConfig`/`Round` pydantic models: transcript schema to align our `verdict.json` / candidate JSON against.

**How to invoke:** research harness, not runnable as-is without hydra+OpenAI creds:
`cd llm_debate && python -m core.main` (needs `config/config.yaml`, `method: debate`, `rollout.num_steps: 3`).
Do not run wholesale; lift the patterns into `bin/debate-run`.

**Verdict: PULL** — round manager, judge transcript rendering, swap-both-orderings, BoN sampling. Highest-value file set of the four.

## 2. `vendor/ChatEval/` — thunlp/ChatEval ⭐343 — JUDGE-PANEL REUSE
Code for "ChatEval: Towards Better LLM-based Evaluators through Multi-Agent Debate".

**What it implements:** multi-role referee panel that debates an evaluation before scoring: roles `General Public`, `Critic`, `Scientist` (+ others in config) each score Assistant 1 vs 2 (1–10) after seeing each other's arguments, sequential speaking order, all-visible memory, final forced score emission parsed by `llmeval` output parser.

**Reusable pieces:**
- `agentverse/tasks/llm_eval/config.yaml` — **referee prompt templates**: role_description per persona (General Public = lay judgment, Critic = question others' judgments + offer alternatives when tied), anti-position-bias final prompt ("avoiding any potential bias and ensuring that the order in which the responses were presented does not affect your judgment", "you are not required to output the same value as other referees!"), strict output format (`Evaluation evidence: ...` then `The score of Assistant 1: [score]` / `The score of Assistant 2: [score]`).
- `agentverse/tasks/llm_eval/output_parser.py` — regex-based strict score extraction with retry-on-parse-failure semantics: template for our verdict parser.
- `agentverse/environments/llm_eval.py` — rule-based environment (order/visibility/selector/updater/describer): over-engineered for us, but the *idea* of a rule object (speaking order + who-sees-what) is the right abstraction for mid-round lane cutting.

**How to invoke:** needs FastChat + OpenAI; `python llm_eval.py` (config-driven). Do not adopt agentverse framework; extract prompts + parser only.

**Verdict: PULL prompts** — role personas + strict-format scoring prompts + output parser. Maps to our escalation ladder (cheap parallel jury -> full debate on disagreement): use these roles for the cheap-jury path.

## 3. `vendor/debate-or-vote/` — deeplearning-wisc/debate-or-vote ⭐90 — EVALUATOR REUSE
NeurIPS 2025 Spotlight paper: "Debate or Vote: Which Yields Better Decisions in Multi-Agent LLMs?"

**What it implements:** benchmark harness comparing debate vs majority-vote decision protocols across datasets (GSM8K, CSQA, MMLU, HellaSwag, HH-RLHF, ...): data loaders per dataset, model backends (llama/qwen), a unified `evaluator.py` and `main.py`.

**Reusable pieces:**
- `src/evaluator.py` — decision-aggregation evaluator: pattern for our t3-e2e harness (judge picks + TESTS decide; a protocol should beat the 5-sample self-consistency baseline — PAPERS.md caution).
- `src/data/` — dataset loader pattern (each dataset a small class over `base_ds.py`): template for our e2e corpus task loader (first corpus task).
- `scripts/*.sh` — per-benchmark launch scripts: template for our shakedown-debate launch scripts.

**How to invoke:** `python src/main.py` with `environment.yaml` deps; runs the paper's benchmarks.

**Verdict: PULL for e2e** — evaluator + dataset-loader patterns for the t3-e2e harness. Not a debate protocol source.

## 4. `vendor/argus-ai-debate/` — Argus-Framework/argus-ai-debate ⭐5 — ORCHESTRATOR REUSE
Claim-verification debate: LLMs debate claims; Bayesian reasoning, adversarial evidence, calibrated verdicts, full audit trails. Works with GPT-4/Claude/Gemini/local (Ollama).

**What it implements:** agent roles `moderator` / `specialist` / `refuter` / `jury` (`argus/agents/`), protocol specs (`ARISTOTLE_Protocol_v4.txt`, `CRUX_Protocol_Specification.docx`), architecture diagrams (d2).

**Reusable pieces:**
- `argus/agents/moderator.py` — moderator (round manager) agent: turn-taking + concession detection pattern → mid-round early-stop when a lane concedes.
- `argus/agents/jury.py` — jury verdict aggregation: pattern for our jury fallback (runner-up re-debate escalation).
- `argus/agents/refuter.py` — adversarial refuter role: the "negative" lane template for our rebuttal prompts (`prompts/rebuttal.md`).
- `ARISTOTLE_Protocol_v4.txt` — structured debate protocol spec: compare against ARCHITECTURE.md decisions.

**How to invoke:** check `argus/README.md`; packaging via `MANIFEST.in`.

**Verdict: PULL** — moderator/jury/refuter role patterns; audit-trail design for verdict logging.

## Reuse summary for builders (t3-architect / t3-impl-orchestrator / t3-impl-oracle)
1. **Round loop**: `llm_debate/core/rollouts/quality_seq.py::debate_turn` → template for `bin/debate-run` round manager (timed, cache-resumable, cross-examiner before rounds).
2. **Blinded judge**: `judge_quality.py::get_transcript` (anonymize lanes as A/B) + `swap_transcript` (run judge on both orderings, aggregate) → aligns with ARCHITECTURE.md blinded-judge decision; verify our `prompts/judge.md` against `core/config/experiment/judge/debate/default.yaml`.
3. **Debater sampling**: BoN in `debater_base.py` → cheap lanes get N samples, best argued via preference model.
4. **Cheap jury**: ChatEval referee roles + strict score parser → escalation-ladder fast path; full debate only on disagreement.
5. **E2E harness**: debate-or-vote `evaluator.py` + `src/data/base_ds.py` → t3-e2e corpus loader and "judge picks, tests decide" aggregation.
6. **Moderator/jury/refuter**: argus agents → orchestrator's lane-cutting and escalation logic.
7. **License note**: verify each repo's LICENSE before vendoring code into our tree (not just borrowing patterns).

Perf note (cell saturated at 4.8x when cloned): clones done via yote-side git over bridge; no heavy local compute. All four repos are research harnesses — do not install their full dep trees on the cell.
