# code-racer — Paper Research (T1-PAPERS)

**Topic:** racing diverse code-generation strategies with execution-based selection.
Researched 2026-09-20 by t1-papers (ember). Written for builders: every paper
gets (a) one-paragraph summary, (b) the concrete technique, (c) exactly how it
maps to our harness.

## The unifying lens (read this first)

**"It's MBR All the Way Down" (Freitag et al., arXiv 2310.01387)** reframes
modern generation tricks — self-consistency, MBR-EXEC, crowd sampling, coder-reviewer —
as one thing: *sample a hypothesis set from diverse generators, then select by
expected utility under some metric.* Our harness is literally this: strategies
are the hypothesis generators, the execution score is the utility function,
and selection = MBR with `execution-match` as the gain. Consequence for
builders: **the harness is a general MBR decoder, not a code-racer.** Any new
technique below is a new (generator, metric) pair you can plug in without
changing the core loop.

---

## 1. CodeT — CODE generation with generated Tests (Chen et al., 2022)
**https://arxiv.org/abs/2207.10397**

**Summary:** When you have no oracle tests, generate them too. CodeT samples
code solutions AND test cases from the same LLM, then executes every solution
on every test case and finds *consensus sets* (solutions passing the same
tests) via a RANSAC-like dual execution agreement. It scores each consensus
set as |solutions| × |test cases| — i.e., correctness needs both breadth
(many solutions agree) and depth (many tests agree). Its ablation shows
self-consistency (|solutions| only) and test-count (|tests| only) each perform
*worse than baseline alone* — you need the product of both.

**Technique:** (1) Sample N solutions + M test cases. (2) Execute N×M matrix.
(3) Cluster into consensus sets. (4) Score = |Sx|·|Sy|, pick best solution
from the top set.

**Mapping to our harness:** This is our *default validity/selection function*
when the task ships no tests. Our strategies generate solutions; a "test-gen"
strategy generates tests; the selection step computes the CodeT score over the
N×M matrix instead of plain pass-rate. Concretely: `score(strategy_output) =
consensus_size × tests_passed`. Builders: implement `validity/codet.py` as
the selection rule; the test-generation budget is a first-class parameter
(M tests), not an afterthought.

---

## 2. SRank — Functional Overlap Reranking (2023)
**https://arxiv.org/html/2311.03366v4**

**Summary:** CodeT's consensus sets ignore *relations between clusters* —
clusters that heavily overlap functionally (e.g., two solutions differing on
one edge-case test) are treated as unrelated. SRank models inter-cluster
functional overlap and consistently beats CodeT (e.g., HumanEval WizardCoder34B
75.31 vs 72.36 pass@1; Claude 3 Opus 79.18 vs 77.42). Even without cluster
features, interaction-only reranking beats greedy.

**Technique:** Build consensus clusters like CodeT, then compute pairwise
functional overlap between clusters (shared passed tests), propagate scores
across overlapping clusters, and rank with overlap-aware aggregation.

**Mapping to our harness:** Upgrade path for `validity/codet.py`. Instead of
winner-take-all per cluster, compute the pairwise overlap matrix between all
candidate outputs and let near-duplicate strategies reinforce each other.
Harness hook: after clustering outputs by execution signature, compute a
weighted vote where cluster weight = Σ overlap(cluster, other clusters).
Low-cost: this is pure matrix math over execution signatures we already have.

---

## 3. MBR-EXEC — Execution-based Minimum Bayes Risk Decoding (Shi et al., EMNLP 2022)
**https://aclanthology.org/2022.emnlp-main.231/**

**Summary:** The foundational formalization. Treat program selection as
Minimum Bayes Risk decoding: pick the candidate maximizing expected utility
where utility = agreement on execution outputs across test inputs. Executes
each candidate on a small set of test inputs to *approximate semantic
equivalence* (exact equivalence is intractable). Consistently beats every
execution-unaware selection method. Key caveat from follow-ups: MBR-EXEC is
only as good as its test inputs — on HumanEval's low-quality docstring tests
it underperforms, on MBPP-S it shines.

**Technique:** Sample K candidates. Execute each on T inputs. Cluster by
output vector. Select the candidate with maximum marginal agreement
(Σ over candidates of 1[same outputs]).

**Mapping to our harness:** This is our *selection formalism*. Every race
round ends with: group outputs by execution-output vector, pick the
highest-mass group, return its representative. Builders: the `select()`
primitive in the harness IS MBR-EXEC with test-inputs = our validity suite.
And the caveat maps directly to a design rule: **test-input quality is the
selection ceiling** — budget more on generating/validating test inputs than
on extra candidate strategies past the point of diminishing diversity.

---

## 4. Multi-Prompt MBR (OpenReview hTr8s95SYA)
**https://OpenReview.net/pdf?id=hTr8s95SYA**

**Summary:** The paper closest to our "racing strategies" idea, from the MBR
side. Framing: *each prompt defines a unique distribution over candidates*,
so decoding from multiple prompts = combining multiple candidate
distributions. Empirically, multi-prompt candidate sets beat single-prompt MBR
across candidate-set sizes — until τ→2, where everything is too noisy.
Diversity across prompts helps even when individual prompts are weaker.

