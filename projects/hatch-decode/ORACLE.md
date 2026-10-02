# ORACLE — adjudicated verdicts (pass 1, 2026-09-20)

Method: 8 lanes emit claims with evidence; the oracle resolves by evidence
strength. Verdicts below. `live-change` = can the value take effect without a
daemon restart.

## Headline

The compaction trigger is **not lazy** — it is read **once at daemon startup**
by a single init function (`.text` ~`0x993703c`). No reload path exists in the
binary for it. Chris's "if it's lazy we can fix that": the answer is no — the
durable fix is launch-env + host-initiated restart, never an in-place tweak.

## The reader (proven)

One function reads both avocado vars back-to-back via an `env_u64` helper
(`0x98b8810`: `getenv` + `str::parse::<u64>`, indirect GOT calls):

```
lea rdi,[rip→"JARVIS_AVOCADO_CONTEXT_WINDOW_TOKENS"]  esi=0x24 (36)
call env_u64 → default 0x30d40 = 200000
lea rdi,[rip→"JARVIS_AVOCADO_COMPACTION_TRIGGER_TOKENS"] esi=0x28 (40)
call env_u64 → default 0x249f0 = 150000
cmp trigger, window; jg FATAL
```

FATAL when `trigger > window`: `"<name> must be less than or equal to <name>
(got <t> > <w>)"` — the var names for the message come from a static
`[&str; 2]` table at `.data.rel.ro+0x322fe8` (VA `0x141833e8`). That table is
**only** referenced by this fatal path — it is not the read path.

## Verdict table

| var | reader | timing | default | live-change | conf | evidence |
|-----|--------|--------|---------|-------------|------|----------|
| JARVIS_AVOCADO_CONTEXT_WINDOW_TOKENS | init fn `0x993703c` via env_u64 | once at startup | 200000 | NO — restart required | high | disasm: `mov ebx,0x30d40; cmovne` |
| JARVIS_AVOCADO_COMPACTION_TRIGGER_TOKENS | same fn | once at startup | 150000 | NO — restart required | high | disasm: `mov edx,0x249f0; cmovne`; fatal if > window |
| JARVIS_COMPACTION_HEARTBEAT_SECS | `(ptr,len,default)` helper, `hatch_agent` code | once at subsystem init | 30 (`0x1e`) | NO | high | single xref; `mov edx,0x1e` |
| JARVIS_DISABLE_SCHEDULER_LOOP | bool helper | once at loop init | false | NO | high | `test al,1; jne` init branch |
| JARVIS_DISABLE_SUBAGENT_MONITOR_LOOP | bool helper | once at loop init | false | NO | high | same pattern |
| JARVIS_MEMORY_FLUSH_PERIODIC_THRESHOLD_TOKENS | prompt-build path | per flush build (lazy candidate) | unknown | unlikely (process env fixed at exec) | medium | single xref; adjacent prompt-section strings |
| JARVIS_ENV_FILE | model resolver | per resolution? (diver-b) | n/a (file path) | MAYBE — file re-read is the live path | medium | `"failed to read model resolver env file; using process env and defaults"` |
| JARVIS_ALLOW_DIRECT_COMMAND_EXEC | — | 0 xrefs in binary | unknown | — | low | string present, no code ref found |

## Supporting findings

- Binary imports `inotify_init1/add_watch/rm_watch`, `epoll_*`, `eventfd`,
  `setenv`/`unsetenv`, `environ` — reload/mutation machinery **exists**, but no
  evidence ties it to these vars.
- `JARVIS_ENV_FILE` context proves a **file** read with fallback to process env
  + defaults — the only candidate live knob in the set. Diver-b is resolving
  its path and read timing.
- `/etc/hatch/env.override` is **not durable** (host re-provisioned `/etc/hatch`
  at 19:26 MDT, wiping a staged `170000`). Durable source is wherever the host
  renders it from — outside the cell.
- PID 67 cmdline: `/opt/hatch/bin/hatch daemon --runtime-cell-leader=1960`
  (17 threads, 210 fds, VmRSS ~1.5G).

## Method note — the fused-string trap

Naive `JARVIS_[A-Z_0-9]+` regex **fused** the two packed Rust `&str`s
(`...TOKENSJARVIS_AVOCADO_...`, no NUL between them) into one match, hiding the
real reader under a concatenated key. The L3 xref for the fused key was the
actual read site. Lesson: treat packed string tables as tables, not C strings.

## Open questions

- Host-side renderer of `/etc/hatch` (outside the cell — needs host trace).
- `JARVIS_ENV_FILE` path + read timing (diver-b running).
- Remaining ~120 vars: same treatment in waves; killswitch/lifecycle lane
  (diver-a) running.
