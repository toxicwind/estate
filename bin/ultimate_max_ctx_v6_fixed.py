#!/usr/bin/env python3
"""
Ultimate Max Context Finder v6 – Fixed Capped Exponential Backoff
"""

import os, sys, time, json, pathlib, platform, re, subprocess
from typing import Optional, Dict, List, Any, Tuple

# ============================================================================
# ENVIRONMENT VARIABLES
# ============================================================================
def get_env_or_default(name: str, default: str) -> str:
    return os.environ.get(name, default)

MODEL_PATH = pathlib.Path(get_env_or_default("MODEL_PATH", "/home/toxic/models/Qwen3.6-27B-Heretic-UD/heretic-UD-27B-Q5_K_XL.gguf"))
MMPROJ_PATH = pathlib.Path(get_env_or_default("MMPROJ_PATH", str(MODEL_PATH.parent / "mmproj-27B-F16.gguf")))
SERVER_BIN = pathlib.Path(get_env_or_default("SERVER_BIN", "/home/toxic/ik_llama.cpp-main/build/bin/llama-server"))
BENCH_BIN = pathlib.Path(get_env_or_default("BENCH_BIN", "/home/toxic/ik_llama.cpp-main/build/bin/llama-bench"))
GGML_H_PATH = pathlib.Path(get_env_or_default("GGML_H_PATH", "/home/toxic/ik_llama.cpp-main/ggml/include/ggml.h"))
PORT_BASE = int(os.environ.get("PORT_BASE", "28080"))
TIMEOUT_GEN = int(os.environ.get("TIMEOUT_GEN", "60"))

# ============================================================================
# DISCOVERY TYPES (filtered)
# ============================================================================
def discover_cache_types(ggml_h_path: pathlib.Path) -> List[Tuple[str, int]]:
    if not ggml_h_path.exists():
        return [("q4_0", 4), ("q8_0", 8), ("f16", 16)]
    with open(ggml_h_path) as f:
        content = f.read()
    matches = re.findall(r'GGML_TYPE_([A-Z0-9_]+)', content)
    keep_re = re.compile(r'^(q|tq|iq|bf16|f16|f32)')
    types = {}
    for name in matches:
        if name in ("COUNT", "UNKNOWN"):
            continue
        t = name.lower()
        if keep_re.match(t):
            bits = estimate_bits(t, name)
            types[t] = bits
    return list(types.items())

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
# POLLING WITH CAPPED EXPONENTIAL BACKOFF
# ============================================================================
def poll_server_ready(port: int, max_attempts: int = 10, base_delay: float = 0.2, max_delay: float = 2.0) -> bool:
    import requests
    url = f"http://127.0.0.1:{port}/v1/models"
    for attempt in range(max_attempts):
        try:
            r = requests.get(url, timeout=1)
            if r.status_code == 200:
                return True
        except:
            pass
        delay = min(base_delay * (2 ** attempt), max_delay)
        time.sleep(delay)
    return False

# ============================================================================
# GPU INFO, FITLLM, UBATCH, KILL, TEST CTX, BINARY SEARCH, DISCOVERY, MAIN
# (same as before, but with the fixed poll function)
# ============================================================================
# ... (rest of the script from v6, but replace poll_server_ready as above)
# Since the full script is long, I'll include the full version below.
# But for brevity, I'll provide the complete corrected script in the final answer.
