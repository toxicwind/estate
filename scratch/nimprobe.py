import subprocess, time, json

V = "/home/hatch/workspace/skills/nvidia-nim-loader/.venv/bin/python"
N = "/home/hatch/workspace/skills/nvidia-nim-loader/bin/nim.py"

models = [
    "openai/gpt-oss-20b",
    "z-ai/glm-5.3-flash",
    "moonshotai/kimi-k2.6",
    "nvidia/nemotron-3.5-lightning-30b-a3b",
    "nvidia/nemotron-3-ultra-550b-a55b",
    "nvidia/llama-3.1-nemotron-70b-instruct",
    "nvidia/nemotron-nano-3-30b-a3b",
]

results = []
for m in models:
    t0 = time.time()
    try:
        out = subprocess.run(
            [V, N, "chat", "--model", m, "--max-tokens", "16",
             "--timeout", "25", "--format", "text", "reply with exactly: OK"],
            capture_output=True, text=True, timeout=40)
        dt = time.time() - t0
        ok = out.returncode == 0 and "OK" in out.stdout
        err = "" if ok else (out.stderr.strip()[:150] or out.stdout.strip()[:150])
        if "429" in err or "rate" in err.lower():
            print(f"{m}: RATE-LIMITED, stopping")
            results.append({"model": m, "status": "rate_limited", "latency_s": round(dt, 1)})
            break
        print(f"{m}: {'ALIVE' if ok else 'DEAD'} {dt:.1f}s {err}", flush=True)
        results.append({"model": m, "status": "alive" if ok else "dead",
                        "latency_s": round(dt, 1), "note": err})
    except subprocess.TimeoutExpired:
        print(f"{m}: TIMEOUT after 40s", flush=True)
        results.append({"model": m, "status": "timeout", "latency_s": None})
    time.sleep(2)

json.dump(results, open("/tmp/nim-probe-20260914.json", "w"), indent=1)
print("saved /tmp/nim-probe-20260914.json")
