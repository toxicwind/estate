"""Direct Mistral benchmark — measures GuideLLM-equivalent metrics via live API.

GuideLLM 0.8.0's OpenAI backend sends array content blocks which Mistral's
API rejects with 422. This script measures the same core metrics directly:
requests/sec, tokens/sec, TTFT, mean/p50/p99 latency, error rate.

Key never leaves this process. Reads from /home/toxic/.secrets.
"""
import json
import statistics
import sys
import time
import urllib.request

MODELS = [
    "ministral-3b-latest",
    "ministral-8b-latest",
    "ministral-14b-latest",
    "codestral-latest",
    "mistral-code-latest",
]

BASE = "https://api.mistral.ai/v1"
N_REQUESTS = 10
PROMPT = "Write a haiku about debugging. Exactly three lines."


def read_key():
    with open("/home/toxic/.secrets") as f:
        for line in f:
            line = line.strip()
            if line.startswith("MISTRAL_API_KEY="):
                return line.split("=", 1)[1].strip().strip("'\"")
    raise RuntimeError("MISTRAL_API_KEY not found")


def percentile(data, p):
    if not data:
        return 0
    s = sorted(data)
    k = (len(s) - 1) * p / 100
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


def benchmark_model(model, api_key):
    latencies = []
    ttfts = []
    prompt_tokens = []
    completion_tokens = []
    errors = 0

    for i in range(N_REQUESTS):
        body = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": PROMPT}],
            "max_tokens": 100,
            "stream": True,
        }).encode()

        req = urllib.request.Request(
            f"{BASE}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        start = time.perf_counter()
        first_token_time = None
        chunks = []

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                for line in resp:
                    line = line.decode("utf-8", errors="ignore").strip()
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    if first_token_time is None:
                        first_token_time = time.perf_counter()
                    chunks.append(data)
            end = time.perf_counter()

            # Parse usage from final chunk if available
            total_text = "".join(chunks)

            latencies.append(end - start)
            if first_token_time:
                ttfts.append(first_token_time - start)

            # Rough token estimate (will refine from usage if present)
            prompt_tokens.append(len(PROMPT.split()) * 1.3)

        except Exception as e:
            errors += 1
            print(f"  request {i+1} error: {type(e).__name__}", flush=True)

    total_time = sum(latencies) if latencies else 0
    n_success = len(latencies)

    return {
        "model": model,
        "requests": N_REQUESTS,
        "successful": n_success,
        "errors": errors,
        "error_rate": errors / N_REQUESTS,
        "requests_per_sec": n_success / total_time if total_time > 0 else 0,
        "latency": {
            "mean": statistics.mean(latencies) if latencies else 0,
            "p50": percentile(latencies, 50),
            "p99": percentile(latencies, 99),
            "min": min(latencies) if latencies else 0,
            "max": max(latencies) if latencies else 0,
        },
        "ttft": {
            "mean": statistics.mean(ttfts) if ttfts else 0,
            "p50": percentile(ttfts, 50),
            "p99": percentile(ttfts, 99),
        },
    }


def benchmark_model_nonstream(model, api_key):
    """Non-streaming variant to get exact token usage."""
    latencies = []
    total_prompt = 0
    total_completion = 0
    errors = 0

    for i in range(5):
        body = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": PROMPT}],
            "max_tokens": 100,
            "stream": False,
        }).encode()

        req = urllib.request.Request(
            f"{BASE}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        start = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
            end = time.perf_counter()
            latencies.append(end - start)
            usage = data.get("usage", {})
            total_prompt += usage.get("prompt_tokens", 0)
            total_completion += usage.get("completion_tokens", 0)
        except Exception as e:
            errors += 1

    total_time = sum(latencies) if latencies else 0
    return {
        "nonstream_latency_mean": statistics.mean(latencies) if latencies else 0,
        "avg_prompt_tokens": total_prompt / max(len(latencies), 1),
        "avg_completion_tokens": total_completion / max(len(latencies), 1),
        "tokens_per_sec": total_completion / total_time if total_time > 0 else 0,
        "nonstream_errors": errors,
    }


def main():
    api_key = read_key()
    print(f"key loaded, len={len(api_key)}", flush=True)
    results = []

    for model in MODELS:
        print(f"--- {model} (streaming) ---", flush=True)
        r = benchmark_model(model, api_key)
        print(f"--- {model} (non-streaming usage) ---", flush=True)
        r.update(benchmark_model_nonstream(model, api_key))
        results.append(r)
        print(f"OK {model}: {r['successful']}/{r['requests']} "
              f"rps={r['requests_per_sec']:.2f} "
              f"p50={r['latency']['p50']:.3f}s", flush=True)

    with open("/tmp/mistral-direct-benchmark.json", "w") as f:
        json.dump(results, f, indent=2)
    print("results written to /tmp/mistral-direct-benchmark.json", flush=True)


if __name__ == "__main__":
    main()
