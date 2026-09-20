# NIM Live-Probe Report — 2026-09-20

**Crew:** nim-prober (Ember) · **Method:** papers-first, then live probes on yote
**Sources hunted before probing:** nvidia/nvcf v0.6.0 generic-HTTP-invocation docs,
nvidia/nvcf API docs, NVIDIA Cloud Functions lifecycle docs, nvidia/garak NVCF
generator docs, backblaze-labs/genblaze NVIDIA connector, nirholas/three.ws
nvidia-models.md, lucky-mandator/gocode-router.

## Headline: moonshotai/kimi-k3 is CAPACITY-STARVED (not dead, not async)

| Probe | Result |
|---|---|
| sync chat/completions + `NVCF-POLL-SECONDS: 30` | **HTTP 504 in 32,149ms** |
| sync chat/completions + `NVCF-POLL-SECONDS: 60` | **HTTP 504 in 62,126ms**, headers `nvcf-reqid: 15bd295f-…`, `nvcf-status: errored` |

Per NVIDIA's own docs, 504 = "no worker picked up the request within the
polling timeout window." The control plane **accepted** the request (issued an
NVCF-REQID) — so the function exists and the key is entitled. No 202 was ever
returned, so the async hypothesis is out. No 404, so the death hypothesis is
out. **Verdict: the function exists; zero serving capacity is allocated behind
this route right now.** The pipe is open, nobody's home.

New classifier state landed: `CAPACITY_STARVED` (nvcf_classifier.py), wired
into `probe()` → verdict `LYING` with operator-truth reframe.

## All six WTF.md priorities

1. **NVCF function-list probe** — DONE, in owned code. `probe_nvcf_functions()`
   added to `probe_truth.py` (+ CLI `probe_truth.py nvcf-functions`).
   Live: **202 functions, 111 ACTIVE**, incl. 5 ACTIVE kimi-k3 functions on this
   account (`ai-kimi-k3` 1586112a-…, plus 4 dynamo kimi-k3 variants). The WTF
   hypothesis is confirmed with a correction: the endpoint lists
   account-associated functions (scope: `list_functions`), which is the honest
   entitlement surface but not a proof of per-model invocation rights.
   Full snapshot: `nvcf_functions_20260920.json`.
2. **kimi-k3 async re-probe** — DONE (headline above). Neither dead nor
   async-alive: **capacity-starved**.
3. **`NVCF-AI-Resource` header** — DONE. **NO-OP**, exactly as the papers
   predicted (no official spec exists; the only prior art passes it as a
   generic custom header). Same 404, same behavior either way.
4. **UUID ghost-ID guard** — DONE. `guard_uuid()` / `guard_model_route()` in
   nvcf_classifier.py. All 3 registry UUIDs blocked; fresh-UUID negative
   control passes. Call before any route insertion.
5. **NemoClaw shell-ERE twin** — DONE, borrowed verbatim (Apache-2.0):
   `Function[[:blank:]]+'[^']+':[[:blank:]]*Not found for account` with real
   `grep -qiE` parity + JS-regex twin + marker
   `nemoclaw-probe:nvcf-function-not-found`. Tested against all 3 canonical
   404 bodies (shell and JS agree); 200-body negative control clean.
6. **401/403 → AUTH_FAILURE** — DONE, **live-verified**: bad key on a live
   model → 403 `{"detail":"Authorization failed"}`; missing key → 401.
   Both classify `AUTH_FAILURE`. (Note: the first attempt used
   meta/llama-3.1-8b-instruct, which returned 410 — that model reached EOL
   2026-08-26. Probe now uses live `nvidia/llama-3.1-nemotron-70b-instruct`.)

## Files changed (backups: `.bak-nimprobe-20260920`)

- `nvcf_classifier.py` — NemoClaw borrow (JS regex + POSIX ERE + marker +
  `classify_shell_ere`), `guard_uuid`/`guard_model_route`, new
  `CAPACITY_STARVED` 504 branch.
- `probe_truth.py` — `probe_nvcf_functions()` + `nvcf-functions` CLI +
  504 verdict wiring in `probe()`.
- `nim_probes.py` (new) — the six paper-informed probes, re-runnable.
- `nvcf_functions_20260920.json` (new) — full 202-function entitlement snapshot.

## Follow-ups for Chris

- kimi-k3 route is unusable until NVIDIA allocates workers; the `ai-kimi-k3`
  NVCF function (1586112a-…) is ACTIVE on the account — direct pexec
  invocation is unexplored (input schema unknown).
- `NVCF-AI-Resource` is confirmed cargo-cult; strip it anywhere it appears.
- No credential material was printed or persisted at any point.
