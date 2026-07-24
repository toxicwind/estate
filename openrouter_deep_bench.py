#!/usr/bin/env python3
"""
Deep OpenRouter + Nemotron 3 Ultra Free benchmark with full pipeline analysis
"""
import asyncio
import aiohttp
import os
import time
import statistics
import json

API_KEY = os.environ.get("OPENROUTER_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://zed.dev",
    "X-Title": "Zed Editor",
}
BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"

async def time_it(coro):
    start = time.perf_counter()
    result = await coro
    elapsed = (time.perf_counter() - start) * 1000
    return elapsed, result

async def stream_benchmark(session, payload, label):
    """Full streaming benchmark: DNS, TLS, connect, first_chunk, chunks, total"""
    start = time.perf_counter()
    first_chunk = None
    chunks = 0
    async with session.post(f"{BASE_URL}/chat/completions", headers=HEADERS, json=payload) as r:
        async for line in r.content:
            line = line.decode().strip()
            if line.startswith("data: "):
                if first_chunk is None:
                    first_chunk = (time.perf_counter() - start) * 1000
                if line != "data: [DONE]":
                    chunks += 1
    total = (time.perf_counter() - start) * 1000
    connect = first_chunk if first_chunk else total
    return {
        "label": label,
        "total_ms": round(total, 1),
        "first_chunk_ms": round(first_chunk, 1) if first_chunk else None,
        "connect_ms": round(connect, 1),
        "stream_ms": round(total - connect, 1) if first_chunk else 0,
        "chunks": chunks,
        "status": r.status,
    }

async def nonstream_benchmark(session, payload, label):
    """Non-streaming benchmark"""
    start = time.perf_counter()
    async with session.post(f"{BASE_URL}/chat/completions", headers=HEADERS, json=payload) as r:
        data = await r.json()
        total = (time.perf_counter() - start) * 1000
    return {
        "label": label,
        "total_ms": round(total, 1),
        "status": r.status,
        "choices": len(data.get("choices", [])),
    }

async def models_list_benchmark(session, label):
    """Models list benchmark (what Zed does on startup)"""
    start = time.perf_counter()
    async with session.get(f"{BASE_URL}/models", headers=HEADERS) as r:
        data = await r.json()
        total = (time.perf_counter() - start) * 1000
    return {
        "label": label,
        "total_ms": round(total, 1),
        "status": r.status,
        "model_count": len(data.get("data", [])),
    }

