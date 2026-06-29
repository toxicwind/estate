#!/usr/bin/env python3
import time
import json
import requests

url = "http://127.0.0.1:25001/v1/chat/completions"

# Create a long prompt of ~4,000 tokens
base_text = "The quick brown fox jumps over the lazy dog. " * 100  # ~900 tokens
long_context = base_text * 4  # ~3600 tokens
prompt = f"System: Analyze the following text carefully.\n\n{long_context}\n\nUser: Summarize the main theme of the fox story in one sentence."

print("=== PROMPT CACHE BENCHMARK ===")
print(f"Endpoint: {url}")
print(f"Payload Size: {len(prompt)} characters (~4000 tokens)")

# Turn 1: Uncached prefill
print("\n--- Turn 1: Sending prompt (Uncached) ---")
t0 = time.time()
r1 = requests.post(
    url,
    json={
        "model": "local",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 50
    }
)
t1 = time.time()
dt1 = t1 - t0

if r1.status_code == 200:
    res1 = r1.json()
    completion_tokens = res1.get("usage", {}).get("completion_tokens", 0)
    prompt_tokens = res1.get("usage", {}).get("prompt_tokens", 0)
    timings = res1.get("timings", {})
    prompt_ms = timings.get("prompt_ms", dt1 * 1000)
    print(f"Status: OK")
    print(f"Total Time: {dt1:.3f} seconds")
    print(f"Tokens: Prompt={prompt_tokens}, Completion={completion_tokens}")
    print(f"Server-reported Prompt Eval: {prompt_ms/1000:.3f} seconds")
    print(f"Content: {res1['choices'][0]['message']['content']}")
else:
    print(f"Error {r1.status_code}: {r1.text}")
    exit(1)

# Turn 2: Cached prefill (exact same prefix/prompt)
print("\n--- Turn 2: Sending exact same prompt (Expected to hit cache) ---")
t0 = time.time()
r2 = requests.post(
    url,
    json={
        "model": "local",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 50
    }
)
t2 = time.time()
dt2 = t2 - t0

if r2.status_code == 200:
    res2 = r2.json()
    completion_tokens = res2.get("usage", {}).get("completion_tokens", 0)
    prompt_tokens = res2.get("usage", {}).get("prompt_tokens", 0)
    cached_tokens = res2.get("usage", {}).get("prompt_tokens_details", {}).get("cached_tokens", 0)
    timings = res2.get("timings", {})
    prompt_ms = timings.get("prompt_ms", dt2 * 1000)
    print(f"Status: OK")
    print(f"Total Time: {dt2:.3f} seconds")
    print(f"Tokens: Prompt={prompt_tokens} (Cached={cached_tokens}), Completion={completion_tokens}")
    print(f"Server-reported Prompt Eval: {prompt_ms/1000:.3f} seconds")
    print(f"Content: {res2['choices'][0]['message']['content']}")
    
    # Calculate Cache efficiency
    if prompt_tokens > 0:
        hit_ratio = (cached_tokens / prompt_tokens) * 100
        print(f"\nCache Hit Ratio: {hit_ratio:.1f}%")
        speedup = dt1 / dt2 if dt2 > 0 else 0
        print(f"Latency Reduction Speedup: {speedup:.1f}x")
        if hit_ratio > 90:
            print("SUCCESS: Prompt caching is active and functional!")
        else:
            print("WARNING: Prompt caching did NOT hit. Cache might be disabled or invalidated.")
else:
    print(f"Error {r2.status_code}: {r2.text}")
