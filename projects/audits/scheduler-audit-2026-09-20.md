# Scheduler audit — the three overnight "suspend notices" on yote

**Date:** 2026-09-20 (MDT)
**Box:** yote (awrawr-pc / bridge box, CachyOS/Arch, systemd 261)
**Auditor:** scheduler-audit (ember)
**Status:** Complete — verdict with evidence
**File:** `/home/toxic/sovereign/projects/audits/scheduler-audit-2026-09-20.md`

---

## 0. Verdict (read this first)

**yote did not suspend. Not once. Not three times.**

- **One genuine suspend broadcast happened** — at `2026-09-20 00:44:53 MDT`, from the physical-console (`tty1`) session, verbatim:
  `Broadcast message from toxic@awrawr-pc on tty1 (Sun 2026-09-20 00:44:53 MDT):` / `The system will suspend now!`
- **The suspend never executed.** systemd logged the wall, then refused the operation because `suspend.target` is masked (masked since 2026-03-29). Decisive proof: `/proc/uptime` (monotonic clock, which freezes during S3 suspend) shows a **1-second deficit** against wall-clock time over 2 days of uptime. Any real suspend — even a brief one — would leave a multi-second gap.
- **The three reported timestamps** (`01:37:41`, `02:36:28`, `03:15:12 MDT`) have **no matching suspend broadcast in any preserved record**. They correlate to the second with overnight scheduler/watchdog events during three real incidents (bridge outage, canary rollback, bridge 401s) — the lane going down, not the box going to sleep.
- **Correction:** the fleet message claiming "the box suspended 3x overnight" (fleet seq 10697, 2026-09-20 08:20:49 MDT, from ember) is **retracted** — it was an unverified causal claim, contradicted by the monotonic-clock test.
- **Correction:** the four sleep-target masks (`sleep`/`suspend`/`hibernate`/`hybrid-sleep`) were **not** installed this morning in response to the incident. They date to **2026-03-29 20:40** — six months of prior hardening. They are exactly what turned the 00:44:53 suspend initiation into a harmless broadcast. **Recommendation: keep them.**
- **Likely reconstruction:** Chris saw (or sat near) the genuine 00:44:53 wall broadcast during the night's bridge work; the three later timestamps mark when the *lane* dropped during three distinct overnight incidents. An earlier agent conflated "lane down 3x" with "box suspended 3x".

---

## 1. What Chris actually saw

### 1.1 The one verified suspend notice

Preserved verbatim in `~/.bash_history` (lines 1342–1344), captured when the broadcast printed into a terminal during a bridge-repair session:

```
Broadcast message from toxic@awrawr-pc on tty1 (Sun 2026-09-20 00:44:53 MDT):

The system will suspend now!
```

This is systemd-logind's canonical suspend wall: the `wall(1)`-style header (`Broadcast message from USER@HOST on TTY (DATE):`) is composed by systemd's shared wall implementation (`src/shared/wall.c`), and the body `The system will suspend now!` is emitted by `systemd-logind` when a sleep operation is initiated through it. Independent journal excerpts from other systems show the identical logind line (`systemd-logind[1071]: The system will suspend now!`) immediately preceding a real suspend sequence (`Starting System Suspend…` → `kernel: PM: suspend entry (deep)`).

**Attribution:** the header records the *caller's* session — `toxic@awrawr-pc on tty1`, the physical-console session (toxic has been logged in on `tty1` continuously since the Sep-18 boot). The suspend was initiated from the local console session at 00:44:53. (No claim is made here about which fingers were on the keyboard.)

### 1.2 What happened next: wall fired, suspend refused

The suspend **did not happen**. Reproduced the exact mechanism on yote itself at 15:07:01 MDT today (`systemctl suspend` with the target masked). yote's own journal shows the three-line pattern:

