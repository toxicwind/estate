#!/usr/bin/env python3
"""
Real-world max context tester for your exact rig.
- Uses ik_llama.cpp llama-server (not the wrong batched bench binary)
- Real curl completion request (not dummy token)
- Binary search (fast)
- Handles this build's "input is empty" exit gracefully
- Kills cleanly between runs
"""

import subprocess
import pathlib
import time
import os

HOME = pathlib.Path("/home/toxic")
MODEL = HOME / "models" / "Qwen3.6-27B-Heretic-UD" / "heretic-UD-27B-Q5_K_XL.gguf"
MMPROJ = HOME / "models" / "Qwen3.6-27B-Heretic-UD" / "mmproj-27B-F16.gguf"
SERVER = HOME / "ik_llama.cpp-main" / "build" / "bin" / "llama-server"

PORT = 28080

# Real bench prompt (technical, long enough to matter)
BENCH_PROMPT = (
    "Write a detailed technical breakdown of running a 27B hybrid transformer-SSM model "
    "at high context on a single RTX 3090. Cover KV cache quantization impact (q4_0), "
    "flash attention memory savings, layer memory distribution, expert routing overhead, "
    "and where the hard VRAM wall appears between 8k and 128k context."
)

def kill_all():
    subprocess.run(["pkill", "-9", "-f", "llama-server"], capture_output=True, timeout=50)
    subprocess.run(["pkill", "-9", "-f", "ollama"], capture_output=True, timeout=50)
    time.sleep(1.2)

def test_ctx(ctx: int) -> tuple[bool, str]:
    kill_all()

    cmd = [
        str(SERVER),
        "-m", str(MODEL),
        "--mmproj", str(MMPROJ),
        "-c", str(ctx),
        "-ngl", "99",
        "-fa", "1",
        "-ctk", "q4_0",
        "-ctv", "q4_0",
        "--host", "127.0.0.1",
        "--port", str(PORT),
        "-t", str(os.cpu_count() or 8),
        "--no-warmup",
    ]

    print(f">>> ctx={ctx:,}")

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    # Wait for server to start listening
    server_ready = False
    for _ in range(30):
        if proc.poll() is not None:
            break
        try:
            r = subprocess.run(["curl", "-s", f"http://127.0.0.1:{PORT}/health"], capture_output=True, text=True)
            if "ok" in r.stdout.lower():
                server_ready = True
                break
        except:
            pass
        time.sleep(1)
        
    if not server_ready:
        out = proc.stdout.read() if proc.stdout else ""
        kill_all()
        if "cudaMalloc failed" in out or "out of memory" in out.lower():
            return False, "OOM on load"
        return False, "server failed to start or OOM"

    # Now run the real bench curl
    import json
    prompt_json = json.dumps(BENCH_PROMPT)
    for _ in range(3):
        try:
            result = subprocess.run([
                "curl", "-s", "-X", "POST",
                f"http://127.0.0.1:{PORT}/completion",
                "-H", "Content-Type: application/json",
                "-d", f'{{"prompt": {prompt_json}, "n_predict": 100, "temperature": 0.1}}'
            ], capture_output=True, text=True, timeout=120)
            
            out = result.stdout
            if "error" in out.lower() and "loading model" in out.lower():
                time.sleep(2)
                continue
                
            kill_all()
            if "error" in out.lower():
                return False, f"server error"
            
            if "content" in out:
                return True, "ok"
                
            return False, f"invalid response"
        except subprocess.TimeoutExpired:
            kill_all()
            return False, "timeout"
            
    kill_all()
    return False, "timeout waiting for model load"

# Binary search
low = 4096
high = 131072
best = 4096

print("=== Max Context Search ===\n")

# Seed check
ok, msg = test_ctx(4096)
if not ok:
    print(f"FATAL at 4k: {msg}")
    exit(1)
print(f"4k: {msg}\n")
best = 4096

while low + 4096 < high:
    mid = ((low + high) // 2 // 4096) * 4096
    ok, msg = test_ctx(mid)
    print(f"{mid:,}: {msg}\n")

    if ok:
        best = mid
        low = mid
    else:
        high = mid

print(f"\nHighest stable context: {best:,}")
