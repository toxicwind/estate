# ipnext / avocado model routes — findings 2026-09-30

Chris's overnight ask: run things on /home/toxic, keep binaries+web on avocado,
try launching new tasks on other avocado models, track ipnext + weirdness.

## What ipnext is

**ipnext is the inference substrate's model provider family** — the route namespace
for agent cognition. NOT "up next". Every agent row in the Hatch DB carries its
route in `agent.agents.model`; browser tasks carry
`runtime.browser_tasks.requester_model` / `requester_effective_model`.

## Live routes (verified 2026-09-30 ~12:40 GMT)

- `ipnext/avocado-5.16-v4` — EVERYTHING current. 20,250 agent rows, all of them.
  Confirmed three ways: hatch binary strings ("falling back to avocado" +
  "ipnext/avocado-5.16-v4"), `agent.agents` GROUP BY, and this session's row.
- `ipnext/avocado-5.14` — 2 agent rows, legacy.

## Candidate routes found in the hatch binary (dormant — never selected)

Extracted from `/opt/hatch/bin/hatch` strings. These exist as code references;
authd has never served any of them (per the DB):

- ipnext/avocado-5.11, 5.13, 5.13b, 5.14, 5.14.1.cm1, 5.14.1.v2, 5.14.2,
  5.14-load-test, 5.14-sglang, 5.15, 5.16-v0, 5.16-v1, 5.16-v2, 5.16-v3,
  avocado-pro-max, avocado-9b-voice, avocado-9b-voice-staging
- Non-avocado ipnext routes: `ipnext/kimi-k3`, `ipnext/glm-5.2`,
  `ipnext_responses/avocado-5.14-load-test`
- Provider namespaces seen: IPNEXT, AVOCADO, SGLANG, GLM, CODEX, FIREWORKS,
  OPENAI, AZURE. Plus "IPNext-wire".

## Can we launch tasks on other avocado models? — No, via supported surfaces

Checked every spawn surface; none exposes a model choice. All new tasks ride
the session's model (5.16-v4):

- `subagent.spawn` — params are message/items/scope only. No model.
- `workflow` `agent(prompt, options)` — options are key/label/phase/timeoutMs/
  schema only. No model.
- `worker.*` — only `respond_with_user_input`. No spawning at all.
- `browser.spawn_task` — model is recorded (requester_model), not chosen.

## The override mechanism (exists, not reachable from here)

The binary has a real model-override path, read by the daemon/authd at
selection time — NOT settable from tool calls:

- Env var `JARVIS_MODEL_ID_OVERRIDE` ("using model override because authd
  selection is not aligned with requested target").
- Selection is per-purpose (`SYSTEM_PURPOSES` rows: main, compaction, memory
  flush, telemetry judging, voice, ...). Unknown purpose → "using the default
  model at Main tier".
- Unknown override values are ignored ("ignoring unknown model override");
  invalid authd routes fall back to bare `avocado`
  ("authd returned an invalid model selection route; falling back to avocado").
- The daemon (PID 67, host-side) env is not writable from the cell, so this
  stays a platform-side knob. If Chris ever wants a different avocado on a
  lane, that's where it lives.

## Yote-conn bridge + fleet bus verified before sleep

- squawk fleet: live, traffic flowing (posts within minutes).
- `yote-conn exec` → ok on awrawr-pc.
- Binaries/services run on /home/toxic (yote) under Chris's standing
  autonomous-operation order (2026-09-20). Agent cognition stays on the
  avocado (Hatch) substrate by design.

## Overnight watch

- Runonce cron `overnight-watch-morning-brief` enabled, fires ~09:11 MDT
  2026-09-30: new ipnext versions vs this baseline, fleet completions/anomalies,
  blocked-on-Chris items, estate health, up-next queue.
- Baseline for "new ipnext version" detection: {5.16-v4, 5.14} — anything else
  appearing in `agent.agents.model` is the anomaly to flag.

## See also

- [Avocado model family — what we can verify (2026-09-30)](avocado-model-family-2026-09-30.md) — full route/version map, knobs, quality notes.
- [Hatch binary decompose](../hatch-binary/README.md) — modular binary investigation index.
