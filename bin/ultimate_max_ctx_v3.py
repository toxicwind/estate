#!/usr/bin/env python3
"""
Ultimate Max Context Finder v3 – Live JSON + Full Report
- Streams test results as JSON Lines (ndjson) to stdout for real‑time monitoring
- Saves final canonical JSON report with all details, command lines, hardware info
- Combines all June 2026 optimizations: TurboQuant, llama-bench --offline, FitLLM,
  TriAttention, UBatch, MTP, etc.
"""

import subprocess
import time
import json
import pathlib
import os
import sys
import platform
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, asdict, field

# ============================================================================
# HARDWARE DETECTION
# ============================================================================

def get_gpu_info() -> Dict[str, Any]:
    """Query GPU info via nvidia-smi."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            text=True
        ).strip().split(",")
        name = out[0].strip()
        vram_mb = float(out[1].strip())
        return {"name": name, "vram_mb": vram_mb}
    except Exception:
        return {"name": "Unknown", "vram_mb": 0}

# ============================================================================
# CONFIGURATION
# ============================================================================

HOME = pathlib.Path("/home/toxic")
MODEL = HOME / "models" / "Qwen3.6-27B-Heretic-UD" / "heretic-UD-27B-Q5_K_XL.gguf"
MMPROJ = HOME / "models" / "Qwen3.6-27B-Heretic-UD" / "mmproj-27B-F16.gguf"
SERVER = HOME / "ik_llama.cpp-main" / "build" / "bin" / "llama-server"
BENCH = HOME / "ik_llama.cpp-main" / "build" / "bin" / "llama-bench"

PORT_BASE = 28080
TIMEOUT_START = 10
TIMEOUT_GEN = 60

# Cache types to test (name, description, bits)
CACHE_TYPES = [
    ("turbo3", "TurboQuant 3-bit, 4.6x compression, <1.5% PPL loss", 3),
    ("turbo2", "TurboQuant 2-bit, 7.5x compression, aggressive", 2),
    ("amx3", "AMX3_1 hybrid, 2.37x raw + 4.74x effective with TriAttention", 3),
    ("q4_0", "4-bit standard, lossless on Qwen3.5/3.6", 4),
    ("q8_0", "8-bit standard, higher quality", 8),
]

# MTP / TriAttention flags (auto-detected if files exist)
MTP_MODEL = HOME / "models" / "Qwen3.6-27B-UDT-MTP.gguf"
TRIATTENTION_CALIB = HOME / "calibrate_ref.py"
USE_MTP = MTP_MODEL.exists()
USE_TRIATTENTION = TRIATTENTION_CALIB.exists()

# ============================================================================
# FITLLM CALCULATOR
# ============================================================================

def fitllm_estimate(ctx: int, cache_bits: int) -> Dict:
    """
    FitLLM-style VRAM estimation.
    Returns estimated memory in MiB and whether it fits.
    """
    # Qwen3.6-27B parameters
    n_params = 26_896_000_000
    n_layers = 64
    n_embd = 5120
    quant_bits = 5.0  # Q5_K
    vram_mb = get_gpu_info()["vram_mb"]

    weight_mb = (n_params * quant_bits / 8) / 1024 / 1024  # ~19.9 GiB
    kv_per_token_mb = (2 * n_embd * n_layers * (cache_bits / 8)) / 1024  # per token in MiB
    kv_mb = ctx * kv_per_token_mb
    overhead_mb = 2048  # compute buffers, activations, etc.
    total_mb = weight_mb + kv_mb + overhead_mb
    return {
        "weight_mb": weight_mb,
        "kv_per_token_mb": kv_per_token_mb,
        "kv_mb": kv_mb,
        "overhead_mb": overhead_mb,
        "total_mb": total_mb,
        "fits": total_mb < vram_mb,
        "max_ctx": int((vram_mb - weight_mb - overhead_mb) / kv_per_token_mb) if kv_per_token_mb > 0 else 0
    }

# ============================================================================
# UBatch DYNAMIC BATCH SIZING
# ============================================================================

def get_ubatch_config(ctx: int) -> Tuple[int, int]:
    if ctx > 196608:
        return 128, 64
    elif ctx > 131072:
        return 256, 128
    elif ctx > 65536:
        return 512, 256
    elif ctx > 32768:
        return 1024, 512
    else:
        return 2048, 512

# ============================================================================
# MTP / TRIATTENTION FLAGS
# ============================================================================

def get_extra_flags() -> List[str]:
    flags = []
    if USE_MTP:
        flags.extend(["--spec-type", "nextn", "--model-draft", str(MTP_MODEL)])
    if USE_TRIATTENTION:
        flags.extend(["--triattention", str(TRIATTENTION_CALIB), "--tri-budget", "128", "--tri-interval", "128"])
    return flags

# ============================================================================
# TEST FUNCTION – RETURNS DETAILED RESULT
# ============================================================================

def kill_all():
    subprocess.run(["pkill", "-9", "-f", "llama-server"], capture_output=True)
    time.sleep(1.2)

def test_ctx(ctx: int, cache_type: str) -> Dict:
    """
    Run a single test and return a result dict with:
    - success, message, command, server_pid, bench_results, vram_estimate, etc.
    """
    kill_all()
    batch, ubatch = get_ubatch_config(ctx)
    port = PORT_BASE  # could be dynamic per test if parallel

    # Build command
    cmd = [
        str(SERVER),
        "-m", str(MODEL),
        "--mmproj", str(MMPROJ),
        "-c", str(ctx),
        "-ngl", "99",
        "-fa", "1",
        "-ctk", cache_type,
        "-ctv", cache_type,
        "--host", "127.0.0.1",
        "--port", str(port),
        "-t", str(os.cpu_count() or 8),
        "-b", str(batch),
        "-ub", str(ubatch),
        "--no-warmup",
        "--alias", "qwen3.5",
        "--jinja",
        "--merge-qkv",
        "--grouped-expert-routing",
        "--reasoning-format", "auto",
    ]
    cmd.extend(get_extra_flags())

    # Start server
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    time.sleep(TIMEOUT_START)

    result = {
        "ctx": ctx,
        "cache_type": cache_type,
        "batch": batch,
        "ubatch": ubatch,
        "command": " ".join(cmd),
        "port": port,
        "pid": proc.pid,
        "success": False,
        "message": "",
        "bench": None,
        "fitllm": fitllm_estimate(ctx, next((b for t, _, b in CACHE_TYPES if t == cache_type), 4)),
    }

    if proc.poll() is not None:
        out = proc.stdout.read() if proc.stdout else ""
        kill_all()
        result["message"] = f"Process died early: {out[:200]}"
        result["success"] = False
        return result

    # Send completion request
    prompt = ("Write a detailed technical breakdown of running a 27B hybrid transformer-SSM model "
              "at high context on a single RTX 3090.")
    try:
        curl_result = subprocess.run(
            ["curl", "-s", "-X", "POST",
             f"http://127.0.0.1:{port}/v1/completions",
             "-H", "Content-Type: application/json",
             "-d", f'{{"prompt": {repr(prompt)}, "n_predict": 64}}'],
            capture_output=True, text=True, timeout=TIMEOUT_GEN
        )
    except subprocess.TimeoutExpired:
        kill_all()
        result["message"] = "Generation timeout"
        result["success"] = False
        return result

    # Run llama-bench (offline) for performance metrics
    bench_results = None
    if BENCH.exists():
        bench_cmd = [
            str(BENCH), "-m", str(MODEL), "-c", str(ctx), "-ngl", "99", "-fa", "1",
            "-ctk", cache_type, "-ctv", cache_type,
            "-b", str(batch), "-ub", str(ubatch),
            "-p", "512", "-n", "128", "-r", "2",
            "--offline", "--output-json"
        ]
        try:
            bench_out = subprocess.check_output(bench_cmd, text=True, timeout=120)
            bench_data = json.loads(bench_out)
            bench_results = {
                "pp_speed": bench_data.get("results", [{}])[0].get("pp_avg"),
                "tg_speed": bench_data.get("results", [{}])[0].get("tg_avg"),
                "n_graph_splits": bench_data.get("results", [{}])[0].get("n_graph_splits"),
            }
        except Exception:
            pass

    kill_all()

    if curl_result.returncode != 0:
        result["message"] = "curl failed"
        result["success"] = False
    elif "text" in curl_result.stdout and len(curl_result.stdout) > 50:
        result["success"] = True
        result["message"] = "Generated successfully"
        result["bench"] = bench_results
    else:
        result["message"] = f"Unexpected response: {curl_result.stdout[:100]}"
        result["success"] = False

    return result

# ============================================================================
# BINARY SEARCH WITH LIVE JSON OUTPUT
# ============================================================================

def binary_search(cache_type: str, low: int = 4096, high: int = 262144) -> Dict:
    """
    Perform binary search and emit each test result as JSON line (ndjson).
    Returns final best result for this cache type.
    """
    best = None
    # Test low first
    res = test_ctx(low, cache_type)
    # Emit live JSON
    sys.stdout.write(json.dumps({"event": "test", "data": res}) + "\n")
    sys.stdout.flush()
    if not res["success"]:
        return {"cache_type": cache_type, "max_ctx": 0, "error": res["message"]}

    best = res
    current_low = low
    current_high = high

    while current_low + 4096 < current_high:
        mid = ((current_low + current_high) // 2 // 4096) * 4096
        res = test_ctx(mid, cache_type)
        sys.stdout.write(json.dumps({"event": "test", "data": res}) + "\n")
        sys.stdout.flush()
        if res["success"]:
            best = res
            current_low = mid
        else:
            current_high = mid

    # Final upward step
    if best and best["ctx"] == current_low and current_low + 4096 <= current_high:
        candidate = current_low + 4096
        res = test_ctx(candidate, cache_type)
        sys.stdout.write(json.dumps({"event": "test", "data": res}) + "\n")
        sys.stdout.flush()
        if res["success"]:
            best = res

    return {
        "cache_type": cache_type,
        "max_ctx": best["ctx"] if best else 0,
        "best_result": best,
    }

# ============================================================================
# MAIN – EMIT LIVE JSON + FINAL REPORT FILE
# ============================================================================

def main():
    # Start with metadata
    gpu_info = get_gpu_info()
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "hostname": platform.node(),
        "gpu": gpu_info,
        "model_path": str(MODEL),
        "mmproj_path": str(MMPROJ),
        "server_path": str(SERVER),
        "cache_types_tested": [t[0] for t in CACHE_TYPES],
        "use_mtp": USE_MTP,
        "use_triattention": USE_TRIATTENTION,
    }
    # Emit metadata event
    sys.stdout.write(json.dumps({"event": "metadata", "data": metadata}) + "\n")
    sys.stdout.flush()

    all_results = []
    for cache_type, desc, bits in CACHE_TYPES:
        # Emit start event
        sys.stdout.write(json.dumps({"event": "start", "cache_type": cache_type, "description": desc}) + "\n")
        sys.stdout.flush()

        res = binary_search(cache_type)
        all_results.append(res)

        # Emit summary for this cache type
        sys.stdout.write(json.dumps({"event": "summary", "cache_type": cache_type, "result": res}) + "\n")
        sys.stdout.flush()

    # Compute best overall
    best_overall = max(all_results, key=lambda x: x.get("max_ctx", 0))
    final_report = {
        "metadata": metadata,
        "results": all_results,
        "best_overall": best_overall,
        "recommendation": {
            "cache_type": best_overall.get("cache_type"),
            "context": best_overall.get("max_ctx"),
        }
    }

    # Emit final report as JSON
    sys.stdout.write(json.dumps({"event": "final", "data": final_report}) + "\n")
    sys.stdout.flush()

    # Save to file
    out_file = HOME / "sovereign" / "canonical_benchmark_v3.json"
    with open(out_file, "w") as f:
        json.dump(final_report, f, indent=2)

    print(f"\n✅ Final report saved to {out_file}", file=sys.stderr)

if __name__ == "__main__":
    main()
