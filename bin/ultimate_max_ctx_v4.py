#!/usr/bin/env python3
"""
Ultimate Max Context Finder v4 – Fully Dynamic
- Parses ggml.h for all GGML_TYPE_* names
- Converts to lower‑case strings (e.g. Q4_0 → q4_0)
- Runs a quick discovery phase at tiny context (128) to find which types work
- Then binary‑searches each working type
- Streams live JSON and saves a final report
"""

import subprocess
import time
import json
import pathlib
import os
import sys
import platform
import re
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple

# ============================================================================
# HARDWARE DETECTION
# ============================================================================

def get_gpu_info() -> Dict[str, Any]:
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
# DYNAMIC TYPE DISCOVERY
# ============================================================================

def discover_cache_types(ggml_h_path: pathlib.Path) -> List[Tuple[str, int]]:
    """
    Parse ggml.h for GGML_TYPE_* enums, convert to lower‑case strings,
    and return list of (type_string, bits_per_element).
    Bits are inferred from the type name.
    """
    if not ggml_h_path.exists():
        print("WARNING: ggml.h not found; using fallback types.", file=sys.stderr)
        return [("f16", 16), ("q4_0", 4), ("q8_0", 8)]

    with open(ggml_h_path) as f:
        content = f.read()

    # Find all GGML_TYPE_* enum names
    pattern = r'GGML_TYPE_([A-Z0-9_]+)'
    matches = re.findall(pattern, content)

    type_strings = []
    for name in matches:
        # Skip generic ones
        if name in ("COUNT", "UNKNOWN"):
            continue
        # Convert to lower case and replace underscore with underscore (keep as is)
        type_str = name.lower()
        # Estimate bits
        bits = estimate_bits(type_str, name)
        type_strings.append((type_str, bits))

    # Remove duplicates
    unique = {}
    for t, b in type_strings:
        if t not in unique:
            unique[t] = b
    return list(unique.items())

def estimate_bits(type_str: str, original: str) -> int:
    """
    Guess bits per element from type name.
    Examples: f16 → 16, q4_0 → 4, tq3 → 3, iq1_s → 1, etc.
    """
    if type_str.startswith("f"):
        try:
            return int(re.search(r'f(\d+)', type_str).group(1))
        except:
            return 16
    if type_str.startswith("q"):
        try:
            return int(re.search(r'q(\d+)', type_str).group(1))
        except:
            return 4
    if type_str.startswith("tq"):
        try:
            return int(re.search(r'tq(\d+)', type_str).group(1))
        except:
            return 3
    if type_str.startswith("iq"):
        try:
            return int(re.search(r'iq(\d+)', type_str).group(1))
        except:
            return 2
    # Fallback
    return 4

# ============================================================================
# DISCOVERY PHASE – Test which types actually work
# ============================================================================

def test_type_quick(cache_type: str) -> bool:
    """Quick test at tiny context to see if the type is supported."""
    kill_all()
    cmd = [
        str(SERVER),
        "-m", str(MODEL),
        "--mmproj", str(MMPROJ),
        "-c", "128",
        "-ngl", "99",
        "-fa", "1",
        "-ctk", cache_type,
        "-ctv", cache_type,
        "--host", "127.0.0.1",
        "--port", str(PORT_BASE),
        "-t", str(os.cpu_count() or 8),
        "-b", "512",
        "-ub", "256",
        "--no-warmup",
        "--alias", "qwen3.5",
        "--jinja",
        "--merge-qkv",
        "--grouped-expert-routing",
        "--reasoning-format", "auto",
    ]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        time.sleep(6)
        if proc.poll() is not None:
            kill_all()
            return False
        # Check if server responds
        result = subprocess.run(
            ["curl", "-s", "-f", f"http://127.0.0.1:{PORT_BASE}/v1/models"],
            capture_output=True, timeout=5
        )
        kill_all()
        return result.returncode == 0
    except Exception:
        kill_all()
        return False

# ============================================================================
# CONFIGURATION (paths – but cache types are discovered)
# ============================================================================

HOME = pathlib.Path("/home/toxic")
MODEL = HOME / "models" / "Qwen3.6-27B-Heretic-UD" / "heretic-UD-27B-Q5_K_XL.gguf"
MMPROJ = HOME / "models" / "Qwen3.6-27B-Heretic-UD" / "mmproj-27B-F16.gguf"
SERVER = HOME / "ik_llama.cpp-main" / "build" / "bin" / "llama-server"
BENCH = HOME / "ik_llama.cpp-main" / "build" / "bin" / "llama-bench"
GGML_H = HOME / "ik_llama.cpp-main" / "ggml" / "include" / "ggml.h"  # adjust if needed

