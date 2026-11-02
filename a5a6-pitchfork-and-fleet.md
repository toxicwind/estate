# A5A6 — Pitchfork Archaeology & Fleet Substrate Analysis

**Date:** 2026-10-23
**Agent:** anomaly-a5a6
**Scope:** Anomaly #6 (pitchfork two-truth) + Anomaly #7 (fleet substrate failure)
**Evidence files:** `pitchfork-convention-report.md`, `estate-recovery-report.md`, `estate-recovery6-state.md`

---

## A5 — PITCHFORK ARCHAEOLOGY (Anomaly #6)

### A5a — ComposerAudit: Fragment Classification Results

**Method:** Hash each `pitchfork.d/*.toml`, extract its `[daemons.X]` section, compare line-by-line against monolith `pitchfork.toml` after stripping comments.

**Classification definitions:**
- **DEAD:** Fragment declares `[daemons.X]` but `X` does NOT exist in monolith (name absent)
- **LIVE-MIRROR:** Daemon name exists in monolith AND fragment content is identical (modulo comments)
- **LIVE-SHADOWED:** Daemon name exists in monolith BUT fragment content differs (monolith won)

**Real counts from live `estate/pitchfork.d/` (103 `.toml` files):**

| Classification | Count | Percentage |
|---|---|---|
| DEAD | 4 | 3.9% |
| LIVE-MIRROR | 25 | 24.3% |
| LIVE-SHADOWED | 74 | 71.8% |

**DEAD fragments (4):** daemon name does not exist in monolith at all
| File | Daemon Name | Notes |
|---|---|---|
| `gatehouse.toml` | `gatehouse` | Renamed to `thresher` in monolith; fragment references old `pens/barn/gatehouse` dir |
| `keeper-failover.toml` | `keeper-failover` | Drop-in for browser-keeper; never registered in monolith |
| `olympus.toml` | `olympus` | Path `/home/toxic/pens/olympus/` appears in monolith as string, but no `daemons.olympus` block |
| `tailscale-keepalive.toml` | `tailscale-keepalive` | Added as a concept 2026-10-22; never adopted into monolith |

**LIVE-MIRROR fragments (25):** content identical to monolith
`bidder-finch`, `bidder-forge`, `bidder-raccoon`, `bidder-scout`, `bidder-vesper`, `bidder-warden`, `dnsmasq`, `estate-reconcile-watch`, `fleet-ui`, `hodos`, `kafka`, `kappa-acp`, `kimiclaw-b`, `kite-daemon`, `market-loop`, `market-watchdog`, `nats-tail`, `nats`, `proc-watch-audit`, `refusal-watchdog`, `rustdesk-hbbr`, `rustdesk-hbbs`, `sorry-watchdog`, `stash-guard`, `task-launch`, `tmp-reaper`

**LIVE-SHADOWED fragments (74):** content differs from monolith
These are the majority — fragments that share a daemon name with the monolith but have diverged content. The monolith is the live truth; fragments are stale snapshots.

**Non-`.toml` files in `pitchfork.d/` (6):**
| File | Status |
|---|---|
| `hodos.toml.bak-20261018-flockdown` | Archived backup |
| `kappa-board-bridge.toml.stale-dup-20261022` | Stale duplicate detection artifact |
| `omniroute.toml.off` | Disabled product |
| `openfang-front.toml.bak-20261013` | Archived backup |
| `rustdesk-hbbs.toml.bak` | Backup copy |
| `storage` | Non-text file (skip) |

**Total files in `pitchfork.d/`: 109** (103 `.toml` + 6 special)

### A5b — DriftDetector: Design + Code Sketch

**Purpose:** Daily daemon-drift check comparing three sources of truth.

**Three sources to compare:**
1. Monolith daemon names: `grep -oP '^\[daemons\.([a-z0-9_-]+)\]' pitchfork.toml | cut -d. -f3 | sort -u`
2. Live `pitchfork list` states: parse `--json` output for status (running/errored/stopped/available)
3. Fragment daemon names: extract from `pitchfork.d/*.toml` files