**Technique:** Sample from P prompts (prompt bank), pool candidates, run MBR
selection over the pooled set. Ablations show the gain is from distribution
diversity, not prompt quality.

**Mapping to our harness:** This is the *theoretical license for our
strategy-racing design*. Our K strategies ARE P prompts in this paper's
terms: different system prompts / temps / framings each define a different
candidate distribution, and pooling + execution-selection beats any single
strategy. Two actionable rules: (1) optimize strategies for *distributional
diversity* (different failure modes), not individual strength — a weak but
uncorrelated strategy adds more than a strong but correlated one; (2) track
the τ→2 limit: past a diversity point the pool is noise, so keep a quality
floor per strategy.

---

## 5. LEVER — Learning to Verify with Execution (Ni et al., ICML 2023)
**https://arxiv.org/abs/2302.08468**

**Summary:** Heuristics over execution results (pass/fail) throw away signal.
LEVER trains a small verifier (~0.5% the size of the generator) on
(NL input, program, execution results) → correct/incorrect, then reranks by
mixing verifier score with generation probability and marginalizing over
programs with identical execution results. +4.6% to +10.9% over base LLMs,
SOTA on all four benchmarks. The learned verifier beats hand heuristics
because it reads *semantic features* of execution (data types, value ranges),
not just pass/fail.

**Technique:** (1) Sample programs. (2) Execute, collect rich execution
artifacts (outputs, types, exceptions, timing). (3) Trained verifier scores
each (input, program, execution) triple. (4) Final rank =
α·verifier_score + (1−α)·log p_LM, marginalized over execution-equivalent
programs.

**Mapping to our harness:** Two-tier validity. Tier 1 (now): heuristic
validity = pass/fail on the test suite — that's CodeT/MBR-EXEC. Tier 2
(follow-up): replace the heuristic with a learned verifier trained on our
race logs: every race produces labeled (task, program, execution-trace,
final-verdict) triples — the training set accrues *for free*. Builders:
log execution artifacts richly NOW (tracebacks, output types, timing), even
if the verifier comes later; LEVER tells us that data is the moat.

---

## 6. AlphaCode (Li et al., Science 2022)

**Summary:** The scale proof. AlphaCode samples ~10³–10⁶ candidates per
problem, filters by execution on example tests, then *clusters remaining
candidates by behavior on generated test inputs* and submits from the largest
clusters. Massive sampling + execution clustering reached median
competitive-programmer performance. The selection insight: at scale you
cannot inspect candidates; you must let execution outputs do the clustering.

**Technique:** Massive temperature sampling → executability filter on given
examples → generate test inputs (separate model) → cluster candidates by
input/output behavior → sample submissions from largest clusters.

**Mapping to our harness:** The high-K regime. When a strategy budget allows
100+ samples, don't rank by per-candidate score — cluster by execution
signature and allocate budget to the largest clusters (our CodeT/SRank
selection already does this). Also: AlphaCode's example-test filter maps to
our "cheap pre-filter" — run the task's given examples first, drop failures
before the expensive validity suite (E2E cost discipline).

---

## 7. EnsLLM — Enhancing LLM Code Generation with Ensembles (2025)
**https://arxiv.org/abs/2503.15838**

**Summary:** Instead of sampling one model, generate candidates from
*multiple different LLMs* and select by structured voting: syntactic/semantic
similarity (CodeBLEU) + behavioral equivalence via differential testing
(CrossHair property-based testing generates counterexamples where candidates
disagree). Pairwise scores aggregated per candidate; highest wins. 90.2%
HumanEval / 50.2% LiveCodeBench, beating GPT-4o standalone; open-source-only
ensemble hits 80.5%/41.6%.

**Technique:** Cross-model candidate pool → pairwise CodeBLEU similarity +
CrossHair differential counterexamples → behavioral similarity metric →
aggregate → argmax.

**Mapping to our harness:** Our strategies need not all be the same model.
A "model" dimension is orthogonal to "prompt" diversity: {model × prompt ×
temp} is the full strategy space. CrossHair-style differential testing maps
to a *differential validity strategy*: when candidates disagree, auto-generate
the distinguishing input and add it to the test suite — the test suite
*improves itself* during the race. Builders: add a `strategies/model_zoo.py`
axis and a differential-test generator in the validity pipeline.

---

## 8. EFFICODE — On Sample-Efficient Code Generation (Han et al., EMNLP 2023)
**https://aclanthology.org/2023.emnlp-industry.73/**

**Summary:** Best-of-n is wasteful: it samples equally on problems the model
can and cannot solve. EFFICODE estimates *solvability* per problem and
prioritizes the sampling budget on solvable ones, cutting sampling cost with
comparable pass@k. It also prunes syntax-error-heavy incorrect code early via
adaptive decoding (early termination of doomed samples). Selection without
execution also works via their ranking.

**Technique:** Solvability estimator → adaptive budget allocation per problem;
early termination of partial decodings that show syntax-error signals.

