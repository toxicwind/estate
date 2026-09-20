# herd CI fix — progress log (worker b38843ae)

## Diagnosis (2026-09-14)
All three red workflows were failing ONLY because of the account Actions budget gate:
annotation on failed runs: "The job was not started because an Actions budget is preventing further use."
No code defect in closeinactive.yml or containers.yml. unified-docker.yml had one real
code bug (hardcoded ghcr.io/mostlygeek/llama-swap namespace -> 403 on fork),
already fixed by predecessor commit 3c298f3e.

## Actions
- closeinactive.yml: added `workflow_dispatch` (commit f32fc0c8) -> manual run 34830624827 GREEN
- containers.yml: no code change -> manual run 34830630820 (dryrun=true) GREEN, all 7 platforms
- unified-docker.yml: manual run 34829809312 in progress; vulkan build FAILED in
  "Build unified Docker image (vulkan)" step -> investigating docker/unified/build-image.sh
- deleted throwaway ci-probe branch (undispatchable from non-default branch; diagnosis
  came from web-UI annotations instead)

## Pre-existing red, NOT my mandate (push events, 2026-09-03, untouched by me)
- Windows CI, Linux CI, UI Tests: last runs failed on push 2026-09-03

## unified-docker vulkan failure (run 34829809312)
- build (vulkan) FAILED after 18m39s in "Build unified Docker image (vulkan)" step.
- Upstream control: mostlygeek/llama-swap unified-docker GREEN on 09-12/09-13/09-14.
- Fork's docker/unified/ is a STALE snapshot of upstream's OLD monolithic build
  (single Dockerfile + build-image.sh); upstream rewrote it into staged Dockerfiles
  (base-*.Dockerfile, llama.Dockerfile, ...). README/install scripts also diverged.
- Hypotheses: (a) OOM — old system compiles whisper+sd+llama.cpp concurrently on a
  4-core/16GB runner; (b) compile breakage with current llama.cpp/whisper/sd master.
- build (cuda) still running; its outcome disambiguates (cuda fail => systemic,
  cuda pass => vulkan-specific). Logs downloadable once run completes.
- Retry plan: re-dispatch with inputs build_cuda=false, build_vulkan=true (vulkan-only).

## Out-of-mandate note (for parent report)
- Windows CI / Linux CI / UI Tests last failed 2026-09-03 with 0 steps executed —
  budget-gate signature, NOT real test failures. Untouched per mandate, but they
  will likely go green on re-run now that the gate is lifted.
- Tectonic Drift Detection workflow ran GREEN today (34829314490) — someone else's work.
- Spawned child worker (9c663c5b) to build nightly workflow-health/budget-gate
  monitor on branch ci/workflow-health-monitor (commit-maximally baked in).

## Upstream comparison (no logs yet — cuda still building)
- Upstream's current install-llama.sh cmake flags for vulkan are IDENTICAL to the
  fork's (-DGGML_CUDA=OFF -DGGML_VULKAN=ON); only TARGETS differ (upstream adds
  llama-bench). So the llama.cpp compile itself should behave the same.
- Upstream rewrite (e31a1ade, #1071, 2026-08-30) was for SPEED (6+hr -> 1.5hr),
  not breakage; it also isolates each project build onto its own runner.
- Fork still builds whisper+sd+llama concurrently in ONE job, each with -j$(nproc)
  => up to 12 heavy compile processes on a 4-core/16GB runner. OOM-kill remains a
  prime suspect for the 18m39s vulkan failure.
- Fork MISSED upstream 1f3c68ed (rocm-smi for vulkan backend, 2026-08-01) — runtime
  concern, not build. Also missed audio.cpp/vllm-wrapper/cuda13 additions.
- Awaiting run completion for the actual build log (ground truth).

## Smoking gun for resource hypothesis (upstream's own words)
Upstream unified-docker.yml header: "Building everything in one job put five
concurrent CUDA compiles on a four-core runner, which stopped fitting in the 6h
job limit; a cancelled job also never reached --cache-to, so nothing was cached
and every later run rebuilt from scratch."
- Fork still runs the monolithic build: whisper+sd+llama compile CONCURRENTLY in
  one job, each with -j$(nproc) => ~12 heavy g++ processes on 4c/16GB runner.
- Upstream vulkan green TODAY 05:44 UTC with identical flags/packages/masters =>
  not a "master is broken" issue. Fork failure at ~10:06 UTC same day =>
  resource exhaustion (OOM) or transient is most likely.
- IMPORTANT: failed runs never reach --cache-to, so retries rebuild from scratch.
- Candidate fix (after logs confirm): serialize stage builds in build-image.sh
  via sequential `docker buildx build --target <stage>` invocations before the
  final build, so only one heavy compile runs at a time. Alternative: port
  upstream's split build system (much bigger change).
- DO NOT blind-retry yet: if OOM, it will fail the same way and burn budget.

## Child worker done: workflow-health monitor (2026-09-14 ~10:19 UTC)
- Branch `ci/workflow-health-monitor` (from main f32fc0c8), commit 55bb4f44, NOT merged.
- `.github/workflows/workflow-health.yml` (daily 06:23 UTC + dispatch): classifies
  last 10 runs of 6 key workflows as BUDGET_GATE / REAL_FAILURE / UNKNOWN via
  stdlib Python; writes job summary; maintains single tracking issue, updated only
  on classification change; exits non-zero only on REAL_FAILURE.
- `docs/ci-health.md` triage guide.
- Budget annotation verbatim: "The job was not started because recent account
  payments have failed or your spending limit needs to be increased…"
- Validation: YAML parses, 6/6 self-tests pass, live read-only rehearsal classifies
  current failures as BUDGET_GATE. Issue flow + scheduled run not yet exercised.
- Child's local commits in ~/workspace/herd-ci-health/ (3 commits).
- REVIEW + MERGE DECISION still needed (by parent/Chris).
