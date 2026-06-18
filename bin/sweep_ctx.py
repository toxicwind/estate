#!/usr/bin/env python3
import subprocess
import pathlib
import time

HOME = pathlib.Path("/home/toxic")
MODEL = HOME / "models" / "Qwen3.6-27B-Heretic-UD" / "heretic-UD-27B-Q5_K_XL.gguf"
BENCH = HOME / "sovereign" / "bin" / "llama-batched-bench"

CONTEXTS = [4096, 8192, 16384, 32768, 65536]

print("=== Max Context Sweep (llama-batched-bench) ===\n")

for ctx in CONTEXTS:
    cmd = [
        str(BENCH),
        "-m", str(MODEL),
        "-ngl", "99",
        "-c", str(ctx),
        "--cache-type-k", "q4_0",
        "--cache-type-v", "q4_0",
        "-b", "1024",
        "-ub", "512",
        "-n", "128",
    ]

    print(f">>> Testing ctx={ctx}")
    t0 = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - t0

    if proc.returncode != 0:
        print("    FAILED\n")
        print((proc.stderr or proc.stdout)[-2500:])
        break
    else:
        print(f"    OK ({elapsed:.1f}s)\n")
