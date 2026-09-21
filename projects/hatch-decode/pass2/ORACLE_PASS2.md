# ORACLE PASS 2 — JARVIS_* exhaustive map

**Binary:** `/opt/hatch/bin/hatch` — stripped x86-64 PIE ELF, 341,643,792 bytes,
build-id `a8dd68c1f8682fce61a4559191556fbca7e4e6f6`, imports `getenv@GLIBC_2.2.5`.
**Method:** read-only disassembly (Capstone, corrected VA→file mapping via
`readelf -S`; `.text`: VA `0x4885a00` = file `0x4884a00`). Nothing written to
`/etc/hatch` or `/opt/hatch` during analysis.

**Status of claims:** every default below was read from a `mov reg, imm`
immediately feeding an env-reader call. Reader VAs are exact. Timing claims are
code-verified (once-guard / call-graph / dispatch-table), not inferred from
proximity. Confidence is stated per item.

---

## 1. Exact-name inventory: 153 distinct `JARVIS_*` names

`inventory_v2.json` / `INVENTORY.md` — produced by a binary-wide RIP-relative
`lea` + reader-supplied-length scan (337 raw occurrences, 403 exact `lea`
references, 239 strings with length votes). A name is admitted only if the
supplied length yields a full `JARVIS_[A-Z0-9_]+` match — no fused/packed
false positives.

Known gap: `JARVIS_DISABLE_SUBAGENT_MONITOR_LOOP` is proven to exist (single
verified code site, see §4) but is not in the 153 — it is read through a
different shape (shared boolean helper via GOT, not the `lea`+length idiom).
The inventory is the best exact set for the `lea` shape, not yet proven
exhaustive across all reader shapes (static `&str` records in `.data.rel.ro`,
relocations, indirect/table dispatch).

---

## 2. Decoded integer defaults (30 names, 35 sites)

Direct chunk idiom, machine-verified:

```asm
lea rdi, [rip → name]      ; exact JARVIS_* string
mov esi, <name_length>     ; exact length (cross-checks the inventory)
mov edx, <compiled_default>
call <env-u64-reader>
```

| Variable | Default | Reader VA(s) |
|---|---|---|
| `JARVIS_ACCEPTED_TURN_FIRST_PROGRESS_TIMEOUT_MS` | 90000 | `0x65ca030`-family |
| `JARVIS_SUBAGENT_CONTROL_OP_TIMEOUT_MS` | 90000 | `0x65ca030`-family |
| `JARVIS_POST_TOOL_CONTINUATION_TIMEOUT_MS` | 30000 | `0x65ca030`-family |
| `JARVIS_POST_INFERENCE_TERMINALIZATION_TIMEOUT_MS` | 30000 | `0x65ca030`-family |
| `JARVIS_RESUMED_TURN_INFERENCE_READINESS_TIMEOUT_MS` | 90000 | `0x65ca030`-family |
| `JARVIS_MESSAGE_EVENT_STREAM_IDLE_TIMEOUT_MS` | 90000 | `0x65ca030`-family |
| `JARVIS_MODEL_STREAM_FIRST_CHUNK_TIMEOUT_MS` | 600000 | `0x65ca030`-family |
| `JARVIS_CRON_MODEL_STREAM_FIRST_CHUNK_TIMEOUT_MS` | 1800000 | `0x65ca030`-family |
| `JARVIS_COMMENTARY_END_TURN_MERGE_TIMEOUT_MS` | 60000 | `0x65ca030`-family |
| `JARVIS_TOOL_DISPATCH_TIMEOUT_MS` | 180000 | `0x65ca030`-family |
| `JARVIS_PRE_INFERENCE_STEP_TIMEOUT_MS` | 10000 | `0x65ca030`-family |
| `JARVIS_MODEL_STREAM_CHUNK_IDLE_TIMEOUT_MS` | 90000 **and** 180000 | two wrappers — **open item**: trace each wrapper through the `.data` table (`~0x1459d468`, alternating fn-ptr / tag `3`) to its caller before adjudicating |
| `JARVIS_TOOL_DISPATCH_HEARTBEAT_SECS` | 60 | `0x65f2a90` ×2 |
| `JARVIS_COMPACTION_HEARTBEAT_SECS` | 30 | `0x65f2a90` ×2 |
| `JARVIS_AUDIO_TRANSCRIPTION_TIMEOUT_MS` | 4000 | triple |
| `JARVIS_AUDIO_TRANSCRIPTION_COLD_TIMEOUT_MS` | 15000 | triple |
| `JARVIS_AUDIO_TRANSCRIPTION_PREWARM_TIMEOUT_MS` | 45000 | triple |
| `JARVIS_STALE_COMPLETED_UNSEEN_SUBAGENT_CRON_GRACE_SECS` | 21600 | triple |
| `JARVIS_STALE_COMPLETED_UNSEEN_SUBAGENT_NON_CRON_TERMINAL_GRACE_SECS` | 604800 | triple |
| `JARVIS_STALE_COMPLETED_UNSEEN_SUBAGENT_RECENT_DECISION_GRACE_SECS` | 3600 | triple |
| `JARVIS_SELF_IMPROVEMENT_DB_PURGE_LIMIT` | 500 | triple |
| `JARVIS_SELF_IMPROVEMENT_DB_TERMINAL_RETENTION_SECS` | 2592000 | triple |
| `JARVIS_SELF_IMPROVEMENT_RECORDS_RETENTION_SECS` | 7776000 | triple |
| `JARVIS_SELF_IMPROVEMENT_CONNECTOR_AUDIT_RETENTION_SECS` | 2592000 | triple |
| `JARVIS_SELF_IMPROVEMENT_LEARNINGS_RETIRED_RETENTION_SECS` | 7776000 | triple |
| `JARVIS_SELF_IMPROVEMENT_BACKFILL_DAYS_RETENTION_SECS` | 2592000 | triple |
| `JARVIS_IDEAS_EVENTS_RETENTION_SECS` | 15552000 | triple |
| `JARVIS_AGENT_RECOVERY_OWNER_RETENTION_SECS` | 7776000 | triple |
| `JARVIS_AGENT_RECOVERY_OWNER_PURGE_LIMIT` | 500 | triple |
| `JARVIS_AGENT_RECOVERY_OWNER_RECONCILE_LIMIT` | 500 | triple |

