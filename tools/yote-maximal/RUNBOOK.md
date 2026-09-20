# yote-maximal runbook — herd tuning changes (2026-09-20)
Live config: /home/toxic/sovereign/config/herd.yaml
Snapshot before any change: cp herd.yaml herd.yaml.bak.<date>-<label>
Validate: source /home/toxic/.secrets && llama-swap -validate -config <file>
  (binary: /home/toxic/projects/sovereign-projects/sovereign-swap/build/llama-swap)
Restart (REQUIRED for preload/cmd changes; --watch-config hot-reloads the rest):
  /home/toxic/.local/share/mise/installs/pitchfork/2.25.0/pitchfork restart herd
Verify after restart (every time, in order):
  1. curl -s http://127.0.0.1:25100/health            -> OK
  2. /v1/models count == 199
  3. /running shows preloaded models (exaone-1.2b-iq4xs, qwen-flash-128k)
  4. probe: warm TTFT on preloaded model < 1s (no cold load)
  5. nvidia-smi: per-process VRAM sane (exaone --parallel 4 ~5GB max)
Rollback (ALWAYS ready before restart):
  cp /home/toxic/sovereign/config/herd.yaml.bak.20260920-yotemaximal /home/toxic/sovereign/config/herd.yaml
  /home/toxic/.local/share/mise/installs/pitchfork/2.25.0/pitchfork restart herd
NEVER: touch :25104 (router, sibling track), kill squawk, touch 443/tailscaled.
Tools:
  /home/toxic/sovereign/tools/herd-ranker.py  - full herd sweep -> data/herd-ranker/ranked.{json,md}
  /home/toxic/sovereign/tools/herd-burst.py <model> <N> [max_tokens] - burst A/B
Change A (applied 2026-09-20): preload [exaone-1.2b-iq4xs, qwen-flash-128k], ttl:0 on exaone-1.2b-iq4xs
Change B (applied 2026-09-20): SRV_BASE_P4 (--parallel 4) on 5 exaone 1.2B models
