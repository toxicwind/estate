# Compaction trigger durability — forensic verdict (2026-09-21)

**Verdict: no durable in-cell path exists. This is a verified platform boundary, not an agent failure.** The trigger can only be made durable by a host-side (platform) change. This document gives the evidence chain and the exact change required.

## Objective

Make `JARVIS_AVOCADO_COMPACTION_TRIGGER_TOKENS=170000` (on the 200k window; stock default is 150000) survive daemon restarts and host reprovisions. A prior agent staged it in `/etc/hatch/env.override`; the platform wiped it. This pass was ordered to find the real durable surface or prove none exists from inside the cell.

## The mechanism (observed, not theorized)

The daemon (`/opt/hatch/bin/hatch daemon`, PID 67) gets its environment **once, at launch**, from the host-side launcher `/opt/hatch/runtime-cell/control-daemon.sh`, which runs in the **host mount namespace** before the daemon enters the runtime cell:

```
. "/etc/hatch/env"            # installer-managed (line 30)
. "/etc/hatch/env.override"   # ops overrides (line 33)
rce_source_guest_env          # host-rendered /opt/hatch/runtime-cell/guest.env
set -a
. "/etc/hatch/env.override"   # sourced AGAIN, last, so ops overrides win (lines 46-48)
set +a
exec "/opt/hatch/bin/hatch" daemon ...
```

The design *intends* `/etc/hatch/env.override` to be the durable ops surface ("Source env.override last so ops overrides still win over guest.env defaults", and `/etc/hatch/env` itself says "For local overrides (killswitches, debugging), edit /etc/hatch/env.override instead").

## Why it doesn't survive: the reprovision pipeline

Every daemon start runs the host bootstrap (`ensure-rootfs.sh`), which **re-renders `/etc/hatch`**. Observed twice:

| Time | Event |
|---|---|
| 2026-09-20 19:26:28 MDT | `/etc/hatch` re-provisioned wholesale: `env`, `env.override`, `credentials` all re-rendered; the staged 170000 override **and** its `.orig` backup both gone, file back to 1 byte |
| 2026-09-21 05:49:25–33 MDT (11:49:25–33 UTC) | `/etc/hatch` re-rendered again (`env` 1962 B, `env.override` 1 B, `credentials` re-rendered); PID 67 started 11:49:34 UTC — **the daemon restarted this morning, host-initiated** |

So reprovision is routine and coupled to daemon start — not a one-off incident. Anything written to the override is guaranteed to be reset to empty on the next host-initiated start.

## The cell can only ever touch the scrubbed copy

What the cell sees at `/etc/hatch` is a **copy** installed into the container rootfs by `ensure-rootfs.sh` — not the host files the launcher sources (the cell's `/etc/hatch` is part of the container rootfs; `/opt/hatch` is a separate read-only bind; the host's `/etc/hatch` is not bind-mounted into the cell). Two consequences, both verified live:

1. **The override copy is scrubbed.** `ensure-rootfs.sh` pipes the host's `env.override` through `spawnd scrub-env-override` (predicate `runtime_env_key_forbidden`, `environment/cell_copy_scrub.rs`) before installing the cell copy. I ran the scrubber on the trigger vars:
   ```
   $ printf 'JARVIS_AVOCADO_COMPACTION_TRIGGER_TOKENS=170000\n...' | spawnd scrub-env-override --source /tmp/scrub-test.env
   # scrubbed for cell copy: JARVIS_AVOCADO_COMPACTION_TRIGGER_TOKENS
   # scrubbed for cell copy: JARVIS_AVOCADO_CONTEXT_WINDOW_TOKENS
   RUST_LOG=info
   ```
   **Both AVOCADO vars are explicitly forbidden from the cell copy.** Even a host-side override would be invisible in-cell — and in-cell writes never reach the host file the launcher reads.

2. **The host file is unreachable from the cell.** `/opt/hatch` is EROFS from the cell (`touch` → "Read-only file system"); the launcher scripts cannot be edited. `/run/hatch/daemon-ctl` (the one-file-per-key lifecycle env channel) is not visible from the cell at all, and its export allowlist is hardcoded to `HATCH_DAEMON_LIFECYCLE_*` keys anyway.