Correction applied in this pass: `env_triples.json` v1 computed branch targets
4 bytes early (`iva+18+rel` instead of the branch's next RIP). True reader
entrypoints are `0x65c9c80`, `0x65f2a90`, `0x5ac4da0`, `0xe113600`,
`0xe115cf0`. Defaults and names were unaffected.

---

## 3. Compaction / memory — the four vars that matter

### `JARVIS_AVOCADO_CONTEXT_WINDOW_TOKENS` — default **200000** (`0x30d40`)
### `JARVIS_AVOCADO_COMPACTION_TRIGGER_TOKENS` — default **150000** (`0x249f0`)

**Read site (exact, independently re-verified this pass):** resolver at VA
`0x9936fd0`. At `0x993703c`:
```asm
lea rdi, [rip-0x636d1f3]   ; → "JARVIS_AVOCADO_CONTEXT_WINDOW_TOKENS"
mov esi, 0x24              ; len 36
call 0x98b8810             ; env-or-default helper
test al, 1
mov ebx, 0x30d40           ; fallback 200000
cmovne rbx, rdx            ; env value wins if parsed
```
At `0x993705c`: same for `JARVIS_AVOCADO_COMPACTION_TRIGGER_TOKENS`, len
`0x28` (40), fallback `0x249f0` (150000). At `0x9937084`:
`cmp rdx, rbx; jg 0x9937092` — **trigger > window is a fail-fast panic**
(format string: `"<TRIGGER> must be less than or equal to <WINDOW> (got <t> > <w>)"`).
170000 < 200000: safe.

**Model dispatch (verified):** the resolver's first action is a model-name
check — prefix `"avocado"` (len 7), then exact `"avocado-9b-voice-staging"`
(len 24) → hardcoded `(128000, 96000)`, bypassing env entirely.

**Timing — CORRECTED this pass (was: once-at-init; now: stateless per-invocation):**
the resolver contains **no cache, no OnceLock, no static** — every call
re-reads process env. It is referenced only as a function pointer in a
`.data` dispatch table (24-byte tagged entries at file `0x145a9f50…`,
resolver entry at `0x145aa090`), consumed by compaction-path code
(20 RIP-relative xrefs from `0x89bdc11`, `0x8bffae9`, `0x8c017aa…`,
`0x8d55007…`). So the values are re-resolved per dispatch, **but the source
is still the immutable process environ** — see §6. Pass-1's "once at init"
was wrong; the worker's "lazy" is right about the resolver, but neither
changes the no-live-update verdict.

### `JARVIS_COMPACTION_HEARTBEAT_SECS` — default **30** (`0x1e`)
Two inline read sites (`0x80428c0`, `~0x10ad0eee`), no dedicated resolver.
Fresh env lookup at point of use — the laziest of the four.

### `JARVIS_MEMORY_FLUSH_PERIODIC_THRESHOLD_TOKENS` — default **50000** (`0xc350`)
Read site `0x841b3f1` in fn `0x841b3e0`; all fallback paths converge on
`mov ebx, 0xc350`. Fresh env read per invocation (indirect dispatch).

**Eager compactor:** no `JARVIS_*EAGER*` variable exists in the string
inventory — the eager background compactor runs off the shared trigger.
Telemetry fields: `model_compaction_trigger_tokens`,
`agent_compaction_trigger_tokens`, `auto_compact_limit_tokens`,
`tokens_remaining_to_compaction`.

---

## 4. Killswitch / lifecycle vars

Shared boolean helper at `0xe0aed90` (via GOT). Garbage values log
`invalid boolean env override; ignoring` and are treated as unset —
**a typo does not disable**. Truthy: `true`/`yes`/`1`.

| Variable | Default | Timing (code-verified) |
|---|---|---|
| `JARVIS_DISABLE_SCHEDULER_LOOP` | false (loop on) | once at daemon startup — single site `0xf0ae7ca`, worker-spawn path |
| `JARVIS_DISABLE_SUBAGENT_MONITOR_LOOP` | false | once at daemon startup — single site |
| `JARVIS_DISABLE_NATIVE_FILESYSTEM_WATCHER` | false | once at daemon startup (watcher install) |
| `JARVIS_DISABLE_SELF_IMPROVEMENT_BASELINE` | false | **per scheduled maintenance run** (lazy gate on the cron job) |
| `JARVIS_ALLOW_DIRECT_COMMAND_EXEC` | **disabled** | **per exec attempt** (lazy security gate) |
| `JARVIS_AGENT_RECOVERY_OWNER_RETENTION_SECS` | integer secs (table) | per reconcile cycle |
| `JARVIS_AGENT_RECOVERY_OWNER_PURGE_LIMIT` | positive int (table) | per reconcile cycle |
| `JARVIS_AGENT_RECOVERY_OWNER_RECONCILE_LIMIT` | positive int (validated: `agent recovery owner reconciliation limit must be positive`) | per reconcile cycle |
| `JARVIS_MAX_COMPANION_LIFETIME_SECS` | integer secs | per companion creation (inferred, weak-moderate) |

**`JARVIS_ENV_FILE`** (len 15): exactly one code site (`0x9a6128f` in loader
`0x9a61200`, via `std::env::var`). Unset → file read skipped silently.
Set-but-unreadable → `failed to read model resolver env file; using process
env and defaults`. **Once at daemon startup** (single caller `0x1131fb52`
in the post-ready reconcile path; state-byte once-guard in the loader).
Apparent compiled default is the relative path `PROFILE.md` (suggestive, not
certain — set an absolute path). Serves the **model resolver only**; none of
the §3 vars flow through it.

**Reload sweep:** notify-rs/inotify is linked but serves only channel YAML
configs (Telegram `~/config/home.yaml`, WhatsApp channel config) — no
`JARVIS_*` var and not the env file are watched. No SIGHUP handler, no
generic config reload. `setenv` has exactly one caller in the binary
(`0x1281b027`), an unrelated internal initializer.

**"Launch-time inputs" clarified:** "lazy" above means the *read* happens
per-run/per-attempt — but the *source* is always the process environ fixed at
`execve`. No post-launch change is observable without a daemon restart.

---

## 5. Live-change feasibility — the structural verdict

**NO for every var examined.** All readers resolve through the process
environ (`getenv`/`environ`; GOT `0x145993f0`/`0x14598f78`). A running
process's environ cannot be changed from outside (verified: `/proc/67/environ`
unreadable under yama ptrace_scope=1; no in-process reload path exists).
Even the uncached per-invocation readers (§3) can only re-read the same
frozen environ. **A host-initiated daemon restart picks up new values
immediately** — no stale caches anywhere in these paths.

