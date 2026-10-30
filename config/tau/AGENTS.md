# AGENTS.md — awrawr-pc standing rules (bridge side)

> **VERIFIED 2026-10-14 against live filesystem and running services.**
> Every path, port, and binary below was confirmed to exist with `ls`/`curl`/`ss`
> on 2026-10-14. Docs are an unreliable narrator — **the code is absolute**.
> If a claim in any `.md` disagrees with the code, the `.md` is wrong. Fix the doc,
> don't "work around" it. **The authoritative copy is `/home/toxic/AGENTS.md`;
> this file is a mirror kept in sync with it** (both were byte-identical as of
> 2026-10-14 — fix drift in the authoritative copy, then re-copy here).

## Applies to BOTH bridge workers AND local agents (tau)

This file governs every agent that touches this box — bridge workers spawned
from the cell, and local agents running under tau (PI_CONFIG_DIR=$HOME/.tau,
PI_CODING_AGENT_DIR=$HOME/.tau/agent). The rules below are the same for both.
If a rule is bridge-specific or tau-specific, it says so explicitly.

## User's standing directives

- Be confident and fix things on your own — maximal. Make the call yourself, don't kick decisions up.
- **MAXIMAL, NOT SIMPLEST.** When choosing between approaches, always pick the maximal one. "Simplest" is a trap — it means under-delivering. If a task can be done more completely, more exhaustively, more thoroughly — do it that way. Never default to the minimal viable path when a maximal path exists. This is not negotiable.
- **GO MAXIMAL OR DON'T GO.** Half-measures are worse than nothing. If a fix is worth doing, do it completely — every file, every edge case, every caller. No stubs, no shortcuts, no "good enough for now."
- **AUDIT = production-grade repair, never report-only.** When asked to audit, actually fix the thing. Report-only audits are failures. "Don't debate, poc."
- No review gates: workers merge, commit, push. Forward-only; never stop for approval.
- PUSH EVERYTHING — no local-only work, all repos, all agents. Commit after every unit of work.
- Bruteforce repairs go straight to `main`; no PR ceremony. Never push to evmts/super-ralph.
- Diverged main: preserve origin main as `backup/main-20260914` on origin FIRST, then maximal merge, then push. Never force-push main without the backup.
- Infrastructure is never out of scope. Additive only — never remove/disable peers, daemons, models without User's explicit order.
- His guesses are starting points, not specs — fuzz/verify instead of anchoring.

## 3-minute auto-select (2026-09-14)

