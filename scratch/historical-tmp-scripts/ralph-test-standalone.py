import json, os, time, urllib.request

RALPH_MODEL_CANDIDATES = [
    os.environ.get("RALPH_MODEL") or "",
    "kimi-k3-nim",
    "gemini-3-flash-preview",
]
_ralph_model_cache = {"model": None, "ts": 0.0}
RALPH_MODEL_CACHE_S = 300


def _resolve_ralph_model(base_url, timeout=15):
    now = time.time()
    if (_ralph_model_cache["model"]
            and now - _ralph_model_cache["ts"] < RALPH_MODEL_CACHE_S):
        return _ralph_model_cache["model"]
    candidates = [c for c in RALPH_MODEL_CANDIDATES if c]
    base = base_url.rstrip("/")
    for cand in candidates:
        try:
            body = json.dumps({
                "model": cand,
                "messages": [{"role": "user", "content": "Reply with: ok"}],
                "max_tokens": 5,
            }).encode()
            req = urllib.request.Request(
                base + "/chat/completions", data=body,
                headers={"Content-Type": "application/json",
                         "User-Agent": "oracle-market-bidder"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                payload = json.loads(r.read().decode("utf-8", "replace"))
            if payload.get("choices"):
                _ralph_model_cache.update(model=cand, ts=now)
                return cand
            else:
                print("candidate", cand, "-> no choices:",
                      str(payload)[:120])
        except Exception as e:
            print("candidate", cand, "->", type(e).__name__,
                  str(e)[:100])
            continue
    model = candidates[0] if candidates else "kimi-k3-nim"
    _ralph_model_cache.update(model=model, ts=now)
    return model


if __name__ == "__main__":
    m = _resolve_ralph_model("http://127.0.0.1:25100/v1", timeout=25)
    print("RESOLVED:", m)
