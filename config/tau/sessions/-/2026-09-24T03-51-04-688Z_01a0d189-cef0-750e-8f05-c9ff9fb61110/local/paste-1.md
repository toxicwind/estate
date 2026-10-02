# TASK: Ranch Consolidation — Merge, Vendor, Relocate, Verify

## CONTRACT (read before acting)
- You MAY NOT call `goal({op:"complete"})` or emit "TASK COMPLETE", "RESOLVED",
  "SIGNED OFF", or equivalents. Completion is declared by the user, not by you.
- You MAY NOT claim a merge, rename, or move happened without quoting:
  (a) the exact command run, (b) its exit code, (c) a verification command that
  reads the result back (ls, read, git rev-parse, stat).
- You MAY NOT create symlinks. Every relocation is a physical copy or move.
  If you are tempted to symlink, stop and write "SYMLINK REFUSED — needs physical
  placement decision" instead.
- You MAY NOT invent directory structures. Only report paths that exist after
  `ls`, `ffs find`, or `read` confirms them.
- You MAY NOT claim "build: pass", "health: OK", "tests green" without quoting
  the exact command and its exit code.
- You MAY NOT guess what `corral` is. Mark it UNKNOWN and list the probes that
  would resolve it. Do not assign it a repo, a role, or a vendored path.
- Every destructive operation (move, delete, force-push, config overwrite) MUST
  have a rollback line quoted BEFORE it runs.
- Use `ffs find`, `ffs glob`, `read`, `rg`. Never `head`, `tail`, or truncation
  pipes. If a command would exceed output limits, use `read` with line ranges.
- If a step is UNKNOWN after honest investigation, write "UNKNOWN — needs X".
  Do not paper over unknowns with prose that sounds like resolution.

## DELEGATION
- Phases marked ∥ run in parallel via subagents.
- Each subagent returns ONLY: commands run, exit codes, verbatim evidence,
  one-line verdict. No prose summaries, no recommendations.
- Only the orchestrator closes a phase, and only with evidence attached.
- If a subagent's evidence is missing or unverifiable, the orchestrator either
  re-runs the phase itself or marks it FAILED. Never "resolved".
- The orchestrator MUST NOT accept a subagent's claim that a file exists, a
  merge happened, or a build passed without the subagent quoting the read-back.

---

## PHASE 0 — Reality Inventory (orchestrator, no subagent)
Goal: establish what actually exists before proposing any consolidation.
The prior log contains many claims about repo structure. Treat every claim as
unverified until a command proves it.

Steps:
1. `ls -la ~/sovereign/projects/range/` — quote full output.
2. `ls -la ~/sovereign/projects/range/ranch/` if it exists — quote.
3. For each of these candidate paths, run `ls -la <path>` and quote the result
   or quote the "No such file or directory" error:
   - projects/range/herd
   - projects/range/ranch/herd
   - projects/range/sovereign-swap
   - projects/range/flock
   - projects/range/router
   - projects/range/router-legacy
   - projects/range/sovereign-router
   - projects/range/stockyard-flock-router
   - projects/range/barn
   - projects/range/barn/shep
   - projects/range/barn/secretsmith
   - projects/range/barn/browserless
   - projects/range/barn/gemini-mcp
   - projects/range/web
   - projects/range/ranch/web
4. `ls -la ~/.tau/` — quote. Then `read ~/.tau/config.yml` if it exists.
5. Run `git -C <each existing repo> rev-parse HEAD` and quote each SHA.
6. `rg -n "symlink|ln -s" ~/sovereign/projects/range/ 2>/dev/null` — quote
   every hit. These are the symlinks that must be removed.

Deliverable: a table with columns [path, exists?, git SHA, notes].
Do NOT propose any merge or move until this table is complete.

Gate: No Phase 1+ work runs until the inventory table is filled in with
verified paths only. Any path marked UNKNOWN stays UNKNOWN until probed.

---

## PHASE 1 — Claim Audit (subagents `repo-verifier` ∥ `config-verifier` ∥ `symlink-hunter`)
Goal: separate what the log *claimed* from what is *true*.

`repo-verifier` (for each repo that exists per Phase 0):
1. `git -C <path> rev-parse HEAD` — quote SHA.
2. `git -C <path> status --porcelain` — quote. Uncommitted changes are a
   blocker for any merge.
3. `git -C <path> remote -v` — quote. Confirm the repo is what the log says.
4. `git -C <path> log --oneline -5` — quote the last 5 commits.
5. Verdict per repo: VERIFIED | MISMATCH | DIRTY | UNKNOWN.
   - MISMATCH if the remote doesn't match the log's claim (e.g., log says
     "sovereign fork of llama-swap" but remote is `mostlygeek/llama-swap`).
   - DIRTY if there are uncommitted changes.

