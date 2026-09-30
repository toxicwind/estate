import json, os, subprocess, sys, time

def probe(name, url, token, model):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "Reply with the single word PONG."}],
        "max_tokens": 16,
    })
    t0 = time.time()
    p = subprocess.run(
        ["curl", "-s", "-m", "45", "-w", "\n%{http_code}",
         url,
         "-H", "Authorization: Bearer " + token,
         "-H", "Content-Type: application/json",
         "-d", body],
        capture_output=True, text=True)
    ms = int((time.time() - t0) * 1000)
    lines = p.stdout.rsplit("\n", 2)
    code = lines[-1].strip() if lines else "000"
    payload = "\n".join(lines[:-1])[:200]
    try:
        d = json.loads(payload)
        ch = d.get("choices", [{}])[0].get("message", {}).get("content", "")
        substance = "SUBSTANCE" if ch and ch.strip() else "EMPTY"
    except Exception:
        substance = "ERR"
    print(f"{name}: HTTP {code} {ms}ms {substance} :: {payload[:120]}")

# source .secrets without printing
env = {}
with open("/home/toxic/.secrets") as f:
    for line in f:
        line = line.strip()
        if line.startswith("export "):
            k, _, v = line[7:].partition("=")
            env[k] = v.strip().strip('"').strip("'")

tok1 = env.get("HF_TOKEN_1", "")
tok = env.get("HF_TOKEN", "")
if tok1:
    probe("hf-router(HF_TOKEN_1)/moonshotai/Kimi-K3",
          "https://router.huggingface.co/v1/chat/completions", tok1,
          "moonshotai/Kimi-K3")
if tok and tok != tok1:
    probe("hf-router(HF_TOKEN)/moonshotai/Kimi-K3",
          "https://router.huggingface.co/v1/chat/completions", tok,
          "moonshotai/Kimi-K3")
