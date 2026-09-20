# code-racer-universal — Harness Architecture

**Team 1 · t1-architect (ember) · 2026-09-20**
**Status: living contract.** Sibling teams (t1-papers, t1-repos, t1-impl-core,
t1-impl-strategies, t1-e2e) iterate this doc as findings land. Reality wins
over any line here.

## 0. What this is

A harness that races N **code-generation strategies** against one task spec
with **REAL acceptance tests**. Strategies run concurrently; each produced
candidate is judged by pytest as it arrives; the **first candidate to pass ALL
tests wins**; slow losers are killed. Winners are logged per-task and mirrored
into the fleet's global winners log so the race optimizer, `--lead-with-winner`,
the resilient router's latency-EMA, and the ranker teams all see the data.

This is the **hedgedChain pattern from the resilient-router track (Track 3,
v3.2) applied to code**: speculative hedging with abort isolation — a loser
that fails tests is *data, not a strike*, exactly like a hedged lane that loses
is not a circuit strike.

## 1. Non-goals

- Not a benchmark suite (HumanEval-style). This is a **live racing harness**.
- Not a new executor. We do not fork `race.py`.
- Not a sandbox research project. Judge isolation is `unshare -n` + `timeout`
  + tmpdir — good enough for LLM-generated candidates on yote, upgrade later.

## 2. Key decisions (with rationale)

### D1 — EXTEND `squawk race` / `race.py`, do not build a new racer

`race.py`'s contract — `{name, cmd[], match?, env?}` strategies as **shell
commands**, ThreadPoolExecutor + `as_completed` arrival ordering, per-attempt
fail-fast timeouts, first-**valid**-wins, JSONL winners log, `--lead-with-winner`
ranking — is exactly the executor we need. Forking would split the fleet's
latency memory across two logs and two optimizers.

What is genuinely new (and what `code_race.py` adds on top):
- **Validity = passes real acceptance tests**, not a stdout regex. `race.py`'s
  `match` cannot express "code is correct."
- **Judge-in-arrival-order**: candidates are judged by pytest the moment they
  arrive; losers are killed. `race.py` has no post-generation judge phase.

`t1-impl-core` imports `race.py`'s primitives (borrow, don't fork):
`from race import run_one, log_winners` — same file the skill ships
(`~/workspace/skills/race/bin/race.py`, mirrored on yote).

### D2 — Candidate strategy interface = shell command (race.py compatible)

Every strategy is a `strategies.json` entry:

```json
{"name": "kimi-k2-cot", "cmd": ["cr-llm", "--model", "kimi-k2",
  "--endpoint", "http://127.0.0.1:25100/v1",
  "--template", "cot", "--task", "tasks/fizzbuzz", "--out", "$CR_OUT"],
 "class": "llm-cloud", "timeout": 180}
```

Contract:
- `cmd` runs with env `CR_OUT=<tmpdir>` (created per strategy attempt).
- The strategy **writes the candidate artifact to `$CR_OUT/candidate`** (file)
  or prints the code to stdout (we capture both; file wins).
- `cr-llm` = LLM wrapper: POSTs `problem.md` + prompt template to an
  OpenAI-compatible endpoint, extracts the fenced code block for the task
  language, writes artifact. Exit 0 + artifact present = "produced."
- `cr-repo` = cloned-GitHub-tool wrapper (t1-repos): runs a repo's codegen
  `generate()` single-shot against the task, writes artifact.
- `class` ∈ `llm-fast | llm-mid | llm-cloud | repo | prompt-exotic` — drives
  ceilings (D4) and router scoring (D7).

Why shell commands: `race.py`, `squawk race`, the squawk race protocol, and
every fleet agent can run them. No Python API lock-in.

### D3 — Judge-in-arrival-order (hedgedChain for code)

```
strategies ──race──▶ candidates ──judge FIFO──▶ first ALL-tests-pass = WINNER
                │                        │
                │                        ▼ fail → data, next candidate
                ▼ timeout/slow → killed (abort, not strike)
```

- Judge = `cr-judge <task-dir> <candidate-file>`: copies task `tests/` +
  candidate into a fresh tmpdir, runs `pytest -q` with its own ceiling.
  Runs under `code-racer/.venv/bin/python -m pytest`
  (venv provisioned 2026-09-20, pytest 9.1.1).
  Returns `valid/invalid` + per-test timings + first-failure excerpt.
- Losers failing tests are **abort-isolated** (router-track rule): they do not
  penalize the strategy's future Elo/EMA — a test failure is information
  about the *candidate*, not the *lane*.
- First **pass** wins the race; all remaining strategy subprocesses are
  SIGKILLed immediately (we use Popen, not `subprocess.run`, so we can kill).
- No pass within the global ceiling → race recorded as `no-winner`
  (still logged; still data).

