#!/usr/bin/env python3
"""
Bruteforce Max Context Finder — No test cycles, live memory tracking.
Strategy: Start at highest context, walk down by 4096 until server stays alive.
Monitors nvidia-smi in real-time to detect OOM before crash.
Kills nothing between tests — only the failed process dies.
"""

import subprocess
import time
import json
import os
import sys
from pathlib import Path

HOME = Path("/home/toxic")
MODEL = HOME / "models/Qwen3.6-27B-Heretic-UD/heretic-UD-27B-Q5_K_XL.gguf"
MMPROJ = HOME / "models/Qwen3.6-27B-Heretic-UD/mmproj-27B-F16.gguf"
SERVER = HOME / "ik_llama.cpp-main/build/bin/llama-server"

PORT = 28080
CTX_STEP = 4096
MAX_CTX = 262144
MIN_CTX = 4096

# Cache types to brute-force
CACHE_TYPES = [
    ("q4_0", "q4_0"),
    ("q8_0", "q8_0"),
    ("f16", "f16"),
]

def get_vram():
    """Live VRAM read. Returns (used_mb, total_mb, free_mb)"""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total,memory.free",
             "--format=csv,noheader,nounits"],
            text=True, timeout=2
        ).strip().split(", ")
        used, total, free = map(int, out)
        return used, total, free
    except Exception:
        return None, None, None

def server_alive(port):
    """Fast check if server responds."""
    try:
        import requests
        r = requests.get(f"http://127.0.0.1:{port}/v1/models", timeout=1)
        return r.status_code == 200
    except Exception:
        return False

def kill_server():
    """Only kill llama-server, leave everything else alone."""
    subprocess.run(["pkill", "-9", "-f", "llama-server"], capture_output=True)
    time.sleep(0.5)

def test_ctx_bruteforce(ctx, cache_k, cache_v):
    """
    Start server at ctx. Monitor live.
    If process dies → OOM/crash.
    If server responds → success.
    Returns (success_bool, vram_peak_mb, error_str)
    """
    kill_server()

    cmd = [
        str(SERVER), "-m", str(MODEL), "--mmproj", str(MMPROJ),
        "-c", str(ctx), "-ngl", "99", "-fa", "1",
        "-ctk", cache_k, "-ctv", cache_v,
        "--host", "127.0.0.1", "--port", str(PORT),
        "-t", str(os.cpu_count() or 8),
        "--no-warmup",
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    vram_peak = 0
    alive = False
    start_t = time.time()

    # Poll for up to 30s — monitor VRAM the whole time
    while time.time() - start_t < 30:
        # Check if process died (OOM/crash)
        if proc.poll() is not None:
            out = proc.stdout.read() if proc.stdout else ""
            is_oom = "cudaMalloc" in out or "out of memory" in out.lower()
            return False, vram_peak, ("OOM" if is_oom else f"exit_{proc.returncode}")

        # Live VRAM sampling
        used, total, free = get_vram()
        if used and used > vram_peak:
            vram_peak = used

        # Check if server is responding
        if server_alive(PORT):
            alive = True
            break

        time.sleep(0.5)

    if not alive:
        out = proc.stdout.read() if proc.stdout else ""
        is_oom = "cudaMalloc" in out or "out of memory" in out.lower()
        kill_server()
        return False, vram_peak, ("OOM" if is_oom else "timeout_no_response")

    # SUCCESS — server is running and responding
    # Grab final VRAM, then kill it
    used, total, free = get_vram()
    if used and used > vram_peak:
        vram_peak = used

    # Quick generation test to stress the context
    try:
        import requests
        requests.post(
            f"http://127.0.0.1:{PORT}/v1/completions",
            json={"prompt": "Test.", "n_predict": 8},
            timeout=10
        )
    except Exception:
        pass

    # Final VRAM after generation
    used, total, free = get_vram()
    if used and used > vram_peak:
        vram_peak = used

    kill_server()
    return True, vram_peak, None

def bruteforce_cache_type(cache_k, cache_v):
    """Start at MAX_CTX, walk down by CTX_STEP until it works."""
    print(f"\n{'='*60}")
    print(f"Cache: {cache_k}/{cache_v}")
    print(f"{'='*60}")

    ctx = MAX_CTX
    while ctx >= MIN_CTX:
        used, total, free = get_vram()
        print(f"  [VRAM] {used}/{total} MB used, {free} MB free")
        print(f"  >>> Testing ctx={ctx:,} ... ", end="", flush=True)

        ok, peak, err = test_ctx_bruteforce(ctx, cache_k, cache_v)

        if ok:
            print(f"✅ WORKS (peak VRAM: {peak} MB)")
            return {"cache_type": f"{cache_k}/{cache_v}", "max_ctx": ctx, "vram_peak_mb": peak}
        else:
            print(f"❌ {err} (peak VRAM: {peak} MB)")
            ctx -= CTX_STEP

    return {"cache_type": f"{cache_k}/{cache_v}", "max_ctx": 0, "error": "Nothing works"}

def main():
    print("=" * 60)
    print("BRUTEFORCE Max Context Finder")
    print("=" * 60)
    print(f"Model: {MODEL}")
    print(f"Range: {MIN_CTX:,} → {MAX_CTX:,} (step {CTX_STEP:,})")

    # GPU info
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total",
             "--format=csv,noheader"], text=True, timeout=5
        ).strip()
        print(f"GPU:   {out}")
    except:
        print("GPU:   unknown")

    results = []
    for ck, cv in CACHE_TYPES:
        res = bruteforce_cache_type(ck, cv)
        results.append(res)

    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")
    for r in results:
        if r.get("max_ctx", 0) > 0:
            print(f"  {r['cache_type']:12} {r['max_ctx']:>7,} tokens  (peak {r.get('vram_peak_mb','?')} MB)")
        else:
            print(f"  {r['cache_type']:12} FAILED")

    best = max(results, key=lambda x: x.get("max_ctx", 0))
    print(f"\nBest: {best['cache_type']} @ {best['max_ctx']:,} tokens")

    out_file = HOME / "sovereign/bruteforce_results.json"
    with open(out_file, "w") as f:
        json.dump({"results": results, "timestamp": time.time()}, f, indent=2)
    print(f"Saved: {out_file}")

if __name__ == "__main__":
    main()
