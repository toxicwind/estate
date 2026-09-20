# MODEL-MAX — herd model measurement

Sweep harness that measures every model exposed by the herd gateway
(llama-swap on yote `127.0.0.1:25100`) with real completions. No advertised
catalog entries, no guessed RPM — every `healthy=true` is an observed
completion.

## One-command re-run (on yote)

```bash
cd /home/toxic/sovereign/projects/model-max
python3 sweep.py --phase=all        # liveness + deep + report
```

Phases can run separately; both checkpoint after every model, so killing and
re-running resumes where it left off:

```bash
python3 sweep.py --phase=liveness   # 1 completion/model, fail-fast
python3 sweep.py --phase=deep       # streaming TTFT/TPS/RPM on healthy only
python3 sweep.py --phase=report     # writes model-health.json
python3 sweep.py --phase=liveness --fresh          # ignore checkpoints
python3 sweep.py --phase=liveness --models=a,b     # subset
python3 sweep.py --phase=liveness --max-tokens=256 --workers-cloud=1
```

## What it measures

**Liveness (all models):** one real `/v1/chat/completions` call per model.
Records HTTP status, wall latency, and — critically — *semantic* failures:
HTTP 200 bodies carrying error text, canned "not enough credits" notices,
and empty completions are failures, not health. Models that return empty
with `finish=length` are re-probed with a larger token budget (they're
usually reasoning models, not dead routes); 429s are re-probed serially to
distinguish rate-limit from death.

**Deep (healthy only):** 6 sequential streaming samples + one 3-way burst.
Measures TTFT, total latency, tokens/sec, and an *observed* valid-RPM
(successful completions per minute during the probe window).

**Report:** writes `/home/toxic/sovereign/data/model-health.json` — the
artifact consumed by herd racing, `robust.py`, and Tau. Schema is documented
at the top of that file (`_schema` key).

## Layout

- `sweep.py` — the harness (stdlib only, no deps)
- `model-ids.json` — model list from the sweep run
- `phase1.json` / `phase2.json` — checkpoints (resume state)
- `sweep-*.log` — run logs
- `.venv/` — GuideLLM venv (for deep load benchmarks on top candidates)

## Lessons baked in

- The herd's `/v1/models` set is **fluid** (peers come and go); the sweep
  records what was exposed at sweep time. Counts have varied 99–102.
- `--watch-config` + a bad `${env.VAR}` **kills the herd** (llama-swap exits
  on failed reload instead of keeping the old config). Never edit herd.yaml
  to reference an env var the pitchfork daemon doesn't have.
- GuideLLM lives here for proper load benchmarks of the top candidates;
  the custom prober handles liveness/semantic triage where GuideLLM doesn't fit.