```
Sep 20 15:07:01 awrawr-pc systemd-logind[793]: suspend requested from client PID 1641539 ('systemctl') (unit user@1000.service)...
Sep 20 15:07:01 awrawr-pc systemd-logind[793]: The system will suspend now!
Sep 20 15:07:01 awrawr-pc systemd-logind[793]: Unit suspend.target is masked, refusing operation.
```

On systemd 261 (yote's build, `261.2-1-arch`), logind emits the wall message **first**, then refuses the masked unit. So the 00:44:53 event was: *initiation → broadcast → refusal*. The broadcast is real; the suspend is not. This is the entire mystery in three lines.

(The 15:07:01 reproduction emitted one wall broadcast to all logged-in terminals. Harmless, transient, and it is the evidence for §1.2.)

### 1.3 Proof no suspend occurred (four independent lines)

1. **Monotonic clock (decisive).** `/proc/uptime` is driven by `CLOCK_MONOTONIC`, which *freezes* during S3 suspend. Measured 2026-09-20 15:03:13 MDT:
   - `uptime_s = 173495.70`, wall time since boot (`2026-09-18 14:51:37`) = `173496 s` → **deficit 1 s** over 2 days. A single suspend/resume cycle takes several seconds minimum (freeze → suspend → resume → thaw). Conclusion: the monotonic clock never stopped → **no suspend of any duration occurred since boot**.
2. **Session continuity.** `last -x` shows SSH sessions from `10.0.0.77` (`pts/2`, `pts/6`, `pts/7`) logged in continuously across the entire night (22:32/23:33/23:44 → 09:11). No gap, no re-login.
3. **No PM traces.** `dmesg` contains zero `PM: suspend entry` / `systemd-sleep` lines (current buffer is flooded with `nft-drop` spam, but a suspend would also have left journal traces — see 4).
4. **Power policy.** `/etc/systemd/logind.conf` sets `HandleLidSwitch=ignore` and `IdleAction=ignore`; no idle/lid path can initiate sleep. `smartd` disabled. No cron/at on yote at all (see §4).

### 1.4 The journal gap (honest limitation)

The persistent journal on yote rotates aggressively (≈43.7 MB total, heavy `nft-drop` LOG spam). Retained entries at audit time began only ~13:16–13:24 MDT — the 00:00–04:00 window is gone. So the *absence* of 00:44:53 journal lines today proves nothing by itself; the proof rests on the monotonic clock, the history-preserved broadcast text, the mask symlinks, and today's live reproduction of the identical three-line pattern.

---

## 2. The three reported timestamps

Reported times: `01:37:41`, `02:36:28`, `03:15:12 MDT`.

**Finding: no suspend broadcast matches any of them in any preserved record** — not in `~/.bash_history` (single broadcast: 00:44:53), not in squawk fleet/lead channels, not in the canary runlog, not in the daily memory log. What *does* match, to the second, are scheduler/watchdog events from the night's three real incidents:

| Reported | Nearest scheduler event | Delta | Context |
|---|---|---|---|
| 01:37:41 | Late `kimi-auto-canary-judge` handoff **ran 01:37:40** (phase=0 idle HOLD, delivered out of order) | +1 s | Aftermath of the 01:24–01:35 canary ROLLBACK incident; bridge had just recovered at 01:36 |
| 02:36:28 | `yote-connector-watch` run **02:36:32** (healthy: `ok:true`, both lanes up) | −4 s | 1m46s after squawk fleet seq 10627 (`agent joined: nvidia-kimi-fuzz`, 02:34:42) |
| 03:15:12 | `kimi-auto-canary-judge` tick **03:14:19** + retry window (~53 s → ~03:15:12) | ~0 s | Inside the genuine bridge **401 outage** (judge 401s at 03:04:19 / 03:09:19; connector-watch failed 03:16:32: `all lanes down: HTTP 401`) |

These are correlations, stated as correlations — not identifications. No preserved notice text ties any of the three times to a suspend broadcast, and the only *verified* suspend broadcast is 00:44:53.

**Reading:** each timestamp sits inside a *lane-down* episode, not a *box-down* episode. The night's actual incidents were:

1. **00:45–01:36 — bridge down (hatch-side).** Runtime overlay refused direct TCP (`other_tcp` gate). Watchdogs failed fast; yote-side daemons (pitchfork, sidecar) unaffected. Recovered 01:36 (`ws_daemon.py` 3 procs); bridge-watchdog HEALTHY 01:38.
2. **01:24–01:35 — canary ROLLBACK.** `canary-exec ROLLBACK EXECUTED` fleet pages seq 10435 (01:24:24 MDT) and 10438 (01:29:25 MDT); rollback completed 01:30:33–35; judge confirmed HOLD/phase=0 idle from 01:39.
3. **03:04 → morning — bridge 401 outage (genuine).** Judge ticks 03:04:19 / 03:09:19 / 03:14:19 / 03:29:19 all `HTTP 401 from bridge: unauthorized`; `yote-connector-watch` failed 03:16:32 (`all lanes down: HTTP 401 from bridge: unauthorized; stale process killed, connector restarted; bridge still down — token mismatch`); `~/.cache/bridge-outage-401` sentinel written.

Three lane-down episodes overnight → mis-narrated by an earlier agent as "the box suspended 3x overnight" (fleet seq 10697, 08:20:49 MDT). That message is hereby corrected: the box never suspended; the lane dropped three times for three different, documented reasons.

---

## 3. Why the word "suspend" stuck

Reasonable people saw three things and fused them:

1. A **real** suspend wall broadcast at 00:44:53 ("The system will suspend now!") — alarming text, seen on terminals during the night's bridge work.
2. The lane dropping **three times** overnight at roughly the reported times.
3. An agent (ember, 08:20:49) asserting "the box suspended 3x overnight and that's what kept dropping the lane" — stated as fact, without the monotonic-clock check.

(1) is genuine evidence of a suspend *initiation* (from the console session) — but the initiation died on the masked target. (2) is genuine evidence of *lane* failures — but the causes are documented and unrelated to power state. (3) was the unreliable narrator: a causal claim with no verification, now retracted.

---

## 4. Yote scheduler inventory (the "who could have sent a notice" sweep)

### 4.1 Classic schedulers: absent

- No `/etc/crontab`, no `/etc/cron.d/`, no `/var/spool/cron/` — cron is not installed.
- `atq` not installed — atd ruled out.
- **Conclusion: no yote-local cron/at source exists for any of the three timestamps.**

### 4.2 System timers (10)

| Timer | Schedule | Fired near the timestamps? |
|---|---|---|
| `snapper-cleanup.timer` | distro default | No |
| `systemd-tmpfiles-clean.timer` | distro default | No |
| `shadow.timer` | distro default | No |
| `plocate-updatedb.timer` | distro default | No |
| `logrotate.timer` | distro default | No |
| `fstrim.timer` | distro default | No |
| `man-db.timer` | distro default | No |
| `archlinux-keyring-wkd-sync.timer` | distro default | No |
| `cachyos-rate-mirrors.timer` | distro default | No |
| `hw-audit.timer` | `OnCalendar=03:17` (+`RandomizedDelaySec=600`) | Fired **03:17:22** — 2m10s *after* the third timestamp; runs `/home/toxic/hw-audit.sh` + `hw-watchdog.py` (hardware inventory, no terminal output) |

**None fired at 01:37:41, 02:36:28, or 03:15:12.** The closest (`hw-audit` at 03:17:22) is a JSONL inventory writer — no wall, no broadcast, no terminal writes.

### 4.3 User timers (toxic, lingering enabled)

| Timer | Last fired (audit day) | Near timestamps? |
|---|---|---|
| `awrawr-mcp-audit-export.timer` | 00:00:02 | No |
| `refusal-hunt-nightly.timer` | 03:00:00 | No |
| `gemini-sdk-refresh.timer` | 03:32:16 | No |
| `depend-refire.timer` / `squawk-watchdog.timer` | frequent (sweeps) | No second-precision match |

**None match.** No user timer writes to terminals.

### 4.4 Broadcast-capable paths on yote: audited

- **journald:** default config (`[Journal]` only, no `ForwardToWall` override, no drop-ins) — journald does not wall on yote. (Reference: the 2026-04 oss-security advisory on journald emergency messages being wall-broadcast, and the Arch discussion of `ForwardToWall` — neither applies; yote is default-off.)
- **Direct `wall(1)` callers:** narrow source scan of core sovereign scripts and the canary tree found no `wall`/`utmp`/`broadcast` callers (the `wall` hits in `analyze.py`/`resolver.py` are "wall-clock time" variables). `systemd-cat`/emergency-priority logging paths: no evidence.
- **logind:** `HandleLidSwitch=ignore`, `IdleAction=ignore` — no automatic sleep initiation. The *manual* initiation path (D-Bus `Suspend()`) is live but neutered by the masks (proven §1.2).

---

## 5. Hatch scheduler inventory

Fresh `cron.list` 2026-09-20 (all enabled unless noted):

- **5-minute:** `bridge-watchdog`, `kimi-auto-canary-judge`, `squawk-monitor`, `swarm-watchdog`, `yote-connector-watch` (+ disabled `audit-bridge-watch`)
- **3-minute:** `progress-watchdog`
- **30-minute:** `heartbeat`
- **Hourly:** `deterministic-doctor` (system), 24× `feed-pulse-*` (system)
- **Daily:** `agentic-feature-tour` · **Weekly:** `profile-image` (system)

Relevant run evidence for the night:

- `yote-connector-watch`: 02:36:32 healthy (`ok:true`); 03:11:32 healthy (local daemon); **03:16:32 failed** — `ok:false`, `all lanes down: HTTP 401 from bridge: unauthorized`; killed stale process, restarted connector; bridge still down (token mismatch). Full export: 158 runs at `/home/hatch/workspace/agents/54db60f5-ecae-4611-8d25-b37b913c7737/tool-output/cron.runs-call_01a0c09ee183739bb8da89b150a17dbf.json`.
- `kimi-auto-canary-judge`: ticks at :19 past each 5 min; 03:04:19 / 03:09:19 / 03:14:19 / 03:29:19 all 401; runlog at `/home/hatch/workspace/canary/runlog.md`.
- `bridge-watchdog`: healthy 01:38, 01:43, 02:33, 02:38; outage detection during 03:08–03:12 (401, genuine).

None of these jobs emits terminal wall broadcasts on yote — they are hatch-side agents. They are listed here because their *run records* are the second-precision anchors for §2's correlation table.

---

## 6. Hypotheses, compared

| # | Hypothesis | Evidence for | Evidence against | Verdict |
|---|---|---|---|---|
| H1 | Hatch scheduler/run notices were miscalled "suspend notices" | Second-precision matches at all three timestamps (§2); ~96+/day background agent runs; no suspend evidence | No preserved notice *text* at those times; scheduler jobs don't wall to yote terminals | **Plausible, unproven** — best fit for the three timestamps |
| H2 | A real terminal wall broadcast unrelated to power state | systemd/journald/`wall` *can* write to terminals (agentum issue: wall bypasses `mesg n`, corrupts TUI panes) | Journal window for the period is gone; no matching timer/cron/at; journald `ForwardToWall` default-off; no caller found | **Possible but unsupported** |
| H3 | The 00:44:53 suspend broadcast + three lane-down episodes were fused into "suspended 3x" | Verbatim broadcast preserved; three documented lane incidents; monotonic clock disproves actual suspend; earlier agent's claim matches this fusion exactly | Requires the earlier narrator to have conflated aggressively | **Strongest overall** — explains both the word "suspend" and the number three |
| H4 | Another host/app notification mistaken for yote-local | Persistent SSH sessions from 10.0.0.77; Tailscale/Funnel in play | No evidence for any specific source | **Plausible, unproven** |
| H5 | The box actually suspended 3x | — (none) | Monotonic-clock deficit 1 s; unbroken SSH sessions; masked targets; no PM traces | **Disproven** |

**Do not invent Chris's intended word.** The safest statement: the three timestamps mark *observed lane-down episodes*, and the one verified "suspend notice" was a real-but-refused suspend initiation at 00:44:53.

---

## 7. The sleep-target masks: keep them

- The masks (`sleep.target`, `suspend.target`, `hibernate.target`, `hybrid-sleep.target` → `/dev/null`) date to **2026-03-29 20:40** — they are six-month-old hardening, not this morning's reaction.
- They are **exactly** what converted the 00:44:53 console suspend initiation into a no-op (proven by today's reproduction: wall, then `Unit suspend.target is masked, refusing operation.`).
- logind already ignores lid-switch and idle (`HandleLidSwitch=ignore`, `IdleAction=ignore`), so the masks are *redundant* for automatic initiation — but they are the **only** thing that stops a *manual* `systemctl suspend` from the console (as happened at 00:44:53).
- Steelman against keeping: they don't stop a root write to `/sys/power/state`, a BMC-initiated suspend, or a hypervisor suspend; they convert a dangerous action into a scary-but-harmless broadcast. Keeping them is still correct for an always-on server: the failure mode they produce (loud refusal) is strictly better than the alternative (silent sleep).
- **Recommendation: keep the masks; add monitoring, not more masking.** A one-line canary — e.g. a 5-minute check that the four symlinks still point at `/dev/null` and that no `PM: suspend entry` appears in `dmesg` — would have settled this morning's debate in seconds. (Observability first, hardening second; this time we had the hardening and lacked the observability.)

---

## 8. Recommendations

1. **Retract the "suspended 3x" claim** in fleet (done in this audit; point Chris here, not at the 08:20:49 message).
2. **Keep the four sleep-target masks.** They demonstrably saved the box at 00:44:53.
3. **Add a suspend-canary:** monitor the four mask symlinks + watch for `PM: suspend entry` in the kernel log; alert on change. Cheap, decisive, ends future debates before they start.
4. **Fix the journal rotation pressure:** the `nft-drop` LOG spam is flooding both the kernel ring buffer and the persistent journal (≈43.7 MB, hours of retention). Rate-limit the nft log rule or move it to a separate log — tonight's forensics were needlessly hamstrung by a rotated-away evidence window.
5. **Note the 00:44:53 console initiation for Chris:** something on the physical console (`tty1`) invoked suspend at 00:44:53. If that wasn't Chris, find out what it was (hypridle holds a sleep *delay* inhibitor and manages idle sleep on the Hyprland session — worth one look at its config).
6. **No scheduler changes needed.** No yote timer, cron, or at job is implicated; hatch schedules are behaving as designed.

---

## 9. References

- systemd wall delivery: [`src/shared/wall.c`](https://github.com/systemd/systemd/blob/d0168f4d/src/shared/wall.c) — composes the `Broadcast message from USER@HOST on TTY (DATE):` header.
- systemd-logind suspend path: [`src/login/logind-dbus.c`](https://raw.githubusercontent.com/systemd/systemd/main/src/login/logind-dbus.c) — `method_suspend` → `method_do_shutdown_or_sleep(HANDLE_SUSPEND)`; masked-unit refusal path (`Unit %s is %s, refusing operation.`); wall-message timer captures caller tty/uid (hence `toxic@awrawr-pc on tty1`).
- Canonical real-suspend journal sequence (`The system will suspend now!` → `Starting System Suspend…` → `PM: suspend entry (deep)`): [blakerain.com — spurious wakes](https://github.com/blakerain/blakerain.com/blob/HEAD/content/blog/spurious-wakes-logitech-receiver/index.md); [dixonsolutions — always-on](https://github.com/dixonsolutions/protun-unblocked/blob/HEAD/docs/always-on.md).
- Wall broadcasts corrupt terminal UIs, bypass `mesg n`: [agentum#20](https://github.com/mateocerquetella/agentum/issues/20).
- `systemctl suspend` vs `rtcwake -m mem`: only the logind path emits the wall: [karanshukla/wildcat-lake-linux](https://github.com/karanshukla/wildcat-lake-linux) (s0ix-never-entered notes).
- logind power policy: [logind.conf(5)](https://www.freedesktop.org/software/systemd/man/latest/logind.conf.html) (`HandleLidSwitch=`, `IdleAction=`, inhibitor semantics); [inhibit docs](https://www.freedesktop.org/wiki/Software/systemd/inhibit/) (`PrepareForSleep`, delay locks); [org.freedesktop.login1](https://www.freedesktop.org/software/systemd/man/latest/org.freedesktop.login1.html).
- journald wall-broadcast advisory (2026-04): [oss-security 2026/04/08/1](https://openwall.com/lists/oss-security/2026/04/08/1); [Arch: stop journald broadcast messages](https://archlinuxhacks.wordpress.com/stop-sending-journald-broadcast-messages/).
- systemd shutdown wall-message issue: [systemd#35246](https://github.com/systemd/systemd/issues/35246); wall delivery: [systemd#3700](https://github.com/systemd/systemd/issues/3700).

---

## 10. Evidence log (what was checked, what was found)

| Check | Result |
|---|---|
| `~/.bash_history` for broadcast text | **Found:** verbatim 00:44:53 suspend wall (lines 1342–1344); the *only* broadcast in history |
| `/proc/uptime` vs wall clock | Deficit **1 s** over 2 days → no suspend |
| `last -x` | No suspend/shutdown/reboot; SSH sessions continuous |
| `dmesg` PM traces | Zero (buffer flooded by nft-drop spam) |
| Journal 00:00–04:00 window | Rotated away (retention starts ~13:16–13:24) |
| `/etc/systemd/logind.conf` | `HandleLidSwitch=ignore`, `IdleAction=ignore` |
| Sleep-target masks | Dated **2026-03-29 20:40** (pre-existing) |
| `systemctl suspend` reproduction (15:07:01) | Wall, then `Unit suspend.target is masked, refusing operation.` — mechanism proven |
| yote cron/at | Absent (not installed) |
| yote system timers (10) | None fired at the three timestamps |
| yote user timers (5) | None match |
| journald `ForwardToWall` | Default (off) — no drop-ins |
| `wall(1)` callers in sovereign/canary scripts | None found |
| Squawk fleet/lead at the three timestamps | No suspend notices (nearest: agent-joined 02:34:42) |
| Canary runlog / memory log | ROLLBACK pages 01:24:24/01:29:25; 401s from 03:04:19; no suspend text |
| Hatch `cron.list` | Inventoried (§5); run records anchor §2 correlations |
| `systemd-inhibit --list` | rtkit, upowerd, hypridle (delay) — none block, all delay-only |

## 11. Corrections to prior claims (unreliable-narrator ledger)

1. **"The box suspended 3x overnight"** (fleet seq 10697, 08:20:49, ember) — **false**, retracted. Monotonic-clock test disproves any suspend.
2. **"The four masks were installed this morning as the fix"** — **false**. Dated 2026-03-29 20:40; pre-existing hardening that *worked*.
3. **"Fleet page seq 10603 at 01:37:35 about a ROLLBACK false alarm"** (earlier audit notes) — **false**. Seq 10603 is timestamped 02:03:46 MDT and concerns auction assignment. The real ROLLBACK pages are seq 10435 (01:24:24) and 10438 (01:29:25).
4. **`yote-connector-watch` "failed with 401 at 03:11:32"** (implied by earlier notes) — **imprecise**. 03:11:32 succeeded (local daemon healthy); the genuine lane failure recorded at **03:16:32**. The 401s were seen by the canary judge from **03:04:19**.

---

*Audit complete. No shared files other than this document were created or modified; no daemons were killed. The single `systemctl suspend` reproduction at 15:07:01 was transient (wall broadcast only, refused by the mask) and is documented in §1.2.*
