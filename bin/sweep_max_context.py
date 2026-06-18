#!/usr/bin/env python3
import subprocess
import pathlib
import time

HOME = pathlib.Path("/home/toxic")
MODEL = HOME / "models" / "Qwen3.6-27B-Heretic-UD" / "heretic-UD-27B-Q5_K_XL.gguf"
BENCH = HOME / "sovereign" / "bin" / "llama-bench"

CONTEXTS = [4096, 8192, 16384, 32768, 65536]

print("=== Max Context Sweep ===\n")
print(f"Model: {MODEL.name}\n")

for ctx in CONTEXTS:
    cmd = [
        str(BENCH),
        "-m", str(MODEL),
        "-ngl", "99",
        "--ctx-size", str(ctx),      # ← fixed flag
        "-fa",
        "--cache-type-k", "q4_0",
        "--cache-type-v", "q4_0",
        "-b", "1024",
        "-r", "1",
    ]

    print(f">>> Testing ctx={ctx}   VRAM before: ", end="")
    try:
        v = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            text=True
        ).strip()
        print(f"{v} MiB")
    except:
        print("n/a")

    t0 = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - t0

    if proc.returncode != 0:
        print("    FAILED\n")
        print((proc.stderr or proc.stdout)[-2500:])
        print()
        break
    else:
        print(f"    OK in {elapsed:.1f}s\n")