async def run_all():
    if not API_KEY:
        print("ERROR: OPENROUTER_API_KEY not set")
        return

    print("=" * 70)
    print("OPENROUTER NEMOTRON 3 ULTRA FREE - DEEP BENCHMARK")
    print("=" * 70)

    async with aiohttp.ClientSession() as session:
        # 1. Models list (cold + warm)
        print("\n[1] MODELS LIST (Zed startup fetches this)")
        for i in range(3):
            r = await models_list_benchmark(session, f"cold_{i+1}")
            print(f"  {r['label']}: {r['total_ms']}ms, {r['model_count']} models, status={r['status']}")

        times = []
        for i in range(5):
            r = await models_list_benchmark(session, f"warm_{i+1}")
            times.append(r['total_ms'])
            print(f"  {r['label']}: {r['total_ms']}ms")
        print(f"  AVG: {statistics.mean(times):.1f}ms, STDEV: {statistics.stdev(times):.1f}ms")

        # 2. Non-streaming (baseline)
        print("\n[2] NON-STREAMING chat/completions")
        payload_ns = {"model": MODEL, "messages": [{"role": "user", "content": "Reply with exactly: OK"}], "max_tokens": 16, "stream": False, "temperature": 0}
        times = []
        for i in range(5):
            r = await nonstream_benchmark(session, payload_ns, f"ns_{i+1}")
            times.append(r['total_ms'])
            print(f"  {r['label']}: {r['total_ms']}ms, status={r['status']}, choices={r['choices']}")
        print(f"  AVG: {statistics.mean(times):.1f}ms, STDEV: {statistics.stdev(times):.1f}ms")

        # 3. Streaming (what Zed actually uses)
        print("\n[3] STREAMING chat/completions (Zed default)")
        payload_s = {**payload_ns, "stream": True}
        results = []
        for i in range(10):
            r = await stream_benchmark(session, payload_s, f"stream_{i+1}")
            results.append(r)
            print(f"  {r['label']}: connect={r['connect_ms']}ms first_chunk={r['first_chunk_ms']}ms stream={r['stream_ms']}ms total={r['total_ms']}ms chunks={r['chunks']}")

        # Analyze streaming
        first_chunks = [r['first_chunk_ms'] for r in results if r['first_chunk_ms']]
        totals = [r['total_ms'] for r in results]
        connects = [r['connect_ms'] for r in results]
        streams = [r['stream_ms'] for r in results if r['stream_ms'] > 0]

        print(f"\n  SUMMARY (streaming):")
        print(f"    Connect/headers avg: {statistics.mean(connects):.1f}ms")
        print(f"    First chunk avg:     {statistics.mean(first_chunks):.1f}ms" if first_chunks else "    First chunk: N/A")
        print(f"    Stream body avg:     {statistics.mean(streams):.1f}ms" if streams else "    Stream body: N/A")
        print(f"    Total avg:           {statistics.mean(totals):.1f}ms")
        print(f"    Total p95:           {sorted(totals)[int(len(totals)*0.95)]:.1f}ms")
        print(f"    Chunks per response: {statistics.mean([r['chunks'] for r in results]):.1f}")

        # 4. Test with reasoning_effort (Nemotron supports this)
        print("\n[4] STREAMING with reasoning_effort='high'")
        payload_reason = {**payload_s, "reasoning_effort": "high"}
        times = []
        for i in range(3):
            r = await stream_benchmark(session, payload_reason, f"reason_{i+1}")
            times.append(r['total_ms'])
            print(f"  {r['label']}: total={r['total_ms']}ms first_chunk={r['first_chunk_ms']}ms chunks={r['chunks']}")
        print(f"  AVG: {statistics.mean(times):.1f}ms")

        # 5. Compare with specific provider routing
        print("\n[5] PROVIDER routing: only=openai")
        payload_prov = {**payload_s, "provider": {"only": ["openai"]}}
        times = []
        for i in range(3):
            r = await stream_benchmark(session, payload_prov, f"prov_openai_{i+1}")
            times.append(r['total_ms'])
            print(f"  {r['label']}: total={r['total_ms']}ms first_chunk={r['first_chunk_ms']}ms")
        print(f"  AVG: {statistics.mean(times):.1f}ms")

        # 6. Test with transforms (Zed uses these)
        print("\n[6] TRANSFORMS: middle-out (Zed default for long contexts)")
        payload_xform = {**payload_s, "transforms": ["middle-out"]}
        times = []
        for i in range(3):
            r = await stream_benchmark(session, payload_xform, f"xform_{i+1}")
            times.append(r['total_ms'])
            print(f"  {r['label']}: total={r['total_ms']}ms first_chunk={r['first_chunk_ms']}ms")
        print(f"  AVG: {statistics.mean(times):.1f}ms")

        # 7. Raw TCP/TLS timing (no HTTP)
        print("\n[7] RAW TCP/TLS to openrouter.ai:443")
        import socket
        import ssl
        times_tcp = []
        for i in range(5):
            start = time.perf_counter()
            sock = socket.create_connection(("openrouter.ai", 443), timeout=5)
            ctx = ssl.create_default_context()
            ssock = ctx.wrap_socket(sock, server_hostname="openrouter.ai")
            ssock.do_handshake()
            total = (time.perf_counter() - start) * 1000
            times_tcp.append(total)
            ssock.close()
            print(f"  tcp_tls_{i+1}: {total:.1f}ms")
        print(f"  AVG: {statistics.mean(times_tcp):.1f}ms, STDEV: {statistics.stdev(times_tcp):.1f}ms")

        # 8. DNS timing
        print("\n[8] DNS resolution")
        import socket as s
        times_dns = []
        for i in range(5):
            start = time.perf_counter()
            s.getaddrinfo("openrouter.ai", 443)
            total = (time.perf_counter() - start) * 1000
            times_dns.append(total)
            print(f"  dns_{i+1}: {total:.1f}ms")
        print(f"  AVG: {statistics.mean(times_dns):.1f}ms")

if __name__ == "__main__":
    asyncio.run(run_all())