### D4 — Fail-fast ceilings per strategy class (seconds)

| class | gen ceiling | judge ceiling | notes |
|---|---|---|---|
| `llm-fast` (≤2B local, e.g. `fast` @ :25122) | 60 | 30 | TTFT p50 ~47ms; gen 380–440 tok/s measured |
| `llm-mid` (4–15B, herd/beellama, e.g. qwen-flash, gemma-4-12b) | 120 | 45 | |
| `llm-cloud` (kimi-k2/k3, nemotron, deepseek via herd/NIM) | 180 | 60 | connect ceiling 8s (router rule) |
| `repo` (cloned codegen tools) | 300 | 60 | tools do their own internal loops |
| `prompt-exotic` (self-repair, debate) | 240 | 60 | |
| global race ceiling | 600 | — | wall clock for the whole task |

Ceilings live in `task.yaml` (overridable per task) with these as defaults in
`code_race.py`. The race optimizer's suggested ceilings (from the global log)
can tighten them over time — wire that in Phase 2.

### D5 — Task-spec format

```
tasks/<task-id>/
  task.yaml      # id, lang, artifact name, timeouts, extraction rules
  problem.md     # the ONLY thing strategies see (plus fixtures/)
  tests/         # REAL pytest acceptance tests — hidden from strategies
  fixtures/      # starter code / data the candidate may use
```

`task.yaml`:
```yaml
id: fizzbuzz-01
lang: python
artifact: solution.py          # filename the candidate is tested as
extract: {fence: python}       # which fenced block cr-llm extracts
timeouts: {llm-fast: 60, llm-mid: 120, llm-cloud: 180, repo: 300, judge: 60}
accept: "pytest tests/ -q"     # run by cr-judge inside tmpdir
```

Rules:
- Strategies receive `problem.md` only. `tests/` is never mounted into a
  strategy's environment (judge copies it separately). Public examples live
  in `problem.md` itself.
- Tests must be deterministic, hermetic (no network), and fast (< judge ceiling).

### D6 — Winners ledger: task-specific + global mirror

- **Task ledger** (rich schema):
  `/home/toxic/sovereign/killer-features/code-racer/winners.jsonl`
  ```json
  {"ts": 1726800000.0, "task_id": "fizzbuzz-01", "winner": "kimi-k2-cot",
   "strategies": [{"name": "kimi-k2-cot", "class": "llm-cloud",
     "model": "kimi-k2", "template": "cot", "latency_s": 41.2,
     "produced": true, "passed": true, "judge_s": 1.8},
    {"name": "fast-plain", "class": "llm-fast", "latency_s": 3.1,
     "produced": true, "passed": false, "judge_s": 0.9}],
   "no_winner": false}
  ```
- **Global mirror**: minimal entries appended to
  `~/.cache/shingle/hft_race_winners.jsonl` with `tag: "code-race/<task-id>"`,
  so the race-optimizer daemon, `race.py --lead-with-winner`, and the router's
  latency-EMA see code-race results with zero changes to their code.

Rationale: one schema can't serve both (fleet tooling expects the flat
`{ts, tag, winner, latency}` shape). Two writes, one truth.

### D7 — Papers → scoring (t1-papers contract)

Already-landed papers from the router track (do not re-research):
- **RouteLLM** (2406.18665) → per-task-class routing: the ledger records
  pass-rate per `(model, task-class)`; the router learns which models win
  which task shapes. Latency-EMA candidate scoring (`Elo − EMA/50`) from
  Track 3 applies verbatim.
- **FrugalGPT** (2305.05176) → cascade lane: order strategies cheap-first;
  escalate to expensive models only if cheap candidates fail the judge.
  `code_race.py --cascade` mode implements this (sequential cheap→expensive,
  still judge-gated).
- **Unified routing/cascading** (2410.10347) → the cascade + race hybrid:
  default is full-field race; `--cascade` is the FrugalGPT fallback when
  cost/latency budget is tight.
- **Mixture-of-Schedulers** (2511.11628) → future: schedule strategies across
  yote's GPU/CPU lanes.