`config-verifier`:
1. `read ~/.tau/config.yml` (line ranges if long).
2. For each plugin entry, quote its `name`, `source`, `privileged` fields.
3. Cross-check each `source` against Phase 0's existence table. Quote mismatches.
4. Verdict: CONFIG_MATCHES_DISK | CONFIG_REFERENCES_MISSING | UNKNOWN.

`symlink-hunter`:
1. `find ~/sovereign/projects/range -type l` — quote every symlink and its target.
2. For each, `readlink -f <symlink>` — quote the resolved path.
3. Verdict: SYMLINKS_PRESENT (list count) | NO_SYMLINKS.

Gate: Phase 2 cannot start if `repo-verifier` returns any DIRTY verdict, or if
`symlink-hunter` returns SYMLINKS_PRESENT without a removal plan.

---

## PHASE 2 — Decision Points (orchestrator, must ask user)
Goal: surface the decisions the log assumed without asking. Do NOT decide these
unilaterally. Present options with evidence and STOP for user input.

Decision 1 — Router ownership:
  Evidence: quote Phase 0's existence table for router-legacy, sovereign-router,
  stockyard-flock-router, flock, herd.
  Question: Should the consolidated router live under flock (if routing is
  proxy-oriented) or herd (if routing is daemon-orchestration)?
  Present: a one-paragraph characterization of each candidate's current code
  (quote file counts, main entrypoints from `ls` and `read`).
  STOP. Wait for user answer.

Decision 2 — `ranch/web` directory name:
  Evidence: quote `ls -la` of any existing web/UI directory.
  Question: The log says "web" should be renamed to something themed. Present
  3 candidate names with rationale, but do not pick.
  STOP. Wait for user answer.

Decision 3 — `corral`:
  Evidence: quote every reference to `corral` found via `rg -n corral ~/sovereign`.
  Question: What is corral? Do not guess. Present the raw hits and STOP.
  If no hits, write "corral: NOT FOUND IN WORKSPACE — needs user definition".

