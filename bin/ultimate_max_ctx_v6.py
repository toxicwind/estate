#!/usr/bin/env python3
"""
Ultimate Max Context Finder v6 – Production Grade
- Uses uv for dependency management (requests)
- Exponential backoff polling for server readiness
- Environment variables for paths (institutionally blind)
- Filters KV cache types dynamically from ggml.h
- Binary search with health checks
- Streams live JSON events and saves final report
"""

import os
import sys
import time
import json
import pathlib
import platform
import re
import subprocess
from typing import Optional, Dict, List, Any, Tuple

# ============================================================================
# ENVIRONMENT VARIABLES (institutionally blind)
# ============================================================================

def get_env_or_default(name: str, default: str) -> str:
    return os.environ.get(name, default)

# Paths
MODEL_PATH = pathlib.Path(get_env_or_default("MODEL_PATH", "/home/toxic/models/Qwen3.6-27B-Heretic-UD/heretic-UD-27B-Q5_K_XL.gguf"))
MMPROJ_PATH = pathlib.Path(get_env_or_default("MMPROJ_PATH", str(MODEL_PATH.parent / "mmproj-27B-F16.gguf")))
SERVER_BIN = pathlib.Path(get_env_or_default("SERVER_BIN", "/home/toxic/ik_llama.cpp-main/build/bin/llama-server"))
BENCH_BIN = pathlib.Path(get_env_or_default("BENCH_BIN", "/home/toxic/ik_llama.cpp-main/build/bin/llama-bench"))
GGML_H_PATH = pathlib.Path(get_env_or_default("GGML_H_PATH", "/home/toxic/ik_llama.cpp-main/ggml/include/ggml.h"))

PORT_BASE = int(os.environ.get("PORT_BASE", "28080"))
TIMEOUT_START = int(os.environ.get("TIMEOUT_START", "10"))
TIMEOUT_GEN = int(os.environ.get("TIMEOUT_GEN", "60"))

# ============================================================================
# DYNAMIC TYPE DISCOVERY (filtered to relevant KV types)
# ============================================================================

def discover_cache_types(ggml_h_path: pathlib.Path) -> List[Tuple[str, int]]:
    """Parse ggml.h for GGML_TYPE_* and filter to KV-compatible types."""
    if not ggml_h_path.exists():
        print("WARNING: ggml.h not found; using fallback types.", file=sys.stderr)
        return [("q4_0", 4), ("q8_0", 8), ("f16", 16)]

    with open(ggml_h_path) as f:
        content = f.read()

    pattern = r'GGML_TYPE_([A-Z0-9_]+)'
    matches = re.findall(pattern, content)

    # Keep only types likely for KV cache
    keep_patterns = [
        r'^q',       # q4_0, q8_0, q5_0, q2_k, etc.
        r'^tq',      # tq3, tq4
        r'^iq',      # iq1_s, iq4_nl, etc.
        r'^bf16',
        r'^f16',
        r'^f32',
    ]
    keep_re = re.compile('|'.join(keep_patterns))

    type_strings = []
    for name in matches:
        if name in ("COUNT", "UNKNOWN"):
            continue
        type_str = name.lower()
        if keep_re.match(type_str):
            bits = estimate_bits(type_str, name)
            type_strings.append((type_str, bits))

    unique = {}
    for t, b in type_strings:
        if t not in unique:
            unique[t] = b
    return list(unique.items())

def estimate_bits(type_str: str, original: str) -> int:
    if type_str.startswith("f"):
        try: return int(re.search(r'f(\d+)', type_str).group(1))
        except: return 16
    if type_str.startswith("q"):
        try: return int(re.search(r'q(\d+)', type_str).group(1))
        except: return 4
    if type_str.startswith("tq"):
        try: return int(re.search(r'tq(\d+)', type_str).group(1))
        except: return 3
    if type_str.startswith("iq"):
        try: return int(re.search(r'iq(\d+)', type_str).group(1))
        except: return 2
    if type_str.startswith("bf16"):
        return 16
    return 4

# ============================================================================
# POLLING WITH EXPONENTIAL BACKOFF
# ============================================================================

def poll_server_ready(port: int, max_attempts: int = 20, base_delay: float = 0.5) -> bool:
    """Poll /v1/models until it responds, with exponential backoff."""
    import requests
    url = f"http://127.0.0.1:{port}/v1/models"
    for attempt in range(max_attempts):
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                return True
        except:
            pass
        delay = base_delay * (2 ** attempt)  # exponential
        time.sleep(delay)
    return False

# ============================================================================
# GPU INFO
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
# FITLLM ESTIMATOR
# ============================================================================

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

# ============================================================================
# UBatch CONFIG
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
# KILL ALL
# ============================================================================

def kill_all():
    subprocess.run(["pkill", "-9", "-f", "llama-server"], capture_output=True)
    time.sleep(1.2)

# ============================================================================
# TEST CTX WITH POLLING
# ============================================================================