PORT_BASE = 28080
TIMEOUT_START = 10
TIMEOUT_GEN = 60

# ============================================================================
# REST OF THE SCRIPT (identical to v3 but with dynamic CACHE_TYPES)
# ============================================================================

def kill_all():
    subprocess.run(["pkill", "-9", "-f", "llama-server"], capture_output=True)
    time.sleep(1.2)

def fitllm_estimate(ctx: int, cache_bits: int) -> Dict:
    n_params = 26_896_000_000
    n_layers = 64
    n_embd = 5120
    quant_bits = 5.0
    vram_mb = get_gpu_info()["vram_mb"]
    weight_mb = (n_params * quant_bits / 8) / 1024 / 1024
    kv_per_token_mb = (2 * n_embd * n_layers * (cache_bits / 8)) / 1024
    kv_mb = ctx * kv_per_token_mb
    overhead_mb = 2048
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

def get_extra_flags() -> List[str]:
    flags = []
    # MTP and TriAttention auto-detected
    mtp = HOME / "models" / "Qwen3.6-27B-UDT-MTP.gguf"
    tri = HOME / "calibrate_ref.py"
    if mtp.exists():
        flags.extend(["--spec-type", "nextn", "--model-draft", str(mtp)])
    if tri.exists():
        flags.extend(["--triattention", str(tri), "--tri-budget", "128", "--tri-interval", "128"])
    return flags

def test_ctx(ctx: int, cache_type: str) -> Dict:
    kill_all()
    batch, ubatch = get_ubatch_config(ctx)
    port = PORT_BASE
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
        "fitllm": fitllm_estimate(ctx, estimate_bits(cache_type, cache_type)),
    }

    if proc.poll() is not None:
        out = proc.stdout.read() if proc.stdout else ""
        kill_all()
        result["message"] = f"Process died early: {out[:200]}"
        result["success"] = False
        return result

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

def binary_search(cache_type: str, low: int = 4096, high: int = 262144) -> Dict:
    best = None
    res = test_ctx(low, cache_type)
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

def main():
    # Discover all possible cache types from ggml.h
    # Fallback to a safe list if ggml.h not found
    all_types = discover_cache_types(GGML_H)
    print(f"Discovered {len(all_types)} potential cache types: {[t for t,_ in all_types]}", file=sys.stderr)

    # Quick discovery phase: test each at ctx=128
    working_types = []
    for ct, bits in all_types:
        sys.stdout.write(json.dumps({"event": "discovery", "cache_type": ct, "status": "testing"}) + "\n")
        sys.stdout.flush()
        ok = test_type_quick(ct)
        if ok:
            working_types.append((ct, bits))
            sys.stdout.write(json.dumps({"event": "discovery", "cache_type": ct, "status": "works"}) + "\n")
        else:
            sys.stdout.write(json.dumps({"event": "discovery", "cache_type": ct, "status": "fails"}) + "\n")
        sys.stdout.flush()

    if not working_types:
        print("ERROR: No working cache types found!", file=sys.stderr)
        sys.exit(1)

    print(f"Working types: {[t for t,_ in working_types]}", file=sys.stderr)

    # Metadata
    gpu_info = get_gpu_info()
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "hostname": platform.node(),
        "gpu": gpu_info,
        "model_path": str(MODEL),
        "mmproj_path": str(MMPROJ),
        "server_path": str(SERVER),
        "all_discovered_types": [t for t,_ in all_types],
        "working_types": [t for t,_ in working_types],
        "use_mtp": (HOME / "models" / "Qwen3.6-27B-UDT-MTP.gguf").exists(),
        "use_triattention": (HOME / "calibrate_ref.py").exists(),
    }
    sys.stdout.write(json.dumps({"event": "metadata", "data": metadata}) + "\n")
    sys.stdout.flush()

    all_results = []
    for ct, bits in working_types:
        sys.stdout.write(json.dumps({"event": "start", "cache_type": ct, "bits": bits}) + "\n")
        sys.stdout.flush()
        res = binary_search(ct)
        all_results.append(res)
        sys.stdout.write(json.dumps({"event": "summary", "cache_type": ct, "result": res}) + "\n")
        sys.stdout.flush()

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

    sys.stdout.write(json.dumps({"event": "final", "data": final_report}) + "\n")
    sys.stdout.flush()

    out_file = HOME / "sovereign" / "canonical_benchmark_v4.json"
    with open(out_file, "w") as f:
        json.dump(final_report, f, indent=2)

    print(f"\n✅ Final report saved to {out_file}", file=sys.stderr)

if __name__ == "__main__":
    main()