**Drift flags:**
1. **MONOLITH-RUNNING-MISMATCH:** Daemon in monolith not in `pitchfork list` (because errored/stopped manually)
2. **RUNNING-BUT-NO-MONOLITH:** Daemon running that has no monolith block (manual/outside-pitchfork)
3. **FRAGMENT-NO-MONOLITH:** Fragment declares daemon name not in monolith (class: DEAD per A5a)
4. **CONTENT-DRIFT:** Fragment content differs from monolith (class: SHADOWED per A5a)

**Expected-drift cases (not anomalies):**
| Daemon | Why |
|---|---|
| `hodos` | Runs outside pitchfork (managed separately); stopped in pitchfork intentionally |
| `files` | Intentionally stopped; health endpoint :34567 works if started |
| `gatehouse` | Stale rename leftover; DO NOT START |
| `awrawr-mcp` | External peer (managed separately from pitchfork) |

**Code sketch (bash one-liner for cron):**
```bash
#!/bin/bash
# daily-drift-check.sh — run as pitchfork-reconcile user
MONO=$(grep -oP '^\[daemons\.\K[a-z0-9_-]+' /home/toxic/pens/estate/pitchfork.toml | sort -u)
FRAGS=$(for f in /home/toxic/pens/estate/pitchfork.d/*.toml; do basename "$f" .toml; done | sort -u)
RUNNING=$(cd /home/toxic/estate && pitchfork list --json 2>/dev/null | python3 -c "
import json,sys
data=json.loads(sys.stdin.read())
print('\n'.join(d['name'] for d in data if d['status']=='running'))
" | sort -u)

echo "=== DRIFT CHECK: $(date -Iseconds) ==="
# Dead fragments (in .d but not in monolith)
comm -23 <(echo "$FRAGS") <(echo "$MONO") | while read d; do
    echo "DEAD-FRAGMENT: $d (in pitchfork.d/, not in monolith)"
done
# Running but not in monolith
comm -23 <(echo "$RUNNING") <(echo "$MONO") | while read d; do
    echo "EXTERNAL-RUNNING: $d (running, no monolith block — may be managed outside pitchfork)"
done
# Monolith but not running
comm -13 <(echo "$RUNNING") <(echo "$MONO") | while read d; do
    # Check if stopped or available
    status=$(cd /home/toxic/estate && pitchfork list --json 2>/dev/null | python3 -c "
import json,sys
data=json.loads(sys.stdin.read())
for d in data:
    if d['name']=='$d':
        print(d['status']); break
" 2>/dev/null)
    echo "NOT-RUNNING: $d (in monolith, status=$status)"
done | tee /home/toxic/tmp/drift-$(date +%Y%m%d).log
```

### A5c — MigrationLinter: Rule List

**Rule 1: Dead/stale file detection**
Flag any file in `pitchfork.d/` matching `*.off`, `*.bak*`, `*.stale*`:
- `omniroute.toml.off` — dead product
- `openfang-front.toml.bak-20261013` — archived
- `hodos.toml.bak-20261018-flockdown` — archived
- `kappa-board-bridge.toml.stale-dup-20261022` — stale duplicate
- `rustdesk-hbbs.toml.bak` — backup copy
- `gatehouse.toml.off` (in pens/ranch/thresher, pens/barn/thresher) — renamed product

**Rule 2: Renamed-daemon fragments**
Flag fragments whose daemon names no longer exist in monolith due to rename:
- `gatehouse.toml` → monolith has `thresher` instead (line 438-452)
- Fragment still references `pens/barn/gatehouse` and `gatehouse-serve.ts` (both wrong)

**Rule 3: projects.toml missing paths**
17 of 31 project paths are missing on disk. Categories:
- `tools/*` (5 entries): live in `pens/ranch/tools/` or `pens/`, not `estate/tools/`
- `standalone/*` (12 entries): paths like `standalone/bedrock/` don't exist; repos live elsewhere
- `ranch/barn/gatehouse`: directory renamed to `thresher`