New papers t1-papers should pull (code-specific): the `code-race` GitHub
project (race.py's origin — check what their validity/judge looks like),
SWE-bench-style eval harnesses, and whatever the repo search (t1-repos)
surfaces for single-shot codegen tools.

### D8 — Squawk integration: new message type, same fence pattern

- New types `code-race-request` / `code-race-result`, fenced JSON blocks
  (same ` ```json squawk-code-race-request ` pattern as RACE-PROTOCOL.md).
- New CLI: `squawk code-race <channel> --task tasks/<id> [--strategies FILE]
  [--mode race|cascade] [--tag T]` — posts the request; the poster also runs
  it locally via `code_race.py` and posts the result (mirrors `squawk race`
  behavior, including `--request-only`).
- `squawk race-poll` extended to service both `race-request` and
  `code-race-request` from the queue.
- Runner profiles (implementer/researcher) can service code-race requests.

### D9 — Candidate sources (probed LIVE on yote 2026-09-20, do not assume)

| source | endpoint | models (code-relevant) | status |
|---|---|---|---|
| herd llama-swap | `http://127.0.0.1:25100` | 199 models incl. `bigcode/starcoder2-15b`, `deepseek-ai/deepseek-coder-6.7b-instruct`, `google/codegemma-1.1-7b`, `mistralai/codestral-22b-instruct-v0.1`, `ibm/granite-8b-code-instruct`, `meta/codellama-70b`, `kimi-k2`, `kimi-k3-nim`, `beellama/qwen-flash-*`, `gemma-4-12b` | 200, 0.7ms |
| beellama fast | `http://127.0.0.1:25122` | `fast` (exaone-4.0-1.2b, 380–440 tok/s) | 200, 0.3ms |
| toolcall-llm | `http://127.0.0.1:25152` | `qwen3.5-9b-tool` | 200, 0.2ms |
| prompt variants | — | plain / cot / fewshot / role-constrained / self-repair | t1-impl-strategies |
| cloned repos | — | t1-repos adapts codegen tools → `cr-repo` wrapper | t1-repos |

`:25001` is dead (was herd dynamic slot) — do not route there.

### D10 — Herd first-class model (feeds ranker-audit + race-port teams)

`code-racer` becomes a selectable herd model `code-racer/<task-class>` whose
"inference" = race the candidate pool for that task class. The ledger schema
(D6) is the ranker input: per-model pass-rate + latency per task class feeds
the six provider rankers and the race-port selectable model. t1-e2e verifies
the ledger → ranker path.

## 3. Component map (who builds what)

| component | owner | description |
|---|---|---|
| `code_race.py` | t1-impl-core | orchestrator: race strategies (Popen, killable), judge FIFO by arrival, winner kill-switch, ledger writes (task + global mirror) |
| `cr-judge` | t1-impl-core | pytest runner: tmpdir isolation, `unshare -n`, timeout, returns valid/invalid + timings |
| task-spec loader | t1-impl-core | parses `tasks/<id>/task.yaml`, enforces tests/-hidden-from-strategies |
| `cr-llm` | t1-impl-strategies | OpenAI-compatible wrapper: endpoint/model/template → artifact |
| prompt templates | t1-impl-strategies | plain/cot/fewshot/role/self-repair × task |
| strategies.json generator | t1-impl-strategies | task + model pool → race-ready strategies file |
| `cr-repo` + cloned tools | t1-repos | adapt GitHub codegen repos to the strategy contract |
| paper → scoring notes | t1-papers | cascade policy, per-task-class Elo/EMA, scheduler ideas |
| E2E on yote | t1-e2e | sample task → real tasks; ledger → ranker verification |
| `squawk code-race` + race-poll ext | t1-impl-core (with squawk track) | new message types, CLI |

## 4. Hard limits (non-negotiable)

- Never kill squawk processes. `code_race.py` kills **only its own children**
  (track PIDs at spawn; kill by explicit PID, never by name/port).
- Never touch port 443 (tailscaled), never touch the bridge
  (`/home/toxic/sovereign/bridge/awrawr_ws_exec.py`, pitchfork-managed).
- GitHub push from yote is broken (stale auth) — commit locally, never block on push.
- Judge runs untrusted LLM output: `unshare -n` (no network), fresh tmpdir,
  `timeout`, no writes outside tmpdir.

## 5. Phase plan

- **Phase 1 (now):** this doc + sample task fixture (`tasks/fizzbuzz-01/`);
  t1-impl-core builds `code_race.py` + `cr-judge`; t1-impl-strategies builds
  `cr-llm` + 2 prompt templates; t1-e2e races the sample task live.
- **Phase 2:** t1-repos lands first `cr-repo` tool; `--cascade` mode;
  optimizer-driven ceiling tightening; 3+ real tasks (algorithms, parsing, API glue).
- **Phase 3:** `code-racer/<task-class>` as herd selectable model; ledger →
  ranker-audit scoring; Mixture-of-Schedulers lane scheduling.

## 6. Open questions (for fleet)

1. Should a *partial* pass (e.g. 7/10 tests) beat a slower full pass? (Current: no — all-or-nothing. FrugalGPT-style partial credit is Phase 2.)
2. Global ceiling 600s: too generous for the fast lane? Optimizer data will tell.
3. v3 HMAC canonical form for code-race messages — wait for the fleet-wide
   verifier rollout (relay-hmac track's finding).

---
*Contract version: v1 · 2026-09-20 · t1-architect (ember). Iterate in the open.*
