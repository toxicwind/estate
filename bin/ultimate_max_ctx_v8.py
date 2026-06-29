#!/usr/bin/env python3
"""
Ultimate Max Context Finder v8 — Fixed
- Sane discovery: skip it, test only q4_0/q8_0/f16 (the only ones that matter)
- Proper load wait: 15s base + polling, not 10 attempts of capped backoff
- Real OOM detection from stderr, not just "not ready"
- No 88-type discovery nonsense
- Single cache type at a time (VRAM safety)
"""
import os
import sys
import time
import json
import pathlib
import subprocess
from datetime import datetime
HOME = pathlib.Path("/home/toxic")
MODEL = HOME / "models/Qwen3.6-27B-Heretic-UD/heretic-UD-27B-Q5_K_XL.gguf"
MMPROJ = HOME / "models/Qwen3.6-27B-Heretic-UD/mmproj-27B-F16.gguf"
SERVER = HOME / "ik_llama.cpp-main/build/bin/llama-server"
PORT = 28080
LOAD_TIMEOUT = 20.0
GEN_TIMEOUT = 45.0
# Only test these. 88 types is insane — most are internal GGML types not for KV cache.
CACHE_TYPES = ["q4_0", "q8_0", "f16"]


def kill_all():
  subprocess.run(["pkill", "-9", "-f", "llama-server"], capture_output=True)
  subprocess.run(["pkill", "-9", "-f", "ollama"], capture_output=True)
  time.sleep(1.0)


def get_vram():
  try:
    out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total",
             "--format=csv,noheader,nounits"], text=True, timeout=5
        ).strip().split(", ")
    return int(out[0]), int(out[1])
  except:
    Exception


def poll_server(port, max_wait=LOAD_TIMEOUT):
  """Poll /v1/models with requests, waiting up to max_wait seconds total."""
  import requests
  url = f"http://127.0.0.1:{port}/v1/models"
  t0 = time.time()
  while time.time() - t0 < max_wait:
    try:
      r = requests.get(url, timeout=2)
      if r.status_code == 200:
        return True, time.time() - t0
    except:
      Exception
    time.sleep(0.3)
  return False, time.time() - t0


def test_ctx(ctx, cache_type):
  kill_all()
  cmd = [
        str(SERVER), "-m", str(MODEL), "--mmproj", str(MMPROJ),
        "-c", str(ctx), "-ngl", "99", "-fa", "1",
        "-ctk", cache_type, "-ctv", cache_type,
        "--host", "127.0.0.1", "--port", str(PORT),
        "-t", str(os.cpu_count() or 8),
        "--no-warmup", "--alias", "llama",
    ]
  vram_before, vram_total = get_vram()
  t0 = time.time()
  proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
  ready, wait_time = poll_server(PORT)
  if not ready:
    out = proc.stdout.read() if proc.stdout else ""
    kill_all()
    # Check if it's OOM vs other failure
    is_oom = "cudaMalloc failed" in out or "out of memory" in out.lower()
    is_oom |= "unable to allocate" in out.lower()
    return {
    "ctx": ctx,
    "cache_type": cache_type,
    "success": False,
    "error": "OOM" if is_oom else f"not_ready ({wait_time:.1f}s)",
    "stderr_preview": out[-800:] if out else "",
    "vram_before_mb": vram_before,
    "vram_total_mb": vram_total,
    "load_wait_sec": wait_time,
}
  load_time = time.time() - t0
  # Real completion request
  import requests
  try:
    resp = requests.post(
            f"http://127.0.0.1:{PORT}/v1/completions",
            json={"prompt": "Explain memory bandwidth bottlenecks in LLM inference.", "n_predict": 32},
            timeout=GEN_TIMEOUT
        )
  except:
    Exception as e
  vram_after, _ = get_vram()
  kill_all()
  ok = resp.status_code == 200 and len(resp.text) > 50
  return {
    "ctx": ctx,
    "cache_type": cache_type,
    "success": ok,
    "error": None if ok else f"http_{resp.status_code}",
    "load_time_sec": load_time,
    "gen_time_sec": time.time() - t0 - load_time,
    "vram_before_mb": vram_before,
    "vram_after_mb": vram_after,
    "vram_total_mb": vram_total,
    "response_preview": resp.text[:200] if ok else resp.text[-300:],
}


def binary_search(cache_type, low=4096, high=262144):
  print(f"\n=== Cache: {cache_type} ===", flush=True)
  # Verify baseline
  r = test_ctx(low, cache_type)
  print(f"  {low:>7}: {'OK' if r['success'] else 'FAIL'} ({r.get('error','')})", flush=True)
  if not r['success']:
    return {"cache_type": cache_type, "max_ctx": 0, "error": r['error']}
  best = low
  lo, hi = low, high
  while lo + 4096 < hi:
    mid = ((lo + hi) // 2 // 4096) * 4096
    if mid <= lo:
      mid = lo + 4096
    r = test_ctx(mid, cache_type)
    status = "OK" if r['success'] else "FAIL"
    vram_info = ""
    if r.get('vram_after_mb'):
      vram_info = f" VRAM={r['vram_after_mb']}/{r['vram_total_mb']}MB"
    print(f"  {mid:>7}: {status} ({r.get('error','')}){vram_info}", flush=True)
    if r['success']:
      best = mid
      lo = mid
    else:
      hi = mid
  # Verify best
  r = test_ctx(best, cache_type)
  print(f"  {best:>7}: FINAL {'OK' if r['success'] else 'FAIL'}", flush=True)
  return {"cache_type": cache_type, "max_ctx": best if r['success'] else 0}


def main():
  print("=" * 60)
  print("Max Context Finder v8")
  print(f"Model: {MODEL}")
  print(f"GPU:   ", end="", flush=True)
  try:
    out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            text=True, timeout=5
        ).strip()
    print(out)
  except:
    print("unknown")
  all_results = []
  for ct in CACHE_TYPES:
    res = binary_search(ct)
    all_results.append(res)
  print("\n" + "=" * 60)
  print("SUMMARY")
  print("=" * 60)
  for r in all_results:
    print(f"  {r['cache_type']:6} -> {r['max_ctx']:>7,} tokens")
  best = max(all_results, key=lambda x: x['max_ctx'])
  print(f"\nBest: {best['cache_type']} @ {best['max_ctx']:,} tokens")
  out_file = HOME / "sovereign/context_results_v8.json"
  with open(out_file, "w") as f:
        json.dump({"results": all_results, "timestamp": datetime.now().isoformat()}, f, indent=2)
  print(f"\nSaved: {out_file}")
if __name__ == "__main__":
  main()