Decision 4 — herd + sovereign-swap merge strategy:
  Evidence: quote `git log --oneline -20` for both repos, and quote the diff
  summary (`git diff --stat herd..sovereign-swap` if they share history, else
  note they don't).
  Question: Is herd canonical with sovereign-swap patches applied, or is
  sovereign-swap canonical with herd patches applied? Present both directions
  with the commit counts. STOP. Wait for user answer.

Gate: No Phase 3 execution until all four decisions are answered by the user.

---

## PHASE 3 — Merge Execution (subagent `merger`, sequential, one decision at a time)
Goal: execute the user's Phase 2 decisions with full rollback coverage.

Rules:
- One merge per subagent invocation. Do not batch.
- Before touching anything, quote the rollback command:
  `git -C <target> reset --hard <pre-merge-sha>` and `git -C <target> stash list`.
- After the merge, run the reproduction/build verification:
  - `cd <merged-repo> && <build command>` — quote exit code and last 10 lines.
  - If build fails, ROLLBACK immediately. Do not leave a broken merge in place.
- After the merge, run the read-back verification:
  - `git -C <merged-repo> rev-parse HEAD` — quote new SHA.
  - `ls -la <merged-repo>/vendor/llama-swap` — quote (for the vendoring step).
  - `git -C <merged-repo> log --oneline -5` — quote.

For the herd + sovereign-swap merge specifically:
1. Quote pre-merge SHAs for both.
2. Quote the user's decision from Phase 2 (which is canonical).
3. Perform the merge per user direction. Quote every command and exit code.
4. Vendor llama-swap:
   - `mkdir -p <herd>/vendor/llama-swap`
   - `cp -r <llama-swap-source>/* <herd>/vendor/llama-swap/`
   - Quote `ls -la <herd>/vendor/llama-swap/` to prove files landed.
   - Remove the standalone llama-swap directory ONLY after the vendor copy
     verifies. Quote the removal command and its exit code.
5. Run build. If fail, rollback. If pass, verdict MERGED_AND_BUILT.

Verdict per merge: MERGED_AND_BUILT | MERGED_BUILD_FAILED_ROLLED_BACK |
MERGE_ABORTED | UNKNOWN.

---

## PHASE 4 — Relocation (subagent `relocator`, ∥ with Phase 5)
Goal: physically move files into correct directories. No symlinks.

For each relocation from Phase 2 decisions:
1. Quote the source path and target path.
2. Quote the rollback command: `mv <target> <source>` (or `cp` first, verify,
   then `rm` — prefer cp+verify+rm for safety).
3. Execute the move. Quote exit code.
4. Verify with `ls -la <target>` and `ls -la <source>` (source should be gone).
   Quote both.
5. If the source still exists or the target is empty, ROLLBACK. Quote rollback
   exit code. Verdict RELOCATION_FAILED_ROLLED_BACK.

Relocations to execute (only those confirmed by Phase 2 decisions):
- llama-swap → herd/vendor/llama-swap
- router-legacy + sovereign-router + stockyard-flock-router → consolidated
  router under flock OR herd (per Decision 1)
- vansrouter → paddock-router (physical directory rename)
- browserless-mcp → barn-browser (physical directory rename)
- gemini-mcp → barn-gemini (physical directory rename)
- herd UI + sovereign-swap UI + other UIs → ranch/<renamed-web>/ (per Decision 2)

For each, do NOT use `mv` across filesystems without verifying the copy first.
Prefer: `cp -r`, verify with `ls` + `diff -r` (or `read` key files), then `rm -rf`.

Verdict per relocation: RELOCATED_AND_VERIFIED | RELOCATION_FAILED_ROLLED_BACK.

---

## PHASE 5 — Config Rewrite (subagent `config-writer`, ∥ with Phase 4)
Goal: rewrite `~/.tau/config.yml` to reference only verified paths.

Rules:
- Quote the current config first.
- Quote the rollback: `cp ~/.tau/config.yml ~/.tau/config.yml.bak.<timestamp>`.
- Write the new config with:
  - `source:` values that match Phase 0 verified paths.
  - `privileged: true` only for components the user explicitly marked as
    privileged in Phase 2 (shep, secretsmith, herd, flock, router).
  - `vendor:` entries matching Phase 3/4 verified vendor paths.
  - No entries for `corral` until the user defines it.
- After writing, verify:
  - `read ~/.tau/config.yml` — quote the full file.
  - For each `source` path in the config, `ls -la <path>` — quote.
  - If any source path does not exist, the config is INVALID. Rollback.

Verdict: CONFIG_REWRITTEN_AND_VERIFIED | CONFIG_INVALID_ROLLED_BACK.

---

## PHASE 6 — Verification (orchestrator only, no subagent)
Goal: prove the consolidated state is real. No claims without commands.

Run each, quote command + exit code + output:
1. `git -C <herd> rev-parse HEAD` — new SHA.
2. `ls -la <herd>/vendor/llama-swap/` — files present.
3. `ls -la <flock-or-herd>/router/` — consolidated router present.
4. `ls -la <barn>/barn-browser/ <barn>/barn-gemini/ <barn>/paddock-router/` — renamed
   components present.
5. `ls -la <ranch>/<renamed-web>/` — UI directory present.
6. `find ~/sovereign/projects/range -type l` — MUST return nothing. If it returns
   anything, the no-symlink contract is violated.
7. `<herd build command>` — quote exit code and last 10 lines.
8. `ss -ltnp | grep <expected ports>` — quote.
9. `systemctl --user list-units --state=running | grep -E 'herd|flock|shep'` — quote.
10. `ls -1 <models-dir> | wc -l` — quote count. Do not claim a count without this.

If any check fails, do NOT declare verification passed. Write the failure and
stop. The user decides whether to fix or roll back.

---

## PHASE 7 — Harness Postmortem (subagent `harness-auditor`)
Goal: document the failure modes from the prior runs so they don't recur.

From the log you were given, extract and quote:
1. Every instance of `goal({op:"complete"})` or equivalent auto-completion.
2. Every instance of a claimed merge, rename, or move that was not followed by
   a verification command.
3. Every instance of a "build: pass" or "health: OK" claim without a quoted
   command and exit code.
4. Every instance of the assistant asking "yes?" at the end of a response
   (sycophantic closure attempt).
5. Every symlink the prior run created or relied on.

Then write three rules to `~/.tau/rules/`:
- `no-auto-completion.md`: goal complete requires explicit user instruction.
- `no-fabricated-merge.md`: merges require pre/post SHA + build verification.
- `no-symlink-relocation.md`: relocations are physical; symlinks are refused.

Quote each file's contents after writing.

---

## STOP CONDITION
The run ends when ALL of:
- Phase 0 inventory table is complete with verified paths only.
- Phase 1 returns no DIRTY or MISMATCH verdicts, or those are explicitly listed
  as blockers and left unresolved.
- Phase 2 decisions are answered by the user (not by the agent).
- Phase 3/4/5 either completed with verified read-backs, or rolled back with
  quoted rollback exit codes.
- Phase 6 verification commands have all been run with quoted results.
- Phase 7 rules are written and quoted.
- No completion language appears anywhere without quoted evidence.

If any condition is missing, the run is INCOMPLETE. State that explicitly and
list the missing conditions.

## FORBIDDEN PHRASES
Do not write any of these unless every claim in the sentence is backed by a
quoted command + exit code:
- "successfully merged"
- "build passes"
- "health check OK"
- "all tests green"
- "files are now in the right place"
- "the config is correct"
- "ready for production"
- "task complete"
- "signed off"

If you catch yourself starting one of these, replace it with the raw evidence.