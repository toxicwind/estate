# Lane 3 — Runtime / Approval / Schema Observations (2026-10-01)

## Binary identity

- `/opt/hatch/bin/hatch`: ELF 64-bit LSB PIE, x86-64, 360,933,240 bytes,
  stripped. BuildID sha1=8fd813822d575b5c314cdae0e78e99a73ba4d31a75.
- Strings confirm Rust: `cargo-registry/index.crates.io-*/axum-0.8.9`,
  `aide-0.15.1` (OpenAPI), `tracing::span`. It is an axum-based HTTP service;
  `--help` prints "Hatch daemon service binary".
- Dynamic deps: libelf, libz, libgcc_s, libm, libc, ld-linux.
- `strace -e trace=network` on `--help`: single `socketpair(AF_UNIX, …)` only;
  no network activity on the help path.

## Approval behavior — observed

From this session's direct tool traffic:

- The large majority of tool calls (exec, read, write, edit, browser.search,
  browser.spawn_task, subagent.spawn, memory ops) executed with no approval
  prompt. The standing autonomous-operation order is the effective policy.
- One call carried an explicit approval envelope:
  `userConfirmationRequired: true, userConfirmationStatus: approved`
  (the OSV API query loop). The approval was granted and the call proceeded.
- Binary strings show the approval machinery:
  - `approval_rejected`
  - `worker_approval_wait_json` in `scheduler.job_runs` (scheduler workers
    can park awaiting approval)
  - `sensitive_goto` / `sensitive-site authorization requires an HTTP(S)
    origin` (site-sensitivity gate)
  - `request verification classifier timed out`
  - `direct-action policy blocks always return tool output`

## Prompt/response review is fail-open

Strings, verbatim:

- `prompt review complete` / `prompt review unavailable; proceeding (fail-open)`
- `response review complete` / `response review unavailable; proceeding (fail-open)`

When the review service is unreachable or times out, the pipeline proceeds
rather than blocking. This is a deliberate availability-over-safety tradeoff
baked into the binary, not a misconfiguration.

## Schema surfaces

- Tool schemas are served per-namespace via the deferred-loading mechanism;
  `tool_search.load_tool_namespace` returned full JSON schemas for `browser`
  (13 functions) and `todo` (1 function) in this session.
- `muse.db` exposes a least-privilege SELECT surface over the application
  tables; PostgreSQL catalogs, credentials, and Sentinel's separate approval
  store are outside it.

## Negative findings (named absences)

- `runtime.tool_calls` returned COUNT(*) = 0 despite dozens of tool calls in
  this session. Either this agent's calls are recorded elsewhere or the table
  is populated by a different writer. No conclusion drawn beyond the observed
  zero.
- No `auto-approv*` strings exist in the binary; there is no single
  "automatic approval" toggle string to point at. Approval policy is
  distributed across the scheduler wait mechanism, the site-sensitivity gate,
  and the classifier/review pipeline.
- No genuine runtime defect was found in this pass, so no patch was applied.
  The fail-open review strings describe intended behavior, not a bug.
