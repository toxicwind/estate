#!/usr/bin/env python3
"""Shared model-call + code-extraction helpers for the t3-e2e harness."""
import json, re, time, urllib.request

ROUTER = "http://127.0.0.1:25104/v1/chat/completions"
DIRECT = "http://127.0.0.1:25100/v1/chat/completions"  # llama-swap, same model ids, no router rate limit
# router lane id -> direct model id (same weights, local serve)
DIRECT_MODEL = {
    "mradermacher/qwen3.5-9b-deepseek-v4-flash-i1-q4_k_m": "toolcall-local/qwen3.5-9b-tool",
}
GEN_TIMEOUT_S = 240
MAX_TOKENS = 3000  # single-file tasks fit; keeps slow lanes under the ~90s bridge idle ceiling

def _post(url, model, system, user, max_tokens, timeout):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }).encode()
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.load(r)
    text = d["choices"][0]["message"]["content"] or ""
    return text, round(time.time() - t0, 2)

def chat(model, system, user, max_tokens=MAX_TOKENS, timeout=GEN_TIMEOUT_S):
    """One chat completion. Primary: direct llama-swap (:25100); fallback: router (:25104).

    The router 503s with rate_limited when its hedged upstreams throttle; the
    direct path serves the same model ids locally. Lane identity (model id) is
    preserved for reporting; only the transport changes.
    """
    direct_model = DIRECT_MODEL.get(model, model)
    t0 = time.time()
    try:
        return _post(DIRECT, direct_model, system, user, max_tokens, timeout)
    except Exception as e1:
        try:
            return _post(ROUTER, model, system, user, max_tokens, timeout)
        except Exception as e2:
            return (f"__TRANSPORT_ERROR__: direct={e1} router={e2}",
                    round(time.time() - t0, 2))

def extract_python(text):
    """Pull the single python fenced block; fallbacks for sloppy models."""
    m = re.search(r"```python\s*\n(.*?)```", text, re.S)
    if m:
        return m.group(1).strip()
    m = re.search(r"```\s*\n(.*?)```", text, re.S)
    if m and ("def " in m.group(1) or "class " in m.group(1) or "import " in m.group(1)):
        return m.group(1).strip()
    # last resort: whole response if it looks like pure code
    lines = [l for l in text.splitlines()
             if l.strip() and not l.strip().startswith("#")]
    if lines and sum(1 for l in lines if re.match(r"^\s*(def |class |import |from |@)", l)) >= 1:
        return text.strip()
    return None

GEN_SYSTEM = ("You are a precise Python engineer. Output exactly one fenced "
              "```python code block containing the complete file. No prose outside the fence.")

def gen_prompt(filename, problem_md):
    return (f"Write ONLY the Python file `{filename}` implementing this task:\n\n"
            f"{problem_md}\n\n"
            f"Rules: output exactly one ```python fenced block with the complete file, "
            f"nothing else. Standard library only.")