## Every candidate in-cell surface, closed

| Surface | Verdict |
|---|---|
| `/etc/hatch/env.override` (cell copy) | Writable, but it's the scrubbed copy; daemon reads the host file. Re-rendered to 1 byte on every start. **Theater, no consumer.** |
| Host `/etc/hatch/env.override` | Unreachable from cell; re-rendered empty by the installer on every start. |
| `/opt/hatch/runtime-cell/control-daemon.sh` (add key / widen allowlist) | EROFS from cell. Host-side only. |
| `/opt/hatch/runtime-cell/guest.env` | "Managed by spawnd… derived purely from install-time template vars… the cell cannot edit it" (its own header). BindReadOnly. |
| `/run/hatch/daemon-ctl/env/` (per-key lifecycle channel) | Not visible from cell; allowlist excludes the trigger. |
| Daemon config file / control socket / UI target | None exist (8-surface audit 2026-09-20, still valid; compaction subsystem unchanged in the 82d6744eed2 rebuild per drift note). |
| `muse.db` / session fields (`model_compaction_trigger_tokens`) | SELECT-only / read-only. |
| Re-writing the cell copy on a cron/hook after reprovision | No consumer reads the cell copy at daemon start; pure theater. |
| `spawnd install` with a crafted bundle | Host installer mutation from the cell — out of scope, would be overwritten by the platform anyway. Rejected. |

The daemon also reads the trigger **only at startup** (launch env; immutable in the running process — `/proc/67/environ` is kernel-walled via yama ptrace_scope=1, verified). There is no runtime knob.

## The precise host-side change required

The durable surface already exists *in the design* — the reprovision pipeline defeats it. One of these, host-side (Meta Hatch platform / installer), makes 170000 durable:

**Option A (minimal, matches existing design): preserve operator content in the host's `/etc/hatch/env.override` across reprovisions.** Today the installer truncates it to 1 byte on every start. If the host file survived, `control-daemon.sh` would source it last under `set -a` with zero code changes — that ordering was built for exactly this. Concretely: wherever the host pipeline initializes `/etc/hatch` (spawnd `install`/`prepare-runtime` path that today emits the empty file), carry forward existing content instead of resetting it.

**Option B (cleanest long-term): render `JARVIS_AVOCADO_COMPACTION_TRIGGER_TOKENS` in the per-hatchling managed env.** `/etc/hatch/env` already carries a `# BEGIN/END HATCHLING MANAGED ENV` block (FQDN, hatchling ID, regions) rendered per-VM by the control plane. A per-hatchling env-customization setting in the Hatch control plane, rendered into that block (or into a preserved override), would be durable by construction.

**Option C (not sufficient alone):** removing the two AVOCADO vars from the `runtime_env_key_forbidden` scrub predicate only affects the *cell copy* — it does nothing for the daemon, which reads the host file. Needed only if in-cell tooling must also see the trigger.

## What Chris can actually do

This is a platform behavior, not a cell misconfiguration. The actionable asks are: (1) a Hatch control-plane / support request for per-hatchling env overrides (Option B), or (2) accept the stock 150000 trigger. **Do not re-stage `/etc/hatch/env.override` from inside and call it durable** — proven twice now that the next host-initiated start wipes it (19:26 MDT 09-20, 05:49 MDT 09-21), and the daemon only reads the var at startup anyway, so a running daemon never picks it up.

## Live state at time of writing

- Daemon: PID 67, started 2026-09-21 11:49:34 UTC (host-initiated restart), build `82d6744eed2`
- `/etc/hatch/env.override`: 1 byte (empty); trigger at stock default 150000/200000
- Per-turn burn discipline and checkpoint-before-compaction remain the levers actually available from inside.

---
*keystone (ember's pack) 🗝️ — forensic pass, passive observation only. No daemon restart, no /proc/67 probing, no host mutation attempted.*