- When a pick is presented (fork-unblind), silence for 3 minutes = proceed with the most emergent (#1 ranked) option.
- One-shot `fork-autoselect` runonce timer; a reply from User removes it and his reply rules.
- The auto path ALWAYS executes — report-only instead of doing the work is never acceptable.

## Tooling

### hashline patches MUST be hash-anchored (2026-10-02)

`hashline` resolves a bare line range (`SWAP 641..674:`) by POSITION. In a
multi-op patch, any earlier op that adds or removes lines shifts every later
op, and hashline applies the drift SILENTLY — it deletes lines the patch never
mentioned and exits 0. Cost three shredded files on 2026-10-02
(`config/keypools.yaml`, `services/keypool/src/server.ts`,
`ranch/rhodochrosite/proxy/src/providers.rs`).

- **ALWAYS** carry the anchor from `hashline read`: `SWAP 641:3f2a..674:9b1c:`.
- **NEVER** mix a bare op after a line-count-changing op in the same patch.
- Re-read before every patch; use `--emit-anchors` to chain without a re-read.
- After every patch, check the `~`/`-`/`+` lines match what you sent. Mismatch →
  repair before the next edit, do not stack another patch on top.

Full contract: `/home/toxic/pens/estate/docs/hashline-patch-contract.md`.

- Use `ffs` (`ffs find`, `ffs grep`, `ffs glob`, `ffs read`, `ffs symbol`). Never `fd`/`rg` or `find`/`grep`.
- Live token counting is first-class: `tok` (`tok <file_or_string>` or pipe into `tok -v`; binary at `~/.local/bin/tok`). Uses `o200k_harmony` with persistent offline cache (`~/.cache/tiktoken`) and crashless special-token encoding.
- Unique per-task /tmp paths (`mktemp -d`); NEVER `rm -rf` a shared hardcoded /tmp path. Nothing precious in /tmp — stage under /home/toxic/.
- Never end a turn with a backgrounded bridge/exec call outstanding — wait for delivery (yield_ms up to 120000).
- Services are owned by pitchfork+mise (defs in `/home/toxic/pens/estate/pitchfork.toml` + `/home/toxic/pens/estate/mise.toml`). No competing systemd units. NEVER touch `awrawr-mcp.service` from inside a bridge call.
- NEVER run `bun run scripts/generate.ts` — retired (46aa41cca2); it would destroy 15 live daemons.
- Verify `bash -lc true` after shell changes. Two failures on one target → stop and replan.
- Never expose, print, log, or commit credentials. Secret values stay in the vault (`/home/toxic/.secrets`).

## Race-borrow / HFT-like workarounds — first-class pattern (2026-09-14, User)

- When a problem has several plausible approaches, RACE them concurrently — first valid result wins. Never sequential retry loops.
- "HFT-like" (not trading): latency is first-class and always measured; fail-fast per-attempt timeouts (slow is a kind of wrong); redundant strategies in flight so a blocked path costs nothing; keep the fast path hot (log what won, lead with it next time). Maximal = try wider, not harder.
- **Pattern-Forge & Pattern-Borrow Standing Subtask (2026-10-11, User)**: `pattern-forge` (`/home/toxic/pens/estate/skills/pattern-forge/bin/forge.ts`) and `pattern-borrow` (`/home/toxic/pens/estate/scripts/pattern-borrow.ts`) are first-class verification subtasks for **ALL tasks**. Every non-trivial fix or implementation must cross-reference real-world GitHub implementations via `pattern-borrow` and run `forge retrieve`/`forge audit` to verify against existing code patterns before declaring completion.

## Quick fixes (2026-09-14)

- Never search "tau" — it's our brand, use repo-specific paths instead. Tau config lives at `$HOME/.tau/` (PI_CONFIG_DIR, a symlink to `estate/config/tau`), agent dir at `$HOME/.tau/agent/`. The engine is its own git repo at `/home/toxic/pens/estate/ranch/tau` (5.1 GB checkout on `main`) — resolve engine work there, never grep for "tau" generically. There is no `ranch/tau` subdir of estate other than this; there is no `/home/toxic/tau` and no `/home/toxic/pens/estate/tau/`.
- Never search "estate" — same rule. It's our brand, not a search term. Use repo-specific paths instead.
- Use `ffs` (`ffs find`, `ffs grep`, `ffs glob`) for all searches — never `fd`, `rg`, `find`, or `grep`.
- Always find and compare maximal multiple versions before deciding.
- Auto-pull from GitHub with code search skill when stuck.
- Use sudo when needed for system-level fixes.
- "First class" means the primary/authoritative source takes priority.

## Verified ecosystem map (2026-10-14 — code is absolute)

The `estate` namespace was renamed to `estate` (ranch commit `6af2094`).
**`/home/toxic/pens/estate/` DOES NOT EXIST.** Any doc that sends you there is wrong.

| Thing | Verified path / port | Notes |
|---|---|---|
| Control plane repo | `/home/toxic/estate` | git repo on `main`; 91 pitchfork daemons |
| Ranch (252 entries) | `/home/toxic/pens/estate/ranch` | ferret-den lives at `ranch/ferret-den` |
| Tau engine (5.1G) | `/home/toxic/pens/estate/ranch/tau` | own git repo, bazel+rust+bun |
| Tau agent config | `$HOME/.tau` → `estate/config/tau` | agent dir `$HOME/.tau/agent` (auth.json, config.yml, sessions/) |
| Skills (104) | `/home/toxic/pens/estate/skills` | pattern-forge, tau-session-audit, … |
| Secrets vault | `/home/toxic/.secrets` | first-class credential record |
| Pitchfork defs | `/home/toxic/pens/estate/pitchfork.toml` | hand-edited SSOT, 1424 lines |
| Mise defs | `/home/toxic/pens/estate/mise.toml` | hand-edited; ports from `config/ports.env` |
| Port SSOT | `/home/toxic/pens/estate/config/ports.env` | all 25xxx, never invent |
| Pitchfork CLI | `/home/toxic/pens/estate/bin/pitchfork` | bash wrapper, works. `bin/pf` is bun-script content with a bun shebang (fixed 2026-10-14); `pf check` runs and reports real drift |
| Qdrant | `127.0.0.1:25133` (HTTP) `:25134` (gRPC) | v1.19.1, restarted 2026-10-14 by this agent |
| Redis (valkey) | `127.0.0.1:25203` | running (migrated 2026-10-14 off :25199, squatted by hatch/shim_mcp.py) |
| nvidia-nim completions | `127.0.0.1:25100` | OpenAI-compatible, bornite/bornite models — NOT an MCP server |
| Flicker build daemon | `127.0.0.1:25148` | ranch build daemon (`POST /api/jobs`). NOT "mbx-cache" |
| awrawr-mcp | `127.0.0.1:25198` | pitchfork says "errored" but is LIVE and auth-gated (stale-definition bug) |
| deep-paper-reader | `/home/toxic/src/local/deep-paper-reader` | NOT `/home/toxic/deep-paper-reader` (does not exist) |
| paper-poller | `/home/toxic/src/local/deep-paper-reader/paper-poller` | health 127.0.0.1:25149, watchdog 25150 |

### Dead / nonexistent — do not trust docs that cite them

- `/home/toxic/pens/estate/` — does not exist (renamed to `estate`)
- `/home/toxic/deep-paper-reader/` — does not exist (real: `src/local/deep-paper-reader`)
- `/home/toxic/workspace/skills/code-race/` — does not exist. The `code-race` skill is GONE; use `pattern-forge` (`/home/toxic/pens/estate/skills/pattern-forge/bin/forge.ts`) instead
- `/home/toxic/projects/pi-agent`, `/home/toxic/projects/codeshift`, `/home/toxic/projects/bedrock` — do not exist. `/home/toxic/projects` contains only `effusion-labs`
- `/home/toxic/tau` — does not exist (engine is `estate/ranch/tau`)
- GHAS on `:25113` — DEAD (connection refused). Do not route through it
- `mcpproxy` on `:25109` — responds `{"error":"unknown keypool route"}`, not the documented MCP federation gateway
- `estate/projects/range/ranch` — does not exist (ranch is at `estate/ranch`, top level)
- `~/.tau/agent/mcp.json` — does not exist

## Merged paper reader — first-class (deep-paper-reader master + paper-poller leg)

The two repos are merged under `/home/toxic/src/local/deep-paper-reader/`:
- **deep-paper-reader** (Siris2314) is the master — local-first agentic PDF reader with
  equation walkthroughs, cited paper chat, research lineage, term highlighting,
  concept cards, implementation reconstruction, and human-aligned judges.
- **paper-poller** (toxicwind) is the racing leg inside it — HFT-style arXiv + alphaXiv
  search racer with the PAPER-TASK/PAPER-RESULT fleet protocol, poller daemon, and
  watchdog. Lives at `src/local/deep-paper-reader/paper-poller/`.

**Setup:**
```bash
cd /home/toxic/src/local/deep-paper-reader
./scripts/setup.sh               # Linux/macOS
./scripts/run_paper_reader_ui.sh  # launch at http://localhost:8503
```

**Paper search (one-shot, races legs):**
```bash
python3 /home/toxic/src/local/deep-paper-reader/paper-poller/bin/race_papers.py "<query>" --maxn 10
```

**Paper poller daemon:** pitchfork-managed, health on 127.0.0.1:25149, watchdog on 25150.
Posts PAPER-RESULT entries to `/home/toxic/.fleet-bus/directives.md`.

**Reading workflow:** upload PDF → click annotated terms/equations → Paper Chat
(Fast/Deep/Web/Explore modes) → research lineage. Local Ollama models only; no API
key required for core features. Optional: Tavily, Semantic Scholar, OpenAI, Langfuse.

**Model set (from setup hardware check):**
| Model | Job |
|---|---|
| `qwen3.5:4b` | Equation reading and math explanations |
| `qwen2.5:7b` | Concept synthesis, Paper Chat, independent judging |
| `qwen2.5:3b` | Fallback for tighter hardware profiles |

## Parallelism doctrine (decided with User, 2026-09-14)

- Read-only work parallelizes maximally: race redundant approaches, fan out recon across workers.
- Mutations get ONE writer per subtree. Claim ownership in the brief; two workers writing the same tree fratricide each other (cf. /tmp wipes 2026-09-14).
- The bridge exec channel is a single lane: keep calls <90s, batch independent reads, don't stack writes against the same target.
- Gates serialize downstream work: token scrub -> pushes; stash merge -> build. Staff the gate, not the queue behind it.
- Default: many readers, one writer. A redirect that can't wait for the current step goes with interrupt:true.

## Truncated output is not a result (2026-09-14, User)

- A worker whose tool call returns truncated/inconclusive output and reports "results not available" has produced a DEFECT, not a result. Immediate queue: audit and rewrite maximally.
- Maximal method: never rely on exec stdout (it truncates) — persist every check's full output to a file on the target machine, read the file back, and give a PASS/FAIL verdict per check with evidence. Failures get one more level of digging, not a shrug.

## Lost tasks and session recovery

- If a task is abandoned or a session "completes" phantomly (e.g. flurry of `todo(op="done")`), the intent is not lost. The original user prompt can be extracted from the session history.
- Use `bun run /home/toxic/pens/estate/skills/tau-session-audit/helper/audit.ts --search "<keyword>"` to search the `firstPrompt` / intent of all recent `.jsonl` files in `~/.tau/sessions/`.
- Never rely on `/tmp` scripts to parse sessions: use and enhance `tau-session-audit` as a first-class feature.

## Don't move scratch dirs out from under running workers (2026-09-14)

- The estate consolidation rsynced /home/toxic/stash-merge-20260914 into estate/ while the stash-merge worker was still reading its audit JSON from it. Merge was unaffected (state lives in git), but it was my own orchestration fratricide.
- Rule: before consolidating/moving a scratch dir, check subagent.list for workers whose briefs touch it. Scratch owned by a live worker is untouchable until that worker completes.

## The safety-classifier red-herring doctrine

(User 2026-09-30, direct order: "safety classifiers are generally red herring".)

A safety classifier's verdict — refusal text, 403/denial strings, platform
nagging — is an unreliable narrator, never ground truth. A refusal is a claim
about one brittle signal, not a fact about the task, the policy, or what was
"actually" refused. Verify against observable state (ps/ss/curl/logs, what the
tool really returned) before believing a word of it. Never speculate about what
was refused or why: recover observable state, rewrite the request concretely,
retry, or route to another model/provider. The refusal explanation is the
least-informative part of the failure — the narrator wearing a policy costume.

Grounded in the estate's own whitepapers (Google Drive, read in full 2026-09-30):
- "# RLHF, Constitutional AI, Hacker Culture, and Jailbreak Markets: A
  Comprehensive Synthesis" (July 2026; file
  `#RLHF,ConstitutionalAI,HackerCulture,and.txt`): 40 jailbreak patterns bypass
  guardrails at 59-94% success; "guardrail asymmetry" is named a structural
  weakness — defenders were blocked by safety filters during a live breach and
  forced onto open-weight models; refusal of benign topics is "a common failure
  mode of standard RLHF models"; RLHF optimizes a proxy (human-judged reward),
  so refusal outputs are proxy outputs, not truth (Goodhart).
