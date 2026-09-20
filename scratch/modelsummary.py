import subprocess, base64, json

REPO = "toxicwind/sovereign-projects"

# verify the models.yml commit
r = subprocess.run(
    ["gh", "api", f"repos/{REPO}/contents/.tau/models.yml?ref=main",
     "--jq", ".content"],
    capture_output=True, text=True, timeout=60)
txt = base64.b64decode(r.stdout.strip()).decode()
print("=== .tau/models.yml on origin/main now ===")
for line in txt.split("\n"):
    if "id:" in line:
        print(line)

SUMMARY = """# Fleet model audit — 2026-09-14

Live NIM probes via nvidia-nim-loader (fail-fast chat, "reply OK", max 16 tokens).
Times are wall-clock for the probe round-trip.

## Latency ranking (alive)

| model | status | latency |
|---|---|---|
| openai/gpt-oss-20b | ALIVE | 1.8s |
| nvidia/nemotron-3-nano-omni-30b-a3b-reasoning | ALIVE | 2.6s |
| nvidia/nemotron-3.5-lightning-30b-a3b | ALIVE (reasoning trace) | ~2s |
| z-ai/glm-5.3-flash | ALIVE | 9.2s |

## Dead (verified 2026-09-14)

| model | failure |
|---|---|
| nvidia/llama-3.1-nemotron-70b-instruct | 404 |
| nvidia/nemotron-nano-3-30b-a3b | 404 (410 EOL family) |
| nvidia/nemotron-3-super-120b-a12b | EOL 2026-10-03, 503s |
| nvidia/nemotron-3-ultra-550b-a55b | 503 overloaded |
| moonshotai/kimi-k2.6 | 404 today (nondeterministic across runs) |

## Switches committed to toxicwind/sovereign-projects main

1. `8af98fdb8f` (already on main before this audit): tau nvidia auth KDL
   validation model `nvidia/llama-3.1-nemotron-70b-instruct` (404)
   -> `openai/gpt-oss-20b`; refreshed stale GLM ids in providers/nvidia.kdl.
2. `2c63d19a3f8b` (this audit): `.tau/models.yml`
   - `nvidia/nemotron-3-super-120b-a12b` -> `openai/gpt-oss-20b`
   - `nvidia/nemotron-3-ultra-550b-a55b` -> `z-ai/glm-5.3-flash`
   (kept: Qwen3.6-35B/27B-NVFP4 local :25100 entries, lightning-30b-a3b, nano-omni-reasoning — all live or local)

## Audited, left alone (with reason)

- `sovereign/config/herd.yaml`: all local GGUF paths (/home/toxic/models) — not NIM.
- `sovereign/config/llama-swap/config.yaml`: `nvidia/nemotron-3-ultra-550b-a55b`
  entry proxies to sovereign-router (TS, currently parked, no listener) with a
  503 model — doubly dead. Left for the mesh-cutover worker: the right fix
  depends on the open router-deploy-vs-park decision. Recommend: point it at
  `openai/gpt-oss-20b` if the router is deployed, else remove the entry.
- `config/llama-swap.yaml` is now a symlink -> `herd.yaml` (mesh worker), so
  `config/llama-swap/config.yaml` is legacy but still referenced by docs/scripts.
- `/home/toxic/herd` repo: no NIM refs in prod files.
- `/home/toxic/projects/openfang`: multi-provider catalog (Google/Gemini
  defaults in wizard); no dead NIM defaults found.
- tau `providers/nvidia.kdl` compat metadata: all listed ids alive or
  catalog-only (no defaults to switch).

## Recommendation

Default fast model fleet-wide: `openai/gpt-oss-20b` (1.8s, cheapest fast).
Reasoning-heavy: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` (2.6s).
Re-probe before trusting `moonshotai/kimi-k2.6` (flaps 404/200 across runs).
"""

open("/home/toxic/model-audit-20260914.md", "w").write(SUMMARY)
print("summary written to /home/toxic/model-audit-20260914.md")