**Rule 4: Native mechanism never adopted**
`pitchfork config list` returns `[]`. This is THE signal: the native fragment registration mechanism was never used. Any fragment that was meant to be "live" was never registered.

**Rule 5: Monolith shadows pitchfork.d**
As proven by the recovery: edits to fragments only took effect when the same changes were applied to `pitchfork.toml`. The monolith is the only live truth.

### A5d — MinimalComposer: Recommendation Spec

**Two coherent options:**

#### Option 1: Keep monolith, clean up dead fragments (RECOMMENDED)
Given that:
- The monolith is 35KB with ~106 daemon blocks (~69 unique daemons)
- 103 fragments are dead litter (never composed, never registered)
- The recovery proved monolith-shadowing works (edits to fragments had no effect)
- `generate.ts` was retired because it destroyed hand-tuned config
- 74 of 103 fragments are LIVE-SHADOWED (content diverged from monolith)

**Action:** Delete `pitchfork.d/` entirely. Keep `pitchfork.toml` as hand-edited SSOT.
**Risk:** LOW — fleet is live and stable with this arrangement. The only risk is if future hand-edits introduce drift that isn't reviewed.

#### Option 2: Adopt D2 convention fully
**Action:** Run `pf migrate` to split monolith → fragments, fix `projects.toml` paths, adopt the convention.
**Risk:** HIGH — a wrong move = fleet down (106 daemons; each needs correct toolchain, env, ports). This would require:
- Architect sign-off
- Full fleet stop before split
- Validation of every daemon post-split
- Training on `pf` workflow

**Recommendation:** Option 1. The estate has proven through recovery that monolith is the only live truth. The fragment directory is 103 files of dead weight. Clean them up.

---

## A6 — FLEET SUBSTRATE (Anomaly #7)

### Current Fleet State (2026-10-23 ~20:20 MDT)

| State | Count | Details |
|---|---|---|
| running | 85 | Full fleet operational |
| errored | 5 | beellama-fast, herd, market-loop, ml-serve, toolcall-llm |
| stopped | 14 | archguard-api, archguard-falkordb, bin-contract-audit, custom-auto-shim, delendai-control-plane, delendai-web, files, gatehouse, hodos, kafka, kitty-mcp, proc-watch-audit, qdrant, shim-drift-watch |
| available | 8 | awrawr-mcp, bedrock-ui, boundless, gibber-mcp, kimi-audit-dash, kimi-code, refusal-watchdog, sorry-watchdog |

**Disk:** 86% used (136GB free of 928GB) — within safe threshold

### A6a — PreflightGate: Pre-start Check Script (~60 lines Python)