**Mapping to our harness:** This is our *budget governor*. Racing K
strategies × N samples is expensive; EFFICODE says: (1) estimate task
solvability first (cheap: one greedy sample + test pass rate) and scale the
race budget accordingly — easy tasks get 1 strategy, hard tasks get the full
hedge; (2) kill doomed candidates early (syntax errors, instant exceptions)
instead of running the full validity suite. Builders: `governor.py` —
solvability probe → dynamic K/N, plus a fast-fail validity tier (compile +
smoke test) before the full suite. Direct HFT synergy (see below).

---

## 9. AdapT — Improving Code Generation by Dynamic Temperature Sampling (2023)
**https://arxiv.org/abs/2309.02772v1**

**Summary:** Code tokens split into *challenging* (hard to predict, mostly at
block starts — control flow, API choices) and *confident* tokens. One global
temperature is wrong: high temp everywhere adds tail noise, low temp
everywhere kills exploration. AdapT uses high temperature on challenging
tokens, low on confident ones — significantly outperforming SOTA decoding.

**Technique:** Per-token temperature schedule driven by a
challenging/confident classifier over token positions.

**Mapping to our harness:** A *within-strategy* diversity knob for our
strategy implementations. Builders: strategies shouldn't all sample at
T=0.8; implement AdapT-style schedules (or simpler: high-temp-first-few-tokens
then low-temp) as a strategy parameter. Cheaper than adding a whole new
model: it extracts more *effective* diversity per sample from the same
strategy.

---

## 10. Coder-Reviewer Reranking (Zhang et al., 2022)
**https://arxiv.org/pdf/2211.16490**

**Summary:** Score candidates by the product of coder likelihood
P(code|task) and reviewer likelihood P(task|code) — the code must be probable
given the task AND the task must be probable given the code (round-trip
consistency). Competitive with CodeT while being more general: it needs no
generated test cases, so it works where test generation is hard.

**Technique:** rank = α·log P_coder(y|x) + (1−α)·log P_reviewer(x|y),
normalized variant wins.

**Mapping to our harness:** Fallback selection when execution is impossible
or tests can't be generated (e.g., tasks with side effects, no sandbox).
Builders: implement `validity/coder_reviewer.py` as the *no-execution
fallback* selector. Also a tiebreaker: when execution signatures tie
(multiple candidates pass everything), break ties with the reviewer score.

---

## HFT synergies (what the papers didn't try)

The papers treat selection as *post-hoc*: sample everything, then select.
Our doctrine — race redundant paths, fail fast, first-valid-wins, keep the
fast path hot — combines with execution-based selection in ways none of the
papers explored:

1. **Hedged early termination (CodeT × HFT):** Consensus sets can be scored
   *incrementally* as the N×M execution matrix fills. Stop the race the
   moment the leading consensus set is mathematically uncatchable
   (score_gap > remaining_possible) — you don't need the full matrix. This
   is EFFICODE's early-termination idea applied to *selection*, not sampling.

2. **Speculative validity (MBR-EXEC × HFT):** Run the cheap validity tiers
   (compile, smoke tests) *while* strategies are still generating — stream
   partial candidates through the fast-fail tier and abort generation for
   candidates that already failed. Push, don't poll: the executor pushes
   kill signals to the generator.

3. **Winner-led budget reallocation (race.py × selection):** Our existing
   `race.py` logs winners per strategy. Feed selection results back: when a
   strategy's candidates repeatedly lose selection, shrink its budget
   mid-race and reallocate to the leader (multi-armed-bandit over
   strategies). EFFICODE allocates across *problems*; we allocate across
   *strategies within one problem*.

4. **Hot consensus cache:** Execution signatures (output vectors) are
   content-addressable. Cache (program-hash → signature) across races so
   repeated strategies skip re-execution. Latency is a correctness
   criterion: selection must be cheaper than one extra strategy sample.

5. **Differential test synthesis as the fast lane (EnsLLM × HFT):** When the
   top two clusters disagree, generate the single distinguishing input
   FIRST and execute only it — one execution can collapse the race instead
   of running the full suite. First-valid-wins on information, not just
   time.

## Builder recommendations (priority order)

1. **`select()` = MBR-EXEC over execution signatures** (paper 3). The
   primitive everything else plugs into.
2. **Default validity = CodeT dual agreement** (paper 1) when no oracle
   tests exist; oracle tests when they do.
3. **Upgrade to SRank overlap weighting** (paper 2) once the matrix code
   exists — it's cheap math on data you already collect.
4. **Governor: solvability probe + fast-fail tier** (paper 8) before
   scaling K/N. This is what keeps the harness affordable.
5. **Strategy space = {model × prompt × temp-schedule}** (papers 4, 7, 9);
   optimize for *uncorrelated failure modes*, not individual strength.
6. **Log rich execution artifacts now** (paper 5) — the free training set
   for a future LEVER-style learned verifier.
7. **No-execution fallback = Coder-Reviewer** (paper 10).
8. **HFT layer on top of selection** (synergies 1–5) — this is our
   differentiator; none of the papers do it.
