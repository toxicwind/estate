# Sweep Work Items — collected 2026-09-20 (tmp-sweeper)

Deduplicated, actionable work items from every previous sweep found in /tmp on
yote and collected into their owning repos. One section per sweep: what it
measured, what's still actionable (concrete next step), what's retired and why.
Feeds the super-ralph emergent implementation pass.

Artifact map (relocated this pass, nothing real left in /tmp):
- `projects/openrouter-probe/resurrect-probe.py`, `resurrect-results.jsonl` (gitignored raw), `resurrect-probe.log` (gitignored), `rewire_peer_v3.py`, `e2e-probe.py`, `guidellm/e2e-probe.json` (gitignored)
- `projects/provider-fuzz/nim_probes_results.json`
- `nvidia-alive/k3-probe-20260920.pcap`, `nvidia-alive/bench/bench-all-20260920-1500.log`, `nvidia-alive/bench/bench-all.log`, `nvidia-alive/bench/bench-all2.log`, `nvidia-alive/full-sweep.pre-patch3b`, `nvidia-alive/full-sweep-resume.log`, `nvidia-alive/full-sweep-resume2.log`
- `scratch/astmine-20260920/` (ast_mine.py, ast_rule.yaml, json/*.json — 9 files)
- Kept in /tmp (other lanes / ambiguous, do not sweep): `mcpv/`, `mcpu/` (mcpproxy-go fork work, staged uncommitted changes in mcpv), `kimi-auto.patch`, `kimi-alias-block.yaml`, `oracle-kimi.log`, `oracle-kimi2.log`, `kimi3-direct-raw.log` (kimi unlock lane), `accept_tok`, `bench-all3.log` (live writer at sweep time), today's 171 one-shot .py, `bw-*` toolkit, `cr-*`/`e2e-*` run dirs.

---

## 1. or-free sweep lineage (OPENROUTER :free reliability)

**What it measured.** Three generations of live probes against the herd
(`:25100`) with the exact-output sentinel `ABSTRACT-7X3Q`:
- `probe_all.py` / `probe_abstract.py` — 446-model availability sweep (v1/v2).
- `probe_reliability.py` (v3) — 3 passes x 446 models, 10 workers, no pacing.
  Error classes: 402-not-entitled 1038, 404-dead-id 234, 429-throttled 14,
  200-empty 12, 403-refused 6, 529 x1. Only 10 IDs ever returned the token.
  Ranking (exact_rate desc, p50 asc): cohere/north-mini-code:free 3/3 557ms,
  nex-n2.5-pro:free 3/3 583ms, nex-n2.5-mini:free 3/3 609ms,
  ling-3.0-flash-sante:free 3/3 941ms, nemotron-3-super-120b 3/3 1349ms,
  nemotron-3-ultra-550b 3/3 6088ms (wild variance), nano-omni-reasoning 2/3,
  laguna-s-2.1 2/3, openrouter/free 1/3, nemotron-3.5-lightning 0/3 (chatty).
- `reverify_top8.py` — no-pacing re-verification. nex-n2.5-mini:free exact at
  489ms (fastest exact); nex-n2.5-pro:free 799ms; laguna-s-2.1 2161ms;
  nemotron-3-super returned `ABSTRACT-` (truncated — needs max_tokens headroom);
  nemotron-3.5-lightning dumped thinking process; cohere + ling-3.0-flash-sante
  returned 200-empty this run (cohere's 332ms too fast for a reasoning model —
  likely filtered, not truncated); nano-omni errored on `choices` key.
- Outputs: `reliability-20260920-144532.{json,jsonl}`, `reverify-20260920.jsonl`,
  `RANKING.md` (retracts the old "abuse detection" 402-storm claim — 402 is
  entitlement). `rewire_peer_v3.py` spliced the v3 order into
  `config/herd.yaml` openrouter-free peer (idempotency-guarded, line-range
  splice; already applied).

**Still actionable.**
1. Run the GuideLLM composite eval per `projects/openrouter-probe/GUIDELLM_EVAL_PLAN.md`
   section 4 — `guidellm/e2e-probe.json` (nex-n2.5-mini, this pass) is the first
   data point; repeat for the other 7 re-verified models, outputs to
   `projects/openrouter-probe/guidellm/*.json` (gitignored by convention).
2. Build the thinking-strip adapter for reasoning models
   (nemotron-3.5-lightning, nemotron-3-nano-omni-30b-a3b-reasoning wrap answers
   in thinking blocks) — required before their GuideLLM scores mean anything.
   Open item in GUIDELLM_EVAL_PLAN.md section 5.
3. Migrate `probe_all.py`, `deep_pass.py`, `guidellm_sweep.sh` from
   `OPENROUTER_API_KEY_1` to `OPENROUTER_API_KEY_FREE` (open item, plan sec 5).
4. Re-run `probe_reliability.py` after any OpenRouter key rotation or 402-storm;
   feed fresh ranking into RANKING.md and re-run `rewire_peer_v3.py` if order
   changes. Reasoning models need generous `max_tokens` in probes (50 truncated
   cohere mid-thought; 300 clean).

**Retired.** `v3.py`, `orfree.py`, `orfree2.py` (one-shot snippets, superseded by
`probe_reliability.py`); `live-orfree.txt` (superseded by RANKING.md);
`/tmp/tokenizer-map.json` (partial copy; canonical at
`nvidia-alive/bench/tokenizer-map.json`); `herd.yaml.bak-v3`,
`herd.yaml.bak-moonshot-comment`, `herd-keypool.py.bak-sweep-fix` (backups; live
files already carry the changes).

---

## 2. Resurrect 78 dead models (dead-model-resurrector)

**What it measured.** `projects/openrouter-probe/resurrect-probe.py` tested the
hypothesis "strip `:batch`, probe base IDs live" against 78 dead-suffixed model
IDs (16 workers, free key). Raw results:
`projects/openrouter-probe/resurrect-results.jsonl` (gitignored). Probe-run
classification: 73 x `paid` (402 — ID exists, not free-entitled), 5 x `dead`
(404: meta/muse-spark-1.3-contributor, meta/muse-spark-1.2-contributor,
sakana/sakana-namazu, openai/gpt-5.2-chat, mistralai/mistral-large-2512).
Commit `06e2cd6c` ("Maximal: resurrect 78 dead models - 77 LIVE, 1 TRULY-DEAD")
landed RESURRECTED blocks in `config/herd.yaml` (lines ~881-906, in main).

**Still actionable.**
1. Reconcile the 5 `cls=dead` probe classifications against the herd.yaml
   RESURRECTED blocks — confirm which single ID is TRULY-DEAD and drop it from
   any peer list that still references it.
2. Re-run `resurrect-probe.py` after the next OpenRouter key rotation; 402 vs
   404 boundaries move when entitlements change.

**Retired.** `resurrect-probe.py.b64` (transfer artifact). `/tmp/sov-eval` and
`/tmp/sovereign-resurrect` clones (5.9G + 1.4G) — all commits verified merged
into canonical main, deleted.

---

## 3. NIM provider-truth probes (provider-fuzz)

**What it measured.** Papers-first, then live probes. Thesis (Chris, validated):
providers LIE — `/v1/models` advertises models that 404/402/empty-200/hang on
invocation; only a real completion with content is truth.
`projects/provider-fuzz/nim_probes.py`, `probe_truth.py`, `nvcf_classifier.py`,
`NIM-PROBE-REPORT.md`, `TRUTH.md`, `nvcf_functions_20260920.json`,
`nim_probes_results.json` (this pass). Headline findings:
- moonshotai/kimi-k3 on NIM is **CAPACITY-STARVED** (new classifier state,
  wired into `probe()` -> verdict `LYING` with operator-truth reframe):
  sync chat/completions + `NVCF-POLL-SECONDS: 30/60` -> HTTP 504 in 32s/62s;
  per NVIDIA docs 504 = no worker picked up the request; control plane accepted
  (issued `nvcf-reqid`) so the function exists and the key is entitled.
- kimi-k2.6 -> 404 account-scoped enablement failure (matches NVIDIA forum
  #379257, same function ID). Only `NVIDIA_API_KEY` authenticates
  (`NIM_API_KEY`, `NVIDIA_NIM_API_KEY`, `_1` all 401).
- `probe_nvcf_functions()` (`probe_truth.py nvcf-functions`): 202 functions,
  111 ACTIVE, incl. 5 ACTIVE kimi-k3 functions on this account.
- `NVCF-AI-Resource` header is a NO-OP (no official spec; same 404 either way).
- Re-fuzz with `max_tokens=100` found 5 MORE live OpenRouter models than the
  `max_tokens=5` sweep (reasoning models emit to `reasoning` field first).

**Still actionable.**
1. Wire `CAPACITY_STARVED` into herd peer selection: capacity-starved routes
   should back off with a cooldown in `herd-keypool.py` instead of hard-fail —
   the pipe is open, nobody's home *right now*.
2. Re-run `probe_truth.py` after any NVIDIA key rotation (auth surface is
   `NVIDIA_API_KEY`-only; the 401s on the other vars are standing).
3. kimi-k3 async re-probe with longer `NVCF-POLL-SECONDS` windows to catch
   capacity appearing; `nvcf-poll-probe.py` and `k3-probe-20260920.pcap`
   (in `nvidia-alive/`) are the instruments.

**Retired.** `/tmp/nim_probes.py` (older than repo's 08:43 version),
`nim_probes.b64`, `nimxfer.tgz`, `nimxfer2.tgz`, `probe_truth_addition.py`,
`apply_truth.py` (additions landed in repo), `nimprobe.idx` (cache).

---

## 4. Nemotron / nvidia-alive bench sweep

**What it measured.** `nvidia-alive/` lane: `full-sweep.py` (+`dedupe-sweep.py`,
resume logic), `prober.py`, `k3-runner.sh`, kimi provider audit scripts,
GuideLLM bench runs against nemotron-3 models. This pass relocated:
`k3-probe-20260920.pcap` (root-owned capture of kimi-k3 probe traffic),
`bench-all-20260920-1500.log` + `bench-all.log` + `bench-all2.log` (GuideLLM run
logs), `full-sweep.pre-patch3b` + `full-sweep-resume.log` +
`full-sweep-resume2.log` (sweep state). Tokenizer lane:
`scripts/prefetch-tokenizers.py` (warms HF cache) + `scripts/gen-tokenizer-map.py`
-> `bench/tokenizer-manifest.json` (12/12 verified) + `bench/tokenizer-map.json`.

**Still actionable.**
1. Analyze `nvidia-alive/k3-probe-20260920.pcap` with `nvidia-alive/pcap-analyze.py`
   — extract kimi-k3 timing/capacity evidence to corroborate the
   CAPACITY-STARVED verdict with packet-level data.
2. Re-run `scripts/prefetch-tokenizers.py` whenever new bench models are added;
   keep `bench/tokenizer-manifest.json` at 12/12.
3. `full-sweep.py` resume state is staged — a full provider sweep can resume
   from `full-sweep-resume*.log` rather than starting cold.

**Retired.** `discover-tokenizers.py` (earlier iteration; superseded by
prefetch + gen-tokenizer-map); `/tmp` bench logs (relocated).

---

## 5. GuideLLM composite eval (openrouter-probe)

**What it measured.** `GUIDELLM_EVAL_PLAN.md` (2026-09-20): standing order is
ranking runs THROUGH the GuideLLM fork (`projects/guidellm`,
toxicwind/guidellm), no parallel harness. Two-layer design: probe_abstract.py
(exact-output correctness) is KEPT, GuideLLM adds latency distributions
(TTFT/ITL/end-to-end, token counts, success/failure). `e2e-probe.py` runs one
model through the full GuideLLM scorer path; `guidellm/e2e-probe.json` is the
first completed eval (nex-agi/nex-n2.5-mini:free on openrouter.ai).

**Still actionable.** See sweep 1 items 1-2 (run remaining 7 models, build
thinking-strip adapter). Fork (`toxicwind/guidellm`) is currently uncustomized
upstream @ 4601968 — future customization (tool use, reasoning retention,
context behavior) goes IN the fork, not a new harness.

**Retired.** Nothing — this sweep is just starting.

---

## 6. Census work

**Status.** No census artifacts were found in /tmp. Census is the census
coordinator's lane (`config/herd.yaml` peer blocks — off-limits to this sweep).
The census LLM-judge ranking fed the herd reconcile (commit `c7c63ee781`,
in canonical main). No work items for super-ralph from this lane.

## 7. Paper-search

**Status.** No paper-search outputs were found in /tmp. The paper-search
promotion was pushed to `toxicwind/sovereign-projects/main` (remote main
`9a8ba6c5b7`, 2026-09-20). No work items for super-ralph from this lane.

## 8. Skill-inventory / AST-mine sweep

**What it measured.** `ast_mine.py` + `ast_rule.yaml` mined checkouts for
model IDs, account refs, client calls, host refs, retry/backoff patterns
(`scratch/astmine-20260920/json/*.json`, 9 files; e.g. `model_maps.json` maps
files to model IDs found in them, including pi-nvidia-nim test fixtures).

**Still actionable.**
1. Cross-check `model_maps.json` against the provider truth table
   (`projects/provider-fuzz/TRUTH.md`) — any mined ID not in the truth table
   is a probe candidate.
2. `client_calls.json` -> audit which clients hardcode model IDs; those are
   migration targets for herd-routed calls.

**Retired.** `all-skills.txt`, `all_ignored.txt`, `sweep_status*.txt`,
`full-sweep-resume*.log` (/tmp copies; the astmine data itself is kept in
`scratch/astmine-20260920/`).

## 9. Kimi probes (other lane — not swept)

`kimi-auto.patch`, `kimi-alias-block.yaml`, `oracle-kimi.log`,
`oracle-kimi2.log`, `kimi3-direct-raw.log` remain in /tmp untouched — they
belong to the kimi unlock lane (`/home/toxic/kimi-auto`, off-limits).
Super-ralph should not pick these up without the kimi lane owner.
