import json, subprocess, time

def probe(model):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": 8,
    })
    t0 = time.time()
    p = subprocess.run(
        ["curl", "-s", "-m", "30", "-w", "\n%{http_code}",
         "http://127.0.0.1:25100/v1/chat/completions",
         "-H", "Content-Type: application/json", "-d", body],
        capture_output=True, text=True)
    ms = int((time.time() - t0) * 1000)
    code = p.stdout.strip().rsplit("\n", 1)[-1]
    print(f"{model}: HTTP {code} {ms}ms")

for m in ["kimi-k2.6", "moonshot/kimi-k2.6", "kimi-k2.7-code",
          "openrouter-pool/moonshotai/kimi-k2.6", "bogus-model-xyz"]:
    probe(m)
