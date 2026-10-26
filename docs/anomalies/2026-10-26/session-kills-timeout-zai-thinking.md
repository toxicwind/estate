# 2026-10-26 — Session-kill forensics, tau timeout/thinking/zai fixes

## 1. "Why were my SSH and tau sessions killed?" — forensics

**Answer: nothing server-side killed them.** The SSH session (pts/4, 02:05–09:57)
ended with a clean **client-side close** (`Connection closed by 10.0.0.77 port
43394`, `session closed for user toxic` at 09:57:31 — `journalctl -u sshd`).
The tau session (pid 2380202) then recorded `reason: "sighup"` in its session
file the same second — stdin ended, tau got SIGHUP, exited. The client
(10.0.0.77) dropped the connection because the box had become unresponsive.

**The box was unresponsive because of a quickshell crash-loop since boot:**

- `quickshell-ii.service` (user unit, `Restart=always`, `RestartSec=2`) exec'd
  quickshell which aborted with `Failed to create wl_display (Connection
  refused)` → SIGABRT → systemd-coredump every ~2s (**NRestarts=15,261**,
  **951+ core dumps ≈ 2.7 GB written** today, boot-time loops recorded in
  `~/.local/state/quickshell/launch.log` since Oct 25 22:03Z).
- Root cause: **no toxic-owned Wayland display exists.** The machine sits at
  the SDDM **greeter** session (`seat0` = session c2, `sddm` uid 960, which is
  running the greeter's `Hyprland` at `/run/user/960/wayland-1`). toxic never
  logged in graphically; `/run/user/1000/wayland-1` is a stale socket file
  nothing listens on → every quickshell launch refused → abort loop.

**Fix (committed + live):**
- `ranch/shell/lib/qs-common.sh`: `qs_wayland_alive()` does a real unix-socket
  connect test; `qs_detect_env` picks the first *connectable* wayland socket,
  not the first leftover file.
- `ranch/shell/bin/qs-launch`: `--systemd` preflights the socket and **exits 0
  cleanly** when no display is reachable; detached mode refuses to launch.
- `quickshell-ii.service` (deploy + dots copies): `Restart=on-failure`.
- Verified: `systemctl --user start quickshell-ii.service` → inactive,
  `ExecMainStatus=0`, `Result=success`, no new coredumps, NRestarts frozen.

Pushed to `github.com/toxicwind/ranch` (main `80642f2e`, backup ref
`backup/main-2026-10-26`) and `github.com/toxicwind/estate-end4` (main
`abb1795`).

> **Environment note (not fixed — architect's):** the local `pens/ranch` clone
> is a broken/half-migrated shared checkout (`origin` → `pinax.git` does not
> contain the shell history, missing parent objects, `backup/ranch-pre-migration-*
> ` refs). The quickshell fix landed on the real `toxicwind/ranch` via a clean
> sandbox clone. Do not fight the local clone; use sandbox-merge.

## 2. The "ridiculous 300s" timeout — where and the fix

- `~/.tau/config.yml` had `streamFirstEventTimeoutSeconds: 300` and
  `streamIdleTimeoutSeconds: 120` (set 2026-09-22; schema default is **-1** =
  provider/env defaults, see `packages/coding-agent/src/config/settings-schema.ts`).
- Enforcement chain: `settings-stream-fn.ts` → `timeoutSecondsToMs` →
  `SimpleStreamOptions.streamFirstEventTimeoutMs` → `streamSimple` (provider
  layer). A hung provider left the UI waiting up to **5 minutes** before the
  first token watchdog fired.
- **Fix:** first-event 300→**60s**, idle 120→**30s** (committed to estate
  config). 0 disables the watchdog, -1 returns to provider defaults.
- Beware anomaly #1: reasoning + bounded `max_tokens` starves content — see §5.

## 3. zai "uselessly default" — root cause + fix

- Every session polled ZAI usage → `ZAI usage response invalid
  当前用户不存在coding plan` (500): the OAuth credential has **no coding plan**.
- Worse: `packages/catalog/src/models.json` (tau product catalog) contained
  **poisoned entries**:
  - `cerebras/zai-glm-4.6`, `cerebras/zai-glm-4.7` → provider **cerebras**,
    baseUrl `api.cerebras.ai/v1`, cost 0
  - `mistral/zai-glm-5-2`, `mistral/zai-glm-5-3` → provider **mistral**,
    `api.mistral.ai/v1`, cost 0
  GLM models do not run on those endpoints → every turn that selected them as
  the cost-minimizing default 401'd (`Wrong API Key`). Real GLM models live at
  `api.z.ai` under the `zai` provider (pi-ai `data/zai.json`).
- **Fix:** removed the 4 entries (tau repo, commit `20aa82f0c6`, work-ref
  pushed); `disabledProviders: [zai, cerebras]` in estate agent config
  (cerebras key 401s anyway). `compat/rules/providers/cerebras.kdl` +
  `taxonomy/glm.kdl` retained (defensive, harmless for nonexistent models).

## 4. thinking `auto` — how it works + shim plugin

- `auto` is a coding-agent sentinel (`AUTO_THINKING = "auto"`, tau-tui
  `thinking.ts`), parsed from `modelRoles` `:auto` suffix / `/thinking auto`.
- **Per turn**, `ModelControls.applyAutoThinkingLevel()` runs
  `classifyDifficulty` (`auto-thinking/classifier.ts`): a **judge model round
  trip** (4s abort budget, `#AUTO_THINKING_TIMEOUT_MS`) classifies the prompt
  into low..max via a ChoiceQuestion, then clamps via
  `clampAutoThinkingEffort` (ceiling `providers.autoThinkingMaxEffort`, default
  XHigh). `ultrathink` magic keyword bypasses the classifier.
- **Shim plugin** `extensions/thinking-auto-shim.ts` (estate config, committed):
  on `session_start` + `before_agent_start`, if `getThinkingLevel() === "auto"`
  it calls `setThinkingLevel(TAU_AUTO_THINK_SHIM_LEVEL || "low")`, which clears
  `#autoThinking` so the classifier never runs — deterministic effort, zero
  judge calls. Caveat: `ultrathink` bypass is inside the auto path, so it is
  suppressed while the shim forces a fixed level.

## 5. Mixture experiment (emergent) — auto-thinking effort strategies

Harness: `~/tmp/auto-think-mixture/harness.py` (6 prompts: 3 easy/3 hard ×
strategies off/low/high/oracle-auto, freeinference deepseek-v4-flash, judge
qwen3.6-35b). Results in `results.jsonl`; runs at max_tokens 400 and 2000.

**easy tasks (rename, one-liner bug, factual) — every strategy scores 5/5.**
Effort is irrelevant to quality; `off` is strictly cheapest (0 reasoning
tokens, ~450 ms vs 800–1000 ms for reasoning variants).

**hard tasks (cross-file debug, concurrency, ambiguous spec):**
- `high` (and `oracle-auto` = the perfect classifier upper bound): **zero
  content**. `reasoning_tokens=2000, completion_tokens=2000,
  finish_reason=length, content=""` at max_tokens=2000 — the model burns the
  entire window in reasoning/drafts and emits nothing. Same trap at 400
  (`reasoning_tokens≈400`). This is anomaly #1's reasoning-budget starvation
  reproduced live, at both budgets.
- `low`: content survives only sometimes (534–1681 reasoning tokens consumed),
  otherwise truncates → judge 0–4.
- `off`: the ONLY strategy that reliably produces usable content under a
  capped budget (scores 2–5).
- `reasoning_effort` ladder is weakly honored on freeinference (low often
  burns as many reasoning tokens as high).

**Emergent conclusions for tau's auto-thinking:**
1. The per-turn judge classifier (one extra model call + 4s budget per turn)
   optimizes a knob that is useless on easy prompts and actively harmful on
   hard ones under any capped `max_tokens` (budget starvation → empty
   replies). The 2026-10-26 run of this exact failure appears in every hard/
   high cell.
2. The shim plugin (§4) forcing a fixed level (default `low`, `off` for
   latency) removes the judge call AND the starvation path. `off` on
   deepseek-v4-flash is a capable fallback.
3. If adaptive effort is wanted, it is only sound with per-model
   content-safe budgets (≥2500 max_tokens for reasoning models — the estate's
   documented rule) AND after fixing `reasoning_effort` honoring; the ladder
   itself (Ares) only matters then.

## Anomalies table (D-2026-10-26)

|#|Anomaly|Essence|Fix status|
|---|---|---|---|
|10|Quickshell abort-loop on headless boots|Stale `/run/user/1000/wayland-*` socket + `Restart=always` → 15k restarts, core-dump I/O belt, killed SSH responsiveness|Fixed + pushed (ranch, end4)|
|11|Catalog poison: zai-glm under cerebras/mistral|GLM ids on wrong endpoints, cost 0 → default picks 401 every turn|Fixed (tau catalog) + providers disabled|
|12|ZAI usage-fetch poll spam|OAuth token without coding plan → 500 every ~3min|Disabled provider zai|
|13|Session-kill forensics|"Killed" sessions = client-side SSH close → tau SIGHUP, backstopped by #10's lag|Documented|