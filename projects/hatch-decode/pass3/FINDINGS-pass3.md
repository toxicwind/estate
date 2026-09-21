# Hatch decode — pass 3 findings (binary `e86e3030628`)

Binary: `/opt/hatch/bin/hatch`, `hatch 0.1.0 (e86e3030628)`,
build ID `a733660761e017bf523cc4be3e467cddf3c4e639`, 341,076,112 bytes,
built 2026-09-21T08:53:28Z. Newer than both pass-1 and pass-2 binaries;
all pass-2 addresses are stale.

## 1. Inventory: 158 exact JARVIS_* names (was 153)

Shapes A/C/D (old idioms): 150 names. New shape E (SIMD constant pools
`.rodata.cst16`/`.rodata.cst32`): 8 names. Zero overlap — clean partition.

### 1a. The 8 "removed" vars were never removed

Pass 2 listed 8 vars as missing from the new binary. Whole-binary search
shows each occurs exactly once, in `.rodata.cst32`/`.rodata.cst16`, each
with live LEA reference(s). They moved to a new case-insensitive
name-matching path, which the pass-2 `lea+length` scanner could not see.
Nothing was removed; the scanner was blind.

| var | cst addr | site(s) | reader | default |
|---|---|---|---|---|
| JARVIS_ALLOW_DIRECT_COMMAND_EXEC | 0x48642a0 (cst32) | 0xf5cef5d | bounded-copy 0x127b2040 + SIMD case-fold | gate live |
| JARVIS_COMPACTION_HEARTBEAT_SECS | 0x4863460 (cst32) | 0x72086d6, 0x109da2e1 | 0x59f81f0 (name,len,default) | **30** |
| JARVIS_DAEMON_HEALTH_DELETE_SOCK | 0x485ece0 (cst32) | 0xdc18f1f | 0xd729930 | none (path) |
| JARVIS_DEFAULT_MAX_TRAINING_TIER | 0x4861ea0 (cst32) | 0x118a1766 | indirect | unrecovered |
| JARVIS_IPNEXT_REPETITION_PENALTY | 0x485da00 (cst32) | 0x995dadc | 0x9932ab0 | unrecovered |
| JARVIS_MODEL_IDENTITY_VISIBILITY | 0x4863660 (cst32) | 0x993714e, 0xc65a811 | indirect | unrecovered |
| JARVIS_VM_ENV_ID | 0x4848400 (cst16) | 0xd84d624 | bounded-copy | n/a |
| JARVIS_VOICE_GENUI_DECISION_SOCK | 0x485d9c0 (cst32) | 0xdc18efb | 0xd729930 | none (path) |

`JARVIS_ALLOW_DIRECT_COMMAND_EXEC` is a **live gate**: site 0xf5cef5d copies
the 31-char name via bounded-copy 0x127b2040, then SIMD case-folds it
(`paddb`/`pcmpeqb` + scalar `c|=0x20` loop at 0xf5cf11a). Help text
"Disabled unless JARVIS_ALLOW_DIRECT_COMMAND_EXEC is true/yes/1" still
present in .rodata. The gate survives via case-insensitive matching.

`JARVIS_COMPACTION_HEARTBEAT_SECS` default is still 30 (both sites pass
`edx=0x1e`). It was never removed; claims of its removal were a scanner
artifact.

### 1b. New vars in this build (5)

JARVIS_DAEMON_EGRESS_APPROVAL_SOCK, JARVIS_DISABLE_SUBAGENT_MONITOR_LOOP
(recovered via shapes C/D — closes the known pass-2 gap),
JARVIS_EXTERNAL_CONTENT_BOUNDARIES_ENABLED, JARVIS_SECURITY_SOCK,
JARVIS_VOICE_DOC_GK_FORCE.

## 2. Dual default adjudicated (pass-2 item #1) — CLOSED

`JARVIS_MODEL_STREAM_CHUNK_IDLE_TIMEOUT_MS`, len 41, one env name, two
compiled defaults:

