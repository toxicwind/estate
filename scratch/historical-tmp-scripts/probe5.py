import json, subprocess, time

def probe(model, base="http://127.0.0.1:25100", timeout=45):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "Reply with the single word PONG."}],
        "max_tokens": 16,
    })
    t0 = time.time()
    try:
        p = subprocess.run(
            ["curl", "-s", "-m", str(timeout), "-w", "\n%{http_code}",
             base + "/v1/chat/completions",
             "-H", "Content-Type: application/json", "-d", body],
            capture_output=True, text=True, timeout=timeout + 10)
    except subprocess.TimeoutExpired:
        print(f"{model}: TIMEOUT")
        return
    ms = int((time.time() - t0) * 1000)
    code = p.stdout.strip().rsplit("\n", 1)[-1] if p.stdout.strip() else "000"
    print(f"{model}: HTTP {code} {ms}ms")

for m in ["oracle-judge-a", "oracle-judge-b", "oracle-judge-c",
          "fast", "tiny", "qwen-flash-da-128k"]:
    probe(m)
probe("kimi-auto", base="http://127.0.0.1:25153")
probe("free", base="http://127.0.0.1:25104")