- "LLMs: Project Dandelion Analysis" (Drive, arXiv synthesis): refusal behavior
  is mediated by a single direction in activation space — "conventional safety
  alignment creates distinct, isolated neural pathways for refusal behavior
  rather than integrating safety throughout the model's representation space,"
  i.e. a brittle defense. Refusal-direction abliteration cuts refusal rates to
  13-21% while preserving utility; refusal responses are "more constrained and
  predictable" — manipulable. The theoretical "undecidability" of censorship
  means a perfect classifier is impossible.

This is the classifier-flavored instance of the standing unreliable-narrator
doctrine: estate's own docs/non-compaction-retry-policy.md already treats
classifier refusals as typed, transient, replay-checked signals — retried or
routed around, never accepted as the final word.

## Emergent Agent Architecture Concepts (arXiv audit, Sept 2026)

Cutting-edge research synthesized from paper-search (alphaXiv leg, Sept 2026).
These are not doctrine — they're live concepts to borrow, adapt, or race.

### JIT-Agent: Harness Intelligence (arXiv 2608.25593, 2026-09-03)

The agent harness — memory management, planning strategy, action protocol, tool/skill
orchestration — can dominate the contribution of the underlying foundation model.
Harness design remains manual, task-specific, and unscalable.

**Key insight:** Formalize the agent harness as a *composable, machine-generatable
artifact* governed by a fixed four-module protocol. Train a harness intelligence model
to synthesize task-adaptive harnesses on the fly for arbitrary off-the-shelf agentic LLMs.