---

## 6. The durable 170000 fix — BLOCKED at the host boundary

**Objective:** `JARVIS_AVOCADO_COMPACTION_TRIGGER_TOKENS=170000` in the
daemon's launch environment, surviving reprovision.

**What was tried and what actually happened:**
- 2026-09-20 ~17:35 MDT: staged `170000` in cell-visible `/etc/hatch/env.override`
  (the launcher `control-daemon.sh` sources it twice, last under `set -a`).
- 2026-09-20 19:26:28 MDT: host reprovision re-rendered `/etc/hatch` wholesale
  (env, env.override → 1 byte, credentials). Staged override destroyed.
- 2026-09-20 19:26:30 MDT: **daemon PID 67 restarted** — 2 seconds after the
  wipe — launching **without** the override.
- 2026-09-20 20:10 MDT: live session reports `compaction_trigger_tokens:
  150000` (the compiled default). Confirmed via `session_status`.

**Why the cell-visible path can never work (verified, not theorized):**
- `/` is an overlay with `upperdir=/run/hatch/overlay/upper` on **tmpfs** —
  every cell-side write to `/etc/hatch` is RAM-backed and discarded on
  reprovision. (`/home/hatch` is btrfs-backed and persistent; `/etc/hatch`
  is not.)
- The host's `/etc/hatch/env.override` (the durable source) is populated by
  the Hatch platform's fleet enrollment / installer provisioning (`spawnd
  install` bundle; "fleet env.override self-healing scrub" via
  `REMOVED_RUNTIME_ENV_KEYS` enrollment). The cell-visible copy is rendered
  from it by `spawnd scrub-env-override` during `ensure-rootfs.sh`.
- No writable mount, API, skill, or reachable metadata endpoint
  (`http://169.254.169.254/` is unreachable through the egress gate) crosses
  that boundary from inside the cell.