def test_ctx(ctx: int, cache_type: str) -> Dict:
    kill_all()
    batch, ubatch = get_ubatch_config(ctx)
    port = PORT_BASE

    cmd = [
        str(SERVER_BIN),
        "-m", str(MODEL_PATH),
        "--mmproj", str(MMPROJ_PATH),
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

    # Optional MTP / TriAttention flags
    mtp = pathlib.Path(os.environ.get("MTP_MODEL", "/home/toxic/models/Qwen3.6-27B-UDT-MTP.gguf"))
    tri = pathlib.Path(os.environ.get("TRI_CALIB", "/home/toxic/calibrate_ref.py"))
    if mtp.exists():
        cmd.extend(["--spec-type", "nextn", "--model-draft", str(mtp)])
    if tri.exists():
        cmd.extend(["--triattention", str(tri), "--tri-budget", "128", "--tri-interval", "128"])

    result = {
        "ctx": ctx,
        "cache_type": cache_type,
        "batch": batch,
        "ubatch": ubatch,
        "command": " ".join(cmd),
        "port": port,
        "success": False,
        "message": "",
        "bench": None,
        "fitllm": fitllm_estimate(ctx, estimate_bits(cache_type, cache_type)),
    }

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    # Poll for readiness
    ready = poll_server_ready(port, max_attempts=20, base_delay=0.5)

    if not ready:
        out = proc.stdout.read() if proc.stdout else ""
        kill_all()
        result["message"] = f"Server not ready: {out[:200]}"
        result["success"] = False
        return result

    # Send completion request
    import requests
    prompt = ("Write a detailed technical breakdown of running a 27B hybrid transformer-SSM model "
              "at high context on a single RTX 3090.")
    try:
        resp = requests.post(
            f"http://127.0.0.1:{port}/v1/completions",
            json={"prompt": prompt, "n_predict": 64},
            timeout=TIMEOUT_GEN
        )
    except Exception as e:
        kill_all()
        result["message"] = f"Generation error: {e}"
        result["success"] = False
        return result

    # Run llama-bench (offline) for performance
    bench_results = None
    if BENCH_BIN.exists():
        bench_cmd = [
            str(BENCH_BIN), "-m", str(MODEL_PATH), "-c", str(ctx), "-ngl", "99", "-fa", "1",
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

    if resp.status_code == 200 and "text" in resp.text and len(resp.text) > 50:
        result["success"] = True
        result["message"] = "Generated successfully"
        result["bench"] = bench_results
    else:
        result["message"] = f"Bad response: {resp.text[:100]}"
        result["success"] = False

    return result

# ============================================================================
# BINARY SEARCH
# ============================================================================

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

# ============================================================================
# DISCOVERY
# ============================================================================

def test_type_quick(cache_type: str) -> Tuple[bool, str]:
    """Quick test at ctx=128, returns (success, error_message)."""
    kill_all()
    cmd = [
        str(SERVER_BIN),
        "-m", str(MODEL_PATH),
        "--mmproj", str(MMPROJ_PATH),
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
        ready = poll_server_ready(PORT_BASE, max_attempts=20, base_delay=0.5)
        if ready:
            kill_all()
            return True, ""
        else:
            out = proc.stdout.read() if proc.stdout else ""
            kill_all()
            return False, f"Server not ready: {out[:300]}"
    except Exception as e:
        kill_all()
        return False, f"Exception: {e}"

# ============================================================================
# MAIN
# ============================================================================

def main():
    # Ensure requests is available (uv will install if needed)
    try:
        import requests
    except ImportError:
        print("requests not found; install with: uv pip install requests", file=sys.stderr)
        sys.exit(1)

    # Discover types
    all_types = discover_cache_types(GGML_H_PATH)
    print(f"Discovered {len(all_types)} potential cache types.", file=sys.stderr)

    # Quick discovery
    working_types = []
    for ct, bits in all_types:
        sys.stdout.write(json.dumps({"event": "discovery", "cache_type": ct, "status": "testing"}) + "\n")
        sys.stdout.flush()
        ok, err = test_type_quick(ct)
        if ok:
            working_types.append((ct, bits))
            sys.stdout.write(json.dumps({"event": "discovery", "cache_type": ct, "status": "works"}) + "\n")
        else:
            sys.stdout.write(json.dumps({"event": "discovery", "cache_type": ct, "status": "fails", "error": err}) + "\n")
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
        "model_path": str(MODEL_PATH),
        "mmproj_path": str(MMPROJ_PATH),
        "server_path": str(SERVER_BIN),
        "all_discovered_types": [t for t,_ in all_types],
        "working_types": [t for t,_ in working_types],
        "use_mtp": pathlib.Path(os.environ.get("MTP_MODEL", "/home/toxic/models/Qwen3.6-27B-UDT-MTP.gguf")).exists(),
        "use_triattention": pathlib.Path(os.environ.get("TRI_CALIB", "/home/toxic/calibrate_ref.py")).exists(),
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

    out_file = pathlib.Path(os.environ.get("REPORT_PATH", "/home/toxic/sovereign/canonical_benchmark_v6.json"))
    with open(out_file, "w") as f:
        json.dump(final_report, f, indent=2)

    print(f"\n✅ Final report saved to {out_file}", file=sys.stderr)

if __name__ == "__main__":
    main()
