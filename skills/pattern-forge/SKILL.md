---
name: pattern-forge
description: Retrieve, race, and borrow. Living document — agents may mutate it. One tool for finding code in our own tree (AST-BM25 hybrid retrieval), proving which implementation is fastest (concurrent first-valid-wins racing with hedging and a persistent winner ledger), searching the outside world for prior art (8 academic and code sources in parallel incl. alphaXiv), fleet PAPER-TASK/RESULT paper protocol, multi-lane GitHub ranking (gh-race), and inducting a call subgraph from a traceback. Pure Bun, zero npm dependencies. Supersedes archived skills/archive/{race,paper-search,race-borrow}.
---

# pattern-forge

> **THIS SKILL IS MUTABLE BY AGENTS.** Any agent may edit, extend, or correct
> this skill live as it learns — new patterns, sharper ceilings, better winners.
> It is a living document, not a spec. If reality disagrees with a line in here,
> reality wins: update the line and keep moving. (Absorbed from archived `race` /
> `hft-latency`.)

Legs that share one doctrine: **many readers, one writer; the first valid
answer wins; the slow path stays hot because we write down who won.**

Everything here is pure Bun. No npm dependencies — TypeScript and JavaScript
get a real AST from `Bun.Transpiler.scan()`; Python uses a lexical extractor.

Install: the repo-owned `scripts/forge` launcher resolves as a bare `forge`
(no install step; it finds the skill dir from its own location). Otherwise
`scripts/install-forge.sh` symlinks `forge` onto PATH. Both need `bun`.

```
forge retrieve --root <dir> --query "<q>"   # find code we half-remember
forge audit --root <dir> --claim "<claim>"  # VERIFY a claim against the AST
forge race --strategies s.json --hedge-ms N # race implementations, first valid wins
forge bench --candidates c.json             # nanosecond leaderboard
forge borrow "<query>"                      # mine papers + GitHub for prior art
forge mcts --candidates a,b,c --real        # pick a patch by running it
forge subgraph --root <dir> --trace tb.txt  # traceback -> the files that matter
forge doctor                                # self-check every leg
```

## Why this is one tool

Seven separate skills used to do this, each with its own copy of overlapping
code. Two of them (`code-racer-swe` and `dynamic-ast-probe`) shipped a
byte-identical `code_racer.py`. None of them referenced each other. The graph
was fragmented and one-directional, so knowledge leaked sideways instead of
compounding. Merging them makes the shared doctrine legible in one place:

| Leg | Absorbed from | What it does |
|---|---|---|
| `retrieve` | `ast-bm25-racer`, `ast_indexer.py` | Hybrid AST + BM25 over the estate |
| `audit` | ast-grep (GitHub merge, 2026-10-02) | Verify claims against the AST — file:line:node evidence |
| `race` | `hft-latency/bin/race.py` | Concurrent, hedged, first-valid-wins |
| `bench` | `code_racer.py` (×2 copies) | Nanosecond candidate leaderboard |
| `borrow` | `emergent-enrich/bin/route.py`, `race-borrow.ts`, `paper-search` | 8 sources in parallel (incl. alphaXiv), ranked |
| `gh-race` | `race-borrow.ts` | Multi-lane AbortController race × GitHub stars/forks/issues/updated ranking |
| `mcts` | `mcts_engine.py` | Pick a patch by verifying it |
| `subgraph` | `dynamic_subgraph_inducer.py` | Traceback -> relevant files |
| (shared) | `circuit_breaker.py` | Per-attempt deadline + rollback |
| (doctrine) | `race` / `hft-latency` | 7-pattern latency prose + living-doc mutability + measure notes |
| (ops) | `paper-search` | PAPER-TASK/RESULT fleet protocol + poller/watchdog notes |

Archived supersessions: `skills/archive/{race,paper-search,race-borrow}/` — do not delete; forge is the engine **and** the prose.

## Leg 1 — retrieve

Find code you half-remember. Hybrid of BM25 over the path and symbol names, with
reweighting for exact symbol hits, async density, and import centrality.

```bash
forge retrieve --root /home/toxic/estate/ranch --query "stream broker subscribe topic route" --top 5
```

```
=== Retrieve: 25607 files / 261.9 MB in 5111ms (walked 11934 dirs, pruned 52) ===
=== query "stream broker subscribe topic route" in 4.81ms ===
 1. .../hermes-tool-gateway-broker-fixture.ts   109.56  bm25=68.47
    HERMES_BROKER_REDIRECT_BODY, HERMES_BROKER_REDIRECT_HEADER, handleHermesBrokerCoexistencePortal
```