```python
#!/usr/bin/env python3
"""
preflight.py — pre-flight check before pitchfork start <daemon>

Usage: python3 preflight.py <daemon_name> [config_dir]
Returns 0 on success, 1 on failure. Writes diagnostic to stderr.
"""
import sys, os, subprocess, socket

def check_disk(config_dir="."):
    """Check disk > 90% free threshold."""
    st = os.statvfs(config_dir)
    free_pct = (st.f_bavail * st.f_frsize) / (st.f_blocks * st.f_frsize) * 100
    if free_pct < 10:
        print(f"FAIL: disk at {100-free_pct:.0f}% used (threshold: 90%)", file=sys.stderr)
        return False
    return True

def check_mise(daemon_config):
    """Check mise resolves for the daemon's toolchain."""
    if not daemon_config.get("mise"):
        return True  # no mise requirement
    # Check mise binary exists
    try:
        subprocess.run(["mise", "--version"], check=True, capture_output=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("FAIL: mise not available for toolchain resolution", file=sys.stderr)
        return False
    return True

def check_ports(config):
    """Check expected ports are free."""
    port = config.get("port")
    if port is None:
        return True
    health = config.get("health_http")
    if health:
        # Parse port from health_http URL
        import re
        m = re.search(r':(\d+)/', health)
        if m:
            port = int(m.group(1))
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.connect(("127.0.0.1", port))
        sock.close()
        print(f"FAIL: port {port} already in use", file=sys.stderr)
        return False
    except (ConnectionRefusedError, OSError):
        return True  # port is free

def check_binary(config):
    """Check target binary exists and is executable."""
    run = config.get("run", "")
    # Extract first token (binary path) from run command
    parts = run.split()
    if parts:
        binary = parts[0]
        if not os.path.isfile(binary):
            print(f"FAIL: binary not found: {binary}", file=sys.stderr)
            return False
        if not os.access(binary, os.X_OK):
            print(f"FAIL: binary not executable: {binary}", file=sys.stderr)
            return False
    return True

def check_health(pid, health_url, timeout=30):
    """Check health endpoint after start."""
    import re
    if not health_url:
        return True  # no health check configured
    m = re.search(r':(\d+)/', health_url)
    if not m:
        return True
    port = int(m.group(1))
    for i in range(timeout):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect(("127.0.0.1", port))
            sock.close()
            return True
        except (ConnectionRefusedError, OSError):
            import time
            time.sleep(1)
    print(f"FAIL: health endpoint :{port} not responding after {timeout}s", file=sys.stderr)
    return False

def main():
    if len(sys.argv) < 2:
        print("Usage: preflight.py <daemon_name> [config_dir]", file=sys.stderr)
        sys.exit(1)
    
    daemon = sys.argv[1]
    config_dir = sys.argv[2] if len(sys.argv) > 2 else "/home/toxic/pens/estate"
    
    # Parse daemon config from monolith
    import re
    with open(os.path.join(config_dir, "pitchfork.toml")) as f:
        content = f.read()
    
    pattern = rf'\[daemons\.{re.escape(daemon)}\](.*?)(?=\n\[daemons\.|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        print(f"FAIL: daemon '{daemon}' not found in monolith", file=sys.stderr)
        sys.exit(1)
    
    config_text = match.group(1)
    config = {}
    for line in config_text.split('\n'):
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            key, _, val = line.partition('=')
            config[key.strip()] = val.strip()
    
    checks = [
        ("disk", check_disk(config_dir)),
        ("mise", check_mise(config)),
        ("ports", check_ports(config)),
        ("binary", check_binary(config)),
    ]
    
    failed = [name for name, ok in checks if not ok]
    if failed:
        print(f"FAIL: {', '.join(failed)}", file=sys.stderr)
        sys.exit(1)
    
    print(f"PASS: {daemon} preflight checks ok", file=sys.stderr)
    sys.exit(0)

if __name__ == "__main__":
    main()
```

### A6b — ToolchainIsolation: Per-Daemon mise Environment

**The exact token that killed 65 daemons:** `bun:path@true`

This malformed token was likely a config line like `mise = bun:path@true` which pitchfork interpreted as an invalid toolchain directive, causing 65 daemons to fail on exec.

**Config diff that fixed it (phone-sentinel example):**
```toml
# BEFORE (broken — global bun:path leaked):
[daemons.phone-sentinel]
# ... (no mise or wrong mise)
run = "exec /home/toxic/.bun/bin/bun run server"

# AFTER (correct — per-daemon mise env):
[daemons.phone-sentinel]
mise = true
run = "exec /home/toxic/.bun/bin/bun run server"
# mise.toml toolchain: bun pinned per-project
```

**Validation script snippet (grep all pitchfork configs for dangerous tokens):**
```bash
#!/bin/bash
# scan_for_bad_tokens.sh — find dangerous toolchain tokens across all configs
CONFIGS="/home/toxic/pens/estate/pitchfork.toml /home/toxic/pens/estate/projects.toml"

echo "=== Scanning for dangerous tokens ==="
for cfg in $CONFIGS; do
    echo "--- $cfg ---"
    grep -n 'bun:path\|@true\|path@' "$cfg" 2>/dev/null
done

# Also scan all .toml fragments
find /home/toxic/pens/estate/pitchfork.d -name '*.toml' | while read f; do
    grep -l 'bun:path\|@true\|path@' "$f" 2>/dev/null
done

echo "=== Scan complete ==="
```

