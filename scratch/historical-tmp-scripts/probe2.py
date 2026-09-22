import json, subprocess, time

def probe(model, base="http://127.0.0.1:25100", timeout=60):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "Reply with the single word PONG."}],
        "max_tokens": 16,
    })
    t0 = time.time()
    p = subprocess.run(
        ["curl", "-s", "-m", str(timeout), "-w", "\n%{http_code}",
         base + "/v1/chat/completions",
         "-H", "Content-Type: application/json", "-d", body],
        capture_output=True, text=True)
    ms = int((time.time() - t0) * 1000)
    out = p.stdout
    code = out.strip().rsplit("\n", 1)[-1] if out.strip() else "000"
    payload = out.rsplit("\n", 1)[0][:150] if "\n" in out else ""
    try:
        d = json.loads(payload)
        ch = d.get("choices", [{}])[0].get("message", {}).get("content", "")
        sub = "SUBSTANCE" if ch and ch.strip() else "EMPTY"
    except Exception:
        sub = "ERR"
    print(f"{model}: HTTP {code} {ms}ms {sub}")

for m in ["beellama/gemma-96k", "oracle-judge-local", "tiny", "qwen-flash-da-128k",
          "nex-agi/nex-n2.5-pro:free", "gemini-3-flash-preview"]:
    probe(m)
probe("kimi-auto", base="http://127.0.0.1:25153")