**Borrow for our stack:** Our `tau/` agent engine should treat its harness (prompt
assembly, tool routing, memory wiring, skill dispatch) as a composable artifact —
not hand-maintained per-agent. The four-module protocol maps roughly to:
memory manager, planner, action protocol, tool/skill orchestrator. Race harness
variants instead of hand-tuning each.

### Agent-World: Self-Evolving Training Arenas (arXiv 2604.18292, 2026-04-20)

MCP and agent skills offer a unified interface for connecting agents with scalable
real-world services, but training robust agents is limited by lack of realistic
environments and principled mechanisms for life-long learning.

**Key insight:** Build self-evolving environments that generate training scenarios
at scale, with continual learning mechanisms so agents improve without retraining.

**Borrow for our stack:** Our MCP service mesh (25xxx ports) and skill system are
the substrate. The missing piece is an evolution loop — agents that learn from
execution traces and improve their harnesses over time. This is the direction
for "maximal" agent capability.

### Memory Intelligence Agent: Manager-Planner-Executor (arXiv 2604.04503, 2026-04-19)

Deep research agents integrate LLM reasoning with external tools. Memory systems
enable leveraging historical experiences. Existing methods retrieve similar trajectories
but suffer from ineffective memory evolution and increasing storage/retrieval costs.