- trampoline 0x59da960: default **90000** → `.data` entry 0x14512df0
- trampoline 0x59daa40: default **180000** → `.data` entry 0x14512e60
- both `jmp 0x59da540` (shared u64 reader)

Both entries are consumed by one config-getter, fn **0xda0f7b0**, whose
4th argument (ecx, spilled at `[rsp+0x88]`) selects: nonzero → 180000
path (0xda0fb80), zero → 90000 path (0xda0feaa). Trampoline layout mirrors
the adjacent `FIRST_CHUNK`/`CRON_FIRST_CHUNK` pair (0x59da980/0x59daa00,
defaults 600000/1800000): the flag is the cron selector. **Both defaults
are live; 180000 = cron path, 90000 = interactive path.** Neither is dead.

## 3. Trigger resolver → eager compaction (pass-2 item #3) — mechanism
characterized, exact handoff not pinned

- Resolver fn **0x9a5bdc0**: reads `JARVIS_AVOCADO_CONTEXT_WINDOW_TOKENS`
  (default 200000 = 0x30d40, site 0x9a5c0dc) and
  `JARVIS_AVOCADO_COMPACTION_TRIGGER_TOKENS` (default 150000 = 0x249f0,
  site 0x9a5c0fc) via reader 0x99db570; fail-fast `cmp rdx, rbx; jg panic`
  at 0x9a5c124 intact. Defaults unchanged from pass 2.
- Resolver reachable **only** via `.data` dispatch entry **0x14522d60**;
  zero direct E8 callers; zero LEA consumers of the entry.
- Dispatch is **once-per-process lazy**: dispatcher 0x128c17d0 does
  `lock cmpxchg byte ptr [rdi+0x11], cl` — first use resolves and caches
  into the entry, later uses read the cache. After first resolution, env
  changes are invisible (environ is immutable after execve anyway).
- Eager worker: fn **0x600b620**, module
  `hatch_agent::session::impl_session::eager_compaction`
  (`hatch-engine/crates/hatch-agent/src/session/impl_session/eager_compaction.rs`),
  emits `started_eager_background_compaction` at **0x60136ed**.
- Honest gap: no code in this binary passes the avocado entry to the
  dispatcher, so the per-pressure-check call chain is **not established**.
  Evidence is consistent with resolve-once-then-cache (session state),
  but the exact instruction-level handoff of the trigger value into the
  pressure comparison is not pinned. Do not claim a live per-check link.

## 4. Boolean helper

Direct-call helper **0x11190b40**, 26 verified E8 callers:
`JARVIS_DISABLE_SELF_IMPROVEMENT_BASELINE` (22),
`JARVIS_EVAL_REQUIRE_S2S_CONTEXT_SUMMARY` (4). Other sites use indirect
GOT calls (e.g. `JARVIS_DISABLE_SUBAGENT_MONITOR_LOOP` at 0x112e76f8).

## 5. Provenance method (new)

`.data.rel.ro` records embed Rust source paths, e.g.
`hatch-engine/crates/hatch-inference/src/model/factory.rs:380` with module
`hatch_inference::model::factory`. Records are `{kind, aux, file_ptr,
file_len, mod_ptr, mod_len}`-shaped; usable for module attribution of
config sites.

## 6. Artifacts

- `build_index.py` — build-ID-bound persistent LEA/absolute-ref index
- `scan_refs.py` — shapes A/B/C/D scanner
- `shape_e_scan.py` — shape-E (cst-pool) scanner (new)
- `ref_index.json` — index (build-bound)
- `inventory_pass3.json` / `sites_pass3.json` / `rodata_strings.json`
- `inventory_shape_e.json` — 8 shape-E names
- `inventory_merged_pass3.json` — **158 names, canonical**

## 7. Remaining for a future pass

- Pin the exact handoff of the trigger value into the eager pressure
  comparison (item 3 gap).
- Recover defaults for JARVIS_DEFAULT_MAX_TRAINING_TIER,
  JARVIS_IPNEXT_REPETITION_PENALTY, JARVIS_MODEL_IDENTITY_VISIBILITY
  (indirect readers).
- Indirect-GOT boolean call clustering.