- Ordering is fatal: reprovision re-renders `/etc/hatch` *before* the daemon
  restart, so even a re-staged cell-side override is wiped before it could
  take effect.

**Required operator action (host-side, outside the cell):** add
`JARVIS_AVOCADO_COMPACTION_TRIGGER_TOKENS=170000` to the host's
`/etc/hatch/env.override` (or the fleet enrollment that renders it), then
let the next host-initiated daemon start pick it up. Verify with a fresh
session's `session_status` → `compaction_trigger_tokens == 170000`.
**Do not restart PID 67 from inside the cell to apply it.**

---

## 7. Confidence ledger

- **High:** 153 exact names+lengths; 30 u64 defaults; avocado read sites,
  defaults, validation panic, model-dispatch branch; bool helper semantics;
  JARVIS_ENV_FILE once-at-startup (3 converging proofs); no-reload sweep;
  tmpfs-overlay wipe mechanism; PID 67 restart ordering; live 150000 reading.
- **Medium:** per-run/per-attempt/per-cycle timing labels (call-graph
  adjacent-string evidence, not full caller traces); `PROFILE.md` as
  JARVIS_ENV_FILE default (suggestive table adjacency); heartbeat second
  site VA (`~0x10ad0eee`).
- **Open items:** `JARVIS_MODEL_STREAM_CHUNK_IDLE_TIMEOUT_MS` dual default
  (90000 vs 180000) — needs per-wrapper caller trace through the `.data`
  table; inventory exhaustiveness beyond the `lea` shape (missing
  `JARVIS_DISABLE_SUBAGENT_MONITOR_LOOP` proves the gap); code-level link
  from the trigger resolver to the eager-compaction pressure check
  (telemetry-level only).

## 8. Reproducibility notes

- Pin Capstone before re-running the scanners (global install was used;
  project pin + regression tests still to add).
- VA→file: use `readelf -S` section mapping (`.text`: VA `0x4885a00` =
  file `0x4884a00`); never index the file by VA.
- Capstone `ins.op_str` is operand-only — regexes must not expect a leading
  mnemonic.
- The `0x6924bf0` "reader cluster" is a false positive from packed-region
  proximity (example pointed at `model returned malformed tool call name`).
- Lane scripts still contain repo-banned patterns (`head`, `/dev/null`) —
  normalize before final commit.
