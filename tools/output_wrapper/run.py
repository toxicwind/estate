#!/usr/bin/env python3
"""
Universal command output wrapper for LLM-friendly structured output.
Wraps any command and returns consistent JSON with stdout, stderr, exit_code, timing.
"""
import json
import subprocess
import sys
import time
import os
from pathlib import Path

def run_wrapped(cmd, cwd=None, env=None, timeout=300):
    """Run command and return structured JSON output."""
    start = time.time()
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=full_env,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=isinstance(cmd, str)
        )
        duration = time.time() - start
        
        return {
            "ok": result.returncode == 0,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration_ms": round(duration * 1000, 2),
            "command": cmd if isinstance(cmd, str) else " ".join(cmd),
            "cwd": cwd or os.getcwd()
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s",
            "duration_ms": round((time.time() - start) * 1000, 2),
            "command": cmd if isinstance(cmd, str) else " ".join(cmd),
            "cwd": cwd or os.getcwd()
        }
    except Exception as e:
        return {
            "ok": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "duration_ms": round((time.time() - start) * 1000, 2),
            "command": cmd if isinstance(cmd, str) else " ".join(cmd),
            "cwd": cwd or os.getcwd()
        }

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "Usage: run.py <command> [args...]"}), file=sys.stderr)
        sys.exit(1)
    
    cmd = sys.argv[1:]
    cwd = os.environ.get("SOVEREIGN_ROOT", "/home/toxic/sovereign")
    
    result = run_wrapped(cmd, cwd=cwd)
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
