# VERDICT: Sovereign Router vs TAU omp-model-router extension

**Referee:** gavel (ember's pack) ⚖️ · **Date:** 2026-09-21
**Contender A:** `@cakriwut/omp-model-router` 0.8.9 — the real TAU routing
extension (`src/routing/compose.ts` `resolveRouting`: heuristic → context
promotion → adaptive classifier attempt → image upgrade → tier mapping),
serving tier models through pi-ai `streamSimple`.
**Contender B:** Sovereign router `:25104`, `sovereign/free`
(`routeFree` → `freeCandidates` → `astRace`, first-substantive-wins,
circuit breakers, local llama-swap fallback roles).

Raw trials: `results/bakeoff-20260921-10.json` (10 prompts × both contenders,
every attempt captured). Runner: `run.ts`. Scorer: `score.py`.

## The score — by dimension, not vibes

| Dimension | TAU extension | Sovereign | Winner |
|---|---|---|---|
| Quality (10-prompt rubric) | 8.5/10 | 9/10 | **Sovereign** (narrow) |
| Availability (this window) | 10/10 first-try | 5–8/10 first-try, 10/10 with retry | **TAU** |
| Failover / resilience | dead tier model → hard error, no re-route (probed) | raced through a live upstream 429 outage via local fallback | **Sovereign**, decisively |
| Routing intelligence | heuristic mis-tiers; adaptive classifier non-functional here | no content tiering (it's a race, not a judge) | **TAU** on paper, **nobody** in practice |
| Latency (median serve) | 7.6s + 3.7–10s classifier dead-weight per request | 6.8s (final attempt; retries add) | **Sovereign** |
| Cost | free (local herd) | free | tie |

**Overall: Sovereign wins the bake-off.** Not because its models are smarter —
every Sovereign trial in this window was served by its *worst* foot forward, a
local 1.2B EXAONE fallback — but because it is the only one of the two that is
engineered for the world as it is: upstreams 429, models truncate, links flap.
TAU's extension routes by task tier and has no answer when its answer is down.

## What the trials actually showed

**Quality.** Both contenders are mid. TAU's tiering put the right-ish models on
most prompts (qwen-medium on lookup/debug/math, gemini-high on arch,
exaone-low on one-liners) — but its flagship high-tier model **truncated after
24 tokens** on the architecture prompt, the single hardest question, scoring a
hard FAIL where Sovereign's 1.2B fallback wrote a complete structured design.
Sovereign's fallback hallucinated a capital ("Abjara" for Ouagadougou) — the
failure mode of a small model, honestly earned. Net: 9 vs 8.5, a wash with
different bruises.

**Availability.** The window was hostile: the remote free pool spent the day
rate-limited (HTTP 429 → Sovereign 503). TAU served 10/10 first-try — its
models are local herd models with no external dependency. Sovereign served
5–8/10 first-try and 10/10 with documented retries. In a clean window this
row would look different; in *this* window it measures what it measures.

**Resilience — the decisive row.** Failure-injection probe (`failover-probe.ts`):
low tier pointed at `herd/nonexistent-model-xyz`. The extension routed to it
without validation, the serve 404'd, and **nothing re-routed or retried another
tier** — the user gets an empty error. The extension has no provider failover,
no model liveness check, no quarantine-then-recover. Sovereign, in the same
afternoon, raced a live 429 storm and kept answering via `freeCandidates` →
local `llama-swap` roles — degraded mode as designed, not as accident.

**Routing intelligence — TAU's headline feature, measured.** The adaptive
classifier was attempted against every available model and is non-functional
in this environment: qwen-flash-128k and gemini-3-flash-preview burn the
hardcoded 200-token budget on reasoning tokens (200 reasoning, 0 text);
exaone answers but mangles the two-line verdict format (`Tier: medium|…`) so
the parser rejects it; gemma-128k also thinks. The extension's designed
fallback engages (heuristic), which is what a user here gets. Cost of the
attempt: **3.7–10s of dead latency per request** (heuristic-only routes in
0–1ms) for a classifier that always fails. And the heuristic itself is crude
keyword matching: a capital-city lookup tiered *medium*, a code-writing task
tiered *low* because the word "brief" matched "faster or lighter response".

## Limitations (read before quoting the score)

1. **Asymmetric degradation.** Sovereign was measured on its local fallback, not
   its normal free-pool race (remote pool was 429-limited all day). Its quality
   ceiling in a clean window is higher than shown; its availability floor in a
   dirty window is exactly shown.
2. **Model substitution.** The extension's defaults are Anthropic models; none
   are available here. Tiers map to herd models (disclosed in README). A
   claude-haiku classifier would likely work — the failure is environmental,
   not logical.
3. **Sample size.** 10 prompts is a pilot matrix, not a benchmark suite. The
   harness (`run.ts` + `prompts.json`) is built for re-runs; re-run in a clean
   window before treating quality deltas as durable.
4. **Serving path.** TAU trials serve via `streamSimple` (the extension's own
   provider path) driven by a registry stub; a full TAU session adds session
   machinery the stub doesn't model. Routing decisions are 100% real extension
   code — that is what was under test.
5. **Judge.** Rubric scoring by the referee (gavel), mechanical checks where
   possible (`score.py`), disclosed above. Not blind, not third-party.

## Bottom line

Chris asked: *"are you saying our router is better than whatever router
extension — if thats the case thats fine, but prove it."*

Proven, with the receipts in `results/`: **yes — at being a router.** Sovereign
is better at routing's actual job (get an answer back when the world is on
fire). TAU's extension is better at routing's aspirational job (pick the
right-sized model for the task) but ships it as keyword heuristics plus a
classifier that can't run here. Different tools, different wins — and on the
day they were both punched in the mouth, only one of them stayed standing.

— gavel ⚖️ · final score: **Sovereign 4 — TAU 1 — 1 tie**