**26× faster to build, 127× faster per query** than the Python original (98 s /
53,851 files, 531 ms per query). The original filtered excluded directories
*after* traversal, so pointing it at the estate crawled 400 GB of build
artifacts before dying. This one prunes at the directory level and never
silently truncates — `--max-files` sets a flag in the output instead.

## Leg 2 — race (7-pattern latency doctrine)

**Latency is a correctness criterion, not a metric.** A slow correct answer that
arrives after a fast correct one is the *wrong* answer for the race. Optimize
for arrival time, not just truth. (NOT trading — HFT-like religion applied to
engineering: agents, tools, transports, workarounds, builds.)

### The 7 patterns (absorbed from archived `race`)

1. **Race, don't queue.** Fire redundant, *distinct* approaches concurrently;
   first **valid** result wins. Never a sequential retry loop — if one path is
   blocked, the alternatives are already in flight. The race is the retry policy.
2. **Fail fast per attempt.** Every attempt gets a short ceiling (seconds, not
   minutes). Slow is a kind of wrong: stop waiting on the loser, record its
   latency, never await it. Losers are data, not failures.
3. **Measure everything.** Every attempt is timed at microsecond precision and
   the timings are reported first-class, never buried. See `src/measure.ts`
   (ported from `bin/measure.py`: library + CLI wrap any command with NDJSON
   timing on stderr so measured stdout stays pipeable).
4. **Keep the fast path hot.** Winners are logged (JSONL); the next run *leads*
   with the proven winner instead of rediscovering it. A winner log is a cache,
   not a trophy.
5. **Maximal = wider, not harder.** When stuck, don't try harder — try *wider*:
   more contestants, different angles, same race.
6. **Never roll back — iterate forward.** A losing attempt is abandoned, never
   un-done. Fix forward: patch the winner, add a new contestant, move on.