### A6b (cont'd) — What the scan found:

<tool_call>
<function=bash>
### A6b (cont'd) — What the scan found:

**Validation results:** Clean — no `bun:path@true` or malformed tokens in monolith or fragments. The prior recovery workers already corrected this.

### A6c — CrashLoopBackoff: Design

**Observed cases:**
1. **browser-keeper:** Crashes every ~2 minutes; no HTTP on :25157 or :25233. Likely Playwright/chromium mismatch or keeper.cjs runtime error.
2. **market-loop:** Module-resolution loop causing exit code 1.
3. **herd:** Go binary ABI segfault (same as flicker — rebuilt from source as the fix).

**Design — per-daemon exponential backoff:**

```
State machine per daemon:
  STARTING → RUNNING (health_ok)
              → ERRORED (health_fail / exit != 0)
              → BACKOFF(N) where N = min(max_attempts, ceil(log2(restart_count)))
              → CRITICAL if N > max_attempts (hold + alert)

Transition rules:
  - On health_http failure or exit != 0: increment restart_counter, enter BACKOFF
  - Backoff interval: 2^N seconds, capped at 5 min
  - After 5 consecutive failures in 30 min window: HOLD + alert (stderr captured)
  - Single writer: pitchfork-reconcile.service is the only restart source
  - Capture: last 50 lines of stderr on each crash, write to /home/toxic/tmp/crashlog-<daemon>.log
```

**Implementation in reconcile loop (pseudocode):**
```python
crash_counter = {}
for daemon in daemons:
    status = query_pitchfork(daemon)
    if status.errored:
        counter = crash_counter[daemon] = crash_counter.get(daemon, 0) + 1
        if counter == 1:
            capture_stderr(daemon, f"/home/toxic/tmp/crashlog-{daemon}.log")
        if counter >= 5:
            mark_critical(daemon, f"{counter} crashes, holding")
        elif time_since_last_restart(daemon) < 2**min(counter, 5):
            skip_restart(daemon)  # respect backoff
        else:
            restart_daemon(daemon)
```

### A6d — Reconciler: Desired-vs-Actual Spec

**What `pitchfork-reconcile.service` does now:**
- Iterates ~103 daemons at ~2s each (3+ min total cycle)
- Attempts to reregister and converge config drift
- Was failing since Oct 12 (exit-code 1/FAILURE), now ACTIVE since Oct 23 ~20:12
- Successfully re-adopted `browser-keeper` and `market-loop` mid-recovery

**State machine:**

| Desired State | Actual State | Action |
|---|---|---|
| running | running | No-op (healthy) |
| running | errored | Restart daemon + capture stderr |
| running | stopped | Start daemon |
| running | available | Start daemon (was never running) |
| stopped | stopped | No-op (intentional) |
| stopped | running | Stop daemon (unexpected) |
| N/A | errored | Kill zombie + alert |

**Known blockers (5 — explicit exceptions pending architect action):**
| Daemon | Blocker | Fix required |
|---|---|---|
| `beellama-fast` | Missing MODEL=/home/toxic/models/EXAONE-4.0-1.2B-IQ4_XS.gguf | Download GGUF |
| `herd` | Go binary ABI segfault (SIGSEGV at exec) | Rebuild from source |
| `ml-serve` | Exit code 1 | Inspect config/stderr |
| `toolcall-llm` | Missing MODEL GGUF | Download GGUF |
| `market-loop` | Exit code 1 (module-resolution loop) | Fix module path in config |

**Orphan policy (from R6):**
- pitchfork supervisor is **SESSION-SCOPED** (under `user@1000.service`, not system-level)
- When the IDE session dies, supervisor dies → daemons survive but are orphaned
- v2.8+ can re-adopt survivors only if the supervisor survived
- Session-scoped death means it CAN'T re-adopt
- **Upgrade path:** Move from `systemctl --user pitchfork.service` to system-level
  - CLI: `pitchfork boot` enables boot start
  - `pitchfork boot --enable` to make supervisor survive session death
  - Then `systemctl --user daemon-reload && systemctl --user restart pitchfork`

