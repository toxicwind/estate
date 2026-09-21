# hatch-decode — oracle forward decoding of /opt/hatch/bin/hatch

Target: `/opt/hatch/bin/hatch` — stripped ELF, 341MB, x86-64, Rust, imports
`getenv@GLIBC_2.2.5`. The daemon that owns this runtime cell.

Goal: for every `JARVIS_*` env knob, determine **what reads it**, **when**
(startup-once into a config struct vs lazily per use), the **compiled default**,
and whether a value change can take effect **without a daemon restart**.

## The 8 orthogonal lanes

| Lane | Script | Method | Question answered |
|------|--------|--------|-------------------|
| L1 | `lanes/lane1_strings.sh` | strings-context mining, one pass | per-var adjacent evidence: defaults, log lines, error text |
| L2 | `lanes/lane2_elf.sh` | ELF/dynamic structure | imports, sections, `.rustc`, build-id |
| L3 | `lanes/lane3_xref.py` | fast-xref: byte-scan `.text` for RIP-relative LEAs targeting each var string + capstone windows | instruction-level read sites per var |
| L4 | `lanes/lane4_rust.sh` | Rust remnants | module paths (`hatch::`), panic sites, lazy-init markers (`OnceLock`, `get_or_init`) |
| L5 | `lanes/lane5_syscalls.sh` | syscall/import surface | inotify/fanotify/signal/epoll — any reload mechanism? |
| L6 | `lanes/lane6_paths.sh` | path-constant sweep | every baked-in `/etc /run /opt /var` path — what files it touches |
| L7 | `lanes/lane7_companions.sh` | companion binaries + launcher scripts | does `spawnd` read the vars? who sets what, when? |
| L8 | `lanes/lane8_live.sh` | live observation without ptrace | `/proc/67` cmdline/maps/fd, sockets, `/etc/hatch` mtimes |

Run: `cd lanes && chmod +x lane* && ./lane1_strings.sh` … each writes to `../findings/`.

## Oracle forward decoding

Lanes emit **claims** into `findings/`. The oracle (`ORACLE.md`) adjudicates:
per-var verdicts — reader, timing, default, live-change path, confidence.
Forward = binary → meaning; the oracle resolves lane conflicts with evidence,
never by vote.

## Tooling notes

- Cell: binutils + `pip install capstone` (done 2026-09-20). No `paru` here.
- yote (Arch/CachyOS, `paru`): for deeper lanes — `paru -S radare2 ghidra`
  (ghidra headless decompile), `x64dbg`-class work stays manual.
- Repos: capstone (PyPI) for disasm windows; anything heavier gets its own lane doc.

## Standing findings

- 2026-09-20: 131 unique `JARVIS_*` strings in the binary (`findings/jarvis_vars.txt`).
- 2026-09-20: `/etc/hatch/env.override` is **not** a durable ops surface — the host
  re-provisioned `/etc/hatch` wholesale at 19:26 MDT, wiping a staged
  `JARVIS_AVOCADO_COMPACTION_TRIGGER_TOKENS=170000`. Durable path must be
  wherever the host renders it from (host-side, outside the cell).
