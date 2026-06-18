#!/usr/bin/env python3
"""
Pure Python launcher for ik_llama.cpp on /home/toxic/ rig only.
Symlinks all llama-* binaries then starts llama-server with safe flags
for the 27B Q5_K_XL model on RTX 3090 (limited ctx + q4_0 KV cache).
"""

import os
import subprocess
import pathlib
import datetime
import signal
import sys

HOME = pathlib.Path("/home/toxic")
IK_BIN = HOME / "ik_llama.cpp-main" / "build" / "bin"
SOV_BIN = HOME / "sovereign" / "bin"
LOG_DIR = HOME / "sovereign" / "logs"
PID_DIR = HOME / "sovereign" / "pids"
MODEL = HOME / "models" / "Qwen3.6-27B-Heretic-UD" / "heretic-UD-27B-Q5_K_XL.gguf"

SOV_BIN.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
PID_DIR.mkdir(parents=True, exist_ok=True)

print("==> Symlinking every llama-* binary under /home/toxic/ only")
count = 0
for src in sorted(IK_BIN.glob("llama-*")):
    if src.is_file() and os.access(src, os.X_OK):
        dst = SOV_BIN / src.name
        try:
            if dst.exists() or dst.is_symlink():
                dst.unlink()
            os.symlink(src, dst)
            print(f"    linked {src.name}")
            count += 1
        except Exception as e:
            print(f"    skip {src.name}: {e}")
print(f"==> {count} binaries now in {SOV_BIN}\n")

# --- Config (override via environment variables) ---
ctx_size = os.environ.get("CTX_SIZE", "8192")
port = os.environ.get("PORT", "8080")
host = os.environ.get("HOST", "0.0.0.0")
threads = str(os.cpu_count() or 8)

log_file = LOG_DIR / "llama.log"
pid_file = PID_DIR / "llama.pid"

# Clean up previous instance
if pid_file.exists():
    try:
        old = int(pid_file.read_text().strip())
        os.kill(old, signal.SIGTERM)
        print(f"Killed previous PID {old}")
    except Exception:
        pass
    pid_file.unlink(missing_ok=True)

cmd = [
    str(SOV_BIN / "llama-server"),
    "--model", str(MODEL),
    "-ngl", "99",
    "-c", ctx_size,
    "-fa",
    "--cache-type-k", "q4_0",
    "--cache-type-v", "q4_0",
    "--host", host,
    "--port", port,
    "--threads", threads,
]

print("==> Starting llama-server with safe flags for 3090")
print(" ".join(cmd))
print(f"    context={ctx_size}  KV=q4_0  flash-attn=on  layers=99\n")

with open(log_file, "a") as logf:
    logf.write(f"\n=== {datetime.datetime.now().isoformat()} ===\n")
    logf.write(" ".join(cmd) + "\n\n")

    proc = subprocess.Popen(
        cmd,
        stdout=logf,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        cwd=str(HOME),
    )

pid_file.write_text(str(proc.pid))
print(f"==> Running as PID {proc.pid}")
print(f"==> Log: {log_file}")
print(f"==> Stop with: kill $(cat {pid_file})")