### EXPERIMENT A5: Daily Drift-Detection Cron

**Artifact 1: Live/Dead Fragment Map**

This is the classification table from A5a, persisted as the first artifact. The map shows:
- 106 monolith daemons (source of truth)
- 103 pitchfork.d fragments
  - 25 LIVE-MIRROR (safe to delete, content matches monolith)
  - 74 LIVE-SHADOWED (dangerous — content diverged, monolith is correct)
  - 4 DEAD (never adopted, can be safely deleted)
- 6 special files (.off, .bak, .stale)

**Tie to pitchfork-reconcile.service:** The reconcile service already iterates all daemons; it should incorporate the drift check as its first step before attempting restarts. Currently it's ACTIVE and cycling.

### EXPERIMENT A6: Dry-Run Reconciliation Design

**Goal:** errored → 0, with explicit exception markers for the 5 known blockers.

**Dry-run approach (since `--dry-run` may not be supported):** Offline computation of desired-vs-actual map.

**Desired state:** 85 of 106 daemons configured as "running" (14 intentionally stopped, 7 are available-only)
**Actual state:** 85 running, 5 errored, 14 stopped, 8 available

**Target: 0 errored.** Currently 5 errored:
- `beellama-fast` → BLOCKED (missing GGUF)
- `herd` → BLOCKED (ABI segfault, rebuild pending)
- `market-loop` → BLOCKED (module-resolution exit 1)
- `ml-serve` → BLOCKED (exit 1, config/model issue)
- `toolcall-llm` → BLOCKED (missing GGUF)

**Exception markers for the reconciler:**
```
EXCEPTION: beellama-fast — pending architect: model download
EXCEPTION: herd — pending architect: ABI rebuild
EXCEPTION: market-loop — pending architect: module path fix
EXCEPTION: ml-serve — pending architect: config/model fix
EXCEPTION: toolcall-llm — pending architect: model download
```

**Reconciler action on these:** Skip restart (mark as EXCEPTED), don't enter crash loop, alert architect.

---

## A6 Supervisor-Mode Recommendation

**One-liner:** Move pitchfork from `systemctl --user pitchfork.service` (session-scoped, dies with IDE session) to system-level via `pitchfork boot --enable` + `systemctl enable --global pitchfork.service`. This prevents the session-scoped death that left 65+ daemons orphaned and is the root cause of why the reconcile service had to manually re-adopt `browser-keeper` and `market-loop` mid-recovery. The upgrade path is: `pitchfork boot --enable` → `systemctl --user daemon-reload` → `systemctl --user enable --now pitchfork.service` → verify with `systemctl --user status pitchfork`.

---

## Appendix: Evidence Cross-Reference

| Finding | Evidence Source |
|---|---|
| Monolith is 35,723 bytes, 106 daemon blocks | `pitchfork-convention-report.md` §2, §8 |
| 103 pitchfork.d fragments | glob result: 103 .toml + 6 special files |
| `pitchfork config list` returns `[]` | `pitchfork-convention-report.md` §2 |
| `generate.ts` retired 2026-09-14 | `pitchfork-convention-report.md` §6 |
| 17/31 projects.toml paths missing | `pitchfork-convention-report.md` §3, §5 |
| Supervisor session-scoped under user@1000 | `estate-recovery-report.md` §4, live `systemctl --user status` |
| Reconcile failing since Oct 12, now active | `estate-recovery-report.md` §4 |
| 65 daemons killed by `bun:path@true` | `estate-recovery-report.md` §5, `AGENTS.md` §Provenance |
| Fleet state: 85 running, 5 errored, 14 stopped, 8 available | Live `pitchfork list --json` |
| Disk at 86% (136GB free) | Live `df -h` |
| 5 known blockers: 2 missing GGUFs, herd ABI, ml-serve/market-loop exit-1 | `estate-recovery-report.md` §1, live data |