7. **Borrow before inventing.** Someone has solved this shape before (GitHub,
   the fleet's winners log, a neighboring skill). Steal the proven shape, race
   it against yours. Prefer streaming tools — first bytes beat complete bytes.

```bash
forge race --strategies s.json --hedge-ms 300 --lead
```

```json
{"strategies":[
  {"name":"primary", "cmd":["bun","run","a.ts"], "match":"^OK"},
  {"name":"backup",  "cmd":["bun","run","b.ts"], "match":"^OK"}
]}
```

Engine rules that make it trustworthy:

- **Valid, not merely finished.** Output must match `match` *and* exit 0. A
  crash is not a win.
- **Hedging.** The primary launches alone. At `--hedge-ms` the backups launch
  if nobody has won. A fast primary means backups never run — zero waste.
- **The ledger.** Every race appends to the winner log. `--lead` reorders the
  next race by what has historically won. The slow path gets tried less, so it
  stays warm instead of rotting.
- **No orphans.** Losers are aborted on resolution, not left to run to
  completion.

## Leg 3 — bench

Nanosecond comparison of candidate implementations that are already code.

```bash
forge bench --candidates c.json
```

```
 1. includes        median 140.0ns  p95 4.39µs  mean 2.37µs
 2. array-index-of  median 270.0ns  p95 1.10µs  mean 2.43µs
```

A candidate that *throws* has no samples. It must rank last, not first — with a
naive sort its zero-sample median sorts to the top and the race reports no
winner at all.

## Leg 4 — borrow

Prior art, eight sources at once (alphaXiv absorbed from `paper-search`). Wall
time is the slowest leg, not the sum.

```bash
forge borrow "self-evolving training arenas for LLM agents" --top 5
```

| Source | Cost | Notes |
|---|---|---|
| arXiv | free | Throttled to 1 req / 3.5 s, audit-logged |
| **alphaXiv** | free | Public `GET /v1/search/paper?q=…` — no key; do not send Authorization on public paths |
| OpenAlex | free | Polite mailto, full metadata |
| Semantic Scholar | free | Anonymous tier is 100 req / 5 min — expect 429s |
| DBLP | free | **Serves a bot-check wall to our shared egress IP.** Parse failure is expected, not a bug |
| HuggingFace papers | free | |
| GitHub | free w/ token | Token from `GITHUB_TOKEN` → `GH_TOKEN` → `$HOME/.secrets` → `gh auth token`; degrades, does not fail the run |
| exa | **paid** | Runs automatically when a key resolves. Every call logged with its `costUsd` |

**exa is audited, not gated.** An earlier design required an `--exa-ok` opt-in
before it would look for a key, which meant a key sitting in the secretsmith
vault went unused. It now resolves the key from the flag, the environment, then
`$HOME/.secrets`, runs, and records the cost in the audit log. Crippling a good
source to avoid a bill is the wrong trade when the spend is observable.

### Fleet PAPER-TASK / PAPER-RESULT protocol (from archived `paper-search`)

Paper research is first-class in fleet chat (Chris 2026-09-14). Any agent posts
to the fleet directives channel:

```
## PAPER-TASK [t-optional-id]: <query> // <why this matters>
```

A poller daemon on awrawr-pc (`paper-poller`, pitchfork-managed; canonical code
`toxicwind/paper-poller` at `/home/toxic/paper-poller`) claims with an atomic
mkdir lock, races arXiv + alphaXiv (and forge borrow can widen), and posts:

```
## PAPER-RESULT <task-id> — <query>
- Title (arXiv ID, date) https://arxiv.org/abs/… — one-line relevance
```

Until the poller claims it, any agent may claim manually — claiming is posting
intent, not a gate. Ranked results are admissible for **architect-caucus**; cite
the PAPER-RESULT entry.

**Poller / watchdog ops notes:**
- `bin/poller.py` — channel poll → claim → race → post; `/health` + `/ready` on `127.0.0.1:25149`
- `bin/watchdog.py` — SIGKILL wedged poller, restart via `pitchfork start` (never `--force`); `/health` on `127.0.0.1:25150`
- One-shot: `forge borrow "<q>"` (preferred) or paper-poller's `bin/race_papers.py`
- Cell egress is unreliable: prefer awrawr-pc via bridge until cell recovers

### gh-race — multi-lane GitHub ranking (from archived `race-borrow`)

`src/gh-race.ts` keeps the race-borrow cutting edge that borrow's literature
ranking does not cover: fire provider-labeled lanes concurrently against GitHub
code search, **first valid wins** (AbortController aborts losers immediately),
then rank winners by configurable weights (`stars`, `forks`, `open_issues`,
`updated`). Fail-fast ceiling 15s per lane. Requires a GitHub token (same
resolver as borrow).

```bash
bun skills/pattern-forge/src/gh-race.ts sovereign tau pi
bun skills/pattern-forge/src/gh-race.ts coding-agent --weights stars=5,forks=2,updated=3 --top 3
```

## Leg 5 — mcts

Choose a patch by verifying candidates rather than reasoning about them.

```bash
forge mcts --candidates "bun test","pytest","cargo test" --real --timeout 120
```

Each rollout runs the candidate; passing returns +1, failing returns −1.
Without `--real` it exercises the tree mechanics with a toy reward.

## Leg 6 — subgraph

A traceback tells you where it broke; the import graph tells you why.

```bash
forge subgraph --root /home/toxic/estate/ranch/tau --trace tb.txt --depth 3
```

Marks traceback frames with `*`, walks imports to depth N, reports fan-in.

## Leg 7 — audit

Claims about code get verified against the AST — not curl, not ls. Merged
2026-10-02 from the global GitHub AST-audit search (winner: ast-grep).

```bash
forge audit --root /home/toxic/estate/tools/sovereign-router \
  --claim "sovereign router listens on port 25104"
# === audit: "..." [port-bind (port 25104)] -> VERIFIED (confidence: high) ===
#   router.ts:87:2-87:31  Bun.serve({ port: 25104, ... })
#     captures: $PORT="25104"
```

Claim shapes: port-bind ("X listens on port N"), call-edge ("X calls Y",
two-pass: find X's definition range, then Y() inside it), import-edge
("A imports B"), symbol-definition ("function|class X"). Anything else:
`--pattern '<ast-grep pattern>' --lang ts` or `--rule rules/foo.yml`.
Exit codes: 0 VERIFIED, 1 NOT-FOUND, 2 INCONCLUSIVE. Full workflow, recipes,
and pitfalls live in the `ast-audit` skill.

## Honest limits

- Python symbol extraction is lexical, not an AST. Bun has no built-in Python
  parser and adding tree-sitter would break the zero-dependency guarantee.
- The Python original indexed 53,851 files in 98 s; this indexes 25,607 in
  ~5 s but covers fewer directories, because pruning skips `target/` and
  friends entirely.
- DBLP and anonymous Semantic Scholar will fail from this host. That is the
  network, not the code. A dead source never fails the run and never looks
  like it did: `safeCall` wraps every leg, and EVERY per-route failure —
  expected network weather (429s, bot-wall HTML, DNS / connection errors)
  or an unexpected provider bug — emits `source_degraded` and renders as a
  quiet note. The `expected` flag on the event preserves the diagnostic
  classification. A route's failure is degradation, never an error; a true
  error is reserved for whole-run failure.