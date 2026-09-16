#!/usr/bin/env bash
# Short llama-bench per fork using LD_* from forks.json (llama-swap macros SSOT).
# Does NOT run 27B at max context.
set -euo pipefail
ROOT="${SOVEREIGN_ROOT:-/home/toxic/sovereign}"
FLEET="$ROOT/tools/fleet"
SCRATCH="${SCRATCH:-/tmp/grok-goal-272520044418/implementer/bench}"
mkdir -p "$SCRATCH" "$FLEET/results"

cd "$ROOT"
bun run "$FLEET/extract_forks.ts"
FORKS_JSON="$FLEET/forks.json"

# Prefer tiny model for gate bench
MODEL_DIR=$(python3 -c "import json;print(json.load(open('$FORKS_JSON'))['MODEL_DIR'])")
GGUF=""
for cand in \
  "$MODEL_DIR/EXAONE-4.0-1.2B-Q4_K_M.gguf" \
  "$MODEL_DIR/Qwen2.5-1.5B-Draft-Q8_0.gguf" \
  /home/toxic/models/EXAONE-4.0-1.2B-Q4_K_M.gguf \
  /home/toxic/models/Qwen2.5-1.5B-Draft-Q8_0.gguf; do
  if [[ -f "$cand" ]]; then GGUF="$cand"; break; fi
done
if [[ -z "$GGUF" ]]; then
  GGUF=$(ls "$MODEL_DIR"/*1.5B*.gguf "$MODEL_DIR"/*1.2B*.gguf 2>/dev/null | head -1 || true)
fi
if [[ -z "$GGUF" || ! -f "$GGUF" ]]; then
  echo "error: no small GGUF for gate bench (avoid 27B)" >&2
  exit 1
fi
echo "GGUF=$GGUF"

python3 - "$FORKS_JSON" "$GGUF" "$SCRATCH" "$FLEET/results" <<'PY'
import json, os, subprocess, time, sys
from pathlib import Path

forks_path, gguf, scratch, results = sys.argv[1:5]
data = json.load(open(forks_path))
out = {"gguf": gguf, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "forks": {}}

# short prompt/gen — context-important but small
# llama-bench: -p prompt tokens -n gen tokens -r reps
for name, f in data["forks"].items():
    bin_path = f.get("bin_resolved") or f.get("bin")
    ld = f.get("ld") or ""
    bench = f.get("bench")
    rec = {"bin": bin_path, "ld": ld, "bench": bench, "ok": False}
    if not bin_path or not os.path.isfile(bin_path):
        rec["error"] = "missing bin"
        out["forks"][name] = rec
        continue
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = ld + (":" + env["LD_LIBRARY_PATH"] if env.get("LD_LIBRARY_PATH") else "")
    # help lines (ctx flags sample)
    try:
        h = subprocess.run([bin_path, "--help"], env=env, capture_output=True, text=True, timeout=15)
        help_txt = (h.stdout or "") + (h.stderr or "")
        Path(scratch, f"help-{name}-server.txt").write_text(help_txt)
        rec["help_lines"] = len(help_txt.splitlines())
        rec["help_has_ctx"] = any(k in help_txt.lower() for k in ["ctx-size", "context", "-c,"])
    except Exception as e:
        rec["help_error"] = str(e)
    if bench and os.path.isfile(bench):
        try:
            # graduated tiny: 512 prompt, 64 gen, 1 rep
            cmd = [bench, "-m", gguf, "-p", "512", "-n", "64", "-r", "1", "-ngl", "99"]
            t0 = time.time()
            b = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=180)
            rec["bench_sec"] = round(time.time() - t0, 2)
            rec["bench_exit"] = b.returncode
            rec["bench_stdout_tail"] = (b.stdout or "")[-800:]
            rec["bench_stderr_tail"] = (b.stderr or "")[-400:]
            rec["ok"] = b.returncode == 0
            Path(scratch, f"bench-{name}.log").write_text((b.stdout or "") + "\n" + (b.stderr or ""))
        except Exception as e:
            rec["bench_error"] = str(e)
    else:
        rec["bench_skip"] = "no llama-bench beside server"
    out["forks"][name] = rec
    print(name, "ok" if rec.get("ok") else rec.get("error") or rec.get("bench_error") or "partial")

path = Path(results) / "bench-forks-latest.json"
path.write_text(json.dumps(out, indent=2))
Path(scratch, "bench-forks.json").write_text(json.dumps(out, indent=2))
print("wrote", path)
PY