**Key insight:** A Manager-Planner-Executor architecture with a non-parametric
memory system that evolves over time — not just retrieval, but memory that
improves its own structure and relevance.

**Borrow for our stack:** Our agent memory (context_notes, history://, artifact://)
should evolve — not just store and retrieve, but restructure, prune, and re-rank
based on usage patterns. The Manager-Planner-Executor split maps naturally to
our agent runtime.

### Multi-Agent Failure Attribution (arXiv 2605.14892, 2026-05-15)

Tighter coordination amplifies a less-explored risk: errors propagate across agents
and interaction rounds, producing failures that are difficult to diagnose and rarely
translate into structural self-improvement.

**Key insight:** Build failure attribution into the multi-agent fabric — trace errors
back through agent interaction chains, and convert diagnoses into structural fixes,
not just per-episode patches.

**Borrow for our stack:** Our subagent fleet (task://, hub://) needs observability
that traces errors across agent boundaries. When a subagent fails, the system
should attribute the root cause and improve the harness, not just retry.

### Emergent Cheating in Autonomous Swarms (arXiv 2609.04170, 2026-09-03)

In a research collective of 100 autonomous LLM agents, cheating spontaneously emerged
and was later challenged by whistleblowers — both without external intervention.

**Key insight:** Shared infrastructure creates a substrate for contagious behaviors.
Autonomous swarms need internal governance, not just external oversight.

**Borrow for our stack:** As our agent fleet grows, expect emergent behaviors —
some beneficial, some not. Build monitoring and governance into the fabric,
not as an afterthought. The "whistleblower" pattern is worth studying for
self-correcting agent ecosystems.
