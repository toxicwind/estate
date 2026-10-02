#!/usr/bin/env python3
"""resurrect-probe.py — cheap hypothesis: strip :batch, probe base IDs live.
Reads OPENROUTER_API_KEY_FREE from /home/toxic/.secrets by name. Never prints the key.
Outputs JSONL to /tmp/resurrect-results.jsonl + prints a summary table.
"""
import asyncio
import aiohttp
import json
import time

SECRETS = "/home/toxic/.secrets"
OUT = "/tmp/resurrect-results.jsonl"
CEIL = 60
WORKERS = 16

DEAD = """openai/gpt-6-astra:batch
openai/gpt-6-astra-pro:batch
anthropic/claude-fable-5.1:batch
meta/muse-spark-1.3-contributor
google/gemini-3.8-flash:batch
z-ai/glm-5.3-flash:batch
deepseek/deepseek-v4-flash-vision-exp:batch
meta/muse-spark-1.2-contributor
z-ai/glm-5.3:batch
google/gemini-3.7-flash:batch
deepseek/deepseek-v4-pro-0813:batch
qwen/qwen3.8-2.4t-a95b:batch
sakana/sakana-namazu
meta/muse-glimmer-30b:batch
deepseek/deepseek-v4-flash-0731:batch
anthropic/claude-opus-5:batch
google/gemini-3.6-flash:batch
google/gemini-3.5-flash-lite:batch
thinkingmachines/inkling:batch
moonshotai/kimi-k3:batch
openai/gpt-5.6-luna:batch
openai/gpt-5.6-terra-pro:batch
openai/gpt-5.6-luna-pro:batch
openai/gpt-5.6-terra:batch
openai/gpt-5.6-sol-pro:batch
openai/gpt-5.6-sol:batch
anthropic/claude-sonnet-5:batch
z-ai/glm-5.2:batch
anthropic/claude-fable-5:batch
minimax/minimax-m3:batch
anthropic/claude-opus-4.8:batch
google/gemini-3.5-flash:batch
google/gemini-3.1-flash-lite:batch
x-ai/grok-4.3:batch
mistralai/mistral-medium-3-5:batch
openai/gpt-5.5-pro:batch
openai/gpt-5.5:batch
anthropic/claude-opus-4.7:batch
openai/gpt-5.4-nano:batch
mistralai/mistral-small-2603:batch
openai/gpt-5.4-mini:batch
qwen/qwen3.5-9b:batch
openai/gpt-5.4-pro:batch
openai/gpt-5.4:batch
google/gemini-3.1-pro-preview:batch
anthropic/claude-sonnet-4.6:batch
anthropic/claude-opus-4.6:batch
google/gemini-3-flash-preview:batch
openai/gpt-5.2-chat
openai/gpt-5.2:batch
openai/gpt-5.2-pro:batch
mistralai/ministral-8b-2512:batch
mistralai/mistral-large-2512:batch
anthropic/claude-opus-4.5:batch
openai/gpt-5.1:batch
anthropic/claude-haiku-4.5:batch
openai/gpt-5-pro:batch
anthropic/claude-sonnet-4.5:batch
mistralai/mistral-medium-3.1:batch
openai/gpt-5:batch
openai/gpt-5-mini:batch
openai/gpt-5-nano:batch
openai/gpt-oss-120b:batch
anthropic/claude-opus-4.1:batch
mistralai/codestral-2508:batch
google/gemini-2.5-flash-lite:batch
google/gemini-2.5-flash:batch
google/gemini-2.5-pro:batch
openai/o3:batch
openai/o4-mini:batch
openai/gpt-4.1:batch
openai/gpt-4.1-mini:batch
openai/gpt-4.1-nano:batch
openai/o3-mini:batch
openai/gpt-4o-mini:batch
openai/gpt-4o:batch
openai/gpt-4-turbo:batch
openai/gpt-3.5-turbo:batch""".split()

PROMPT = "Reply with exactly the word OK and nothing else."


def load_key():
    for line in open(SECRETS):
        line = line.strip()
        if line.startswith("export "):
            line = line[7:]
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            if k.strip() == "OPENROUTER_API_KEY_FREE":
                return v.strip().strip('"').strip("'")
    raise SystemExit("OPENROUTER_API_KEY_FREE not found")


KEY = load_key()
BASE = "https://openrouter.ai/api/v1"
HDR = {"Authorization": "Bearer " + KEY, "Content-Type": "application/json",
       "HTTP-Referer": "https://github.com/toxicwind/sovereign-projects",
       "X-Title": "dead-model-resurrect"}


def classify(status):
    return {200: "works", 402: "paid", 404: "dead", 403: "forbidden",
            429: "throttled", 400: "malformed"}.get(status, f"http{status}")


async def probe(session, sem, model):
    async with sem:
        t0 = time.time()
        rec = {"candidate": model, "ok": False, "http": None,
               "latency_ms": 0.0, "cls": "error", "note": "",
               "content_preview": ""}
        shape = None
        retried = False
        for _ in range(3):
            body = {"model": model,
                    "messages": [{"role": "user", "content": PROMPT}],
                    "temperature": 0}
            if shape == "mctok":
                body["max_completion_tokens"] = 64
            else:
                body["max_tokens"] = 64
            if shape == "notemp":
                body.pop("temperature", None)
            try:
                async with session.post(
                        BASE + "/chat/completions", headers=HDR, json=body,
                        timeout=aiohttp.ClientTimeout(total=CEIL)) as r:
                    status = r.status
                    txt = await r.text()
                    rec["latency_ms"] = round((time.time() - t0) * 1000, 1)
                    rec["http"] = status
                    if status == 200:
                        try:
                            d = json.loads(txt)
                        except Exception:
                            rec.update(cls="malformed", note="200 non-JSON")
                            return rec
                        ch = (d.get("choices") or [{}])[0]
                        msg = ch.get("message", {}) or {}
                        content = str(msg.get("content") or "").strip()
                        reason = str(msg.get("reasoning") or
                                     msg.get("reasoning_content") or "")
                        rec.update(ok=True, cls="works",
                                   content_preview=content[:80])
                        if not content and reason.strip():
                            rec["note"] = "reasoning-only"
                        return rec
                    low = txt[:400].lower()
                    if status == 400:
                        if "max_completion_tokens" in low and shape is None:
                            shape = "mctok"
                            continue
                        if "temperature" in low and shape is None:
                            shape = "notemp"
                            continue
                    if status in (429, 500, 502, 503) and not retried:
                        retried = True
                        continue
                    rec["cls"] = classify(status)
                    rec["note"] = txt[:120].replace("\n", " ")
                    return rec
            except asyncio.TimeoutError:
                rec.update(cls="timeout", note=f"timeout {CEIL}s")
                return rec
            except Exception as e:
                rec.update(cls="error", note=str(e)[:100])
                return rec
        return rec


async def main():
    # candidates: strip :batch; keep the 4 non-batch as-is
    jobs = []
    for d in DEAD:
        cand = d[:-6] if d.endswith(":batch") else d
        jobs.append((d, cand))
    async with aiohttp.ClientSession() as session:
        # 1. catalog snapshot (one call) -> which candidates are listed?
        async with session.get(BASE + "/models", headers=HDR,
                               timeout=aiohttp.ClientTimeout(total=40)) as r:
            r.raise_for_status()
            catalog = {m["id"] for m in (await r.json())["data"]}
        print(f"catalog size: {len(catalog)}", flush=True)
        # 2. probe every candidate
        sem = asyncio.Semaphore(WORKERS)
        results = await asyncio.gather(
            *(probe(session, sem, cand) for _, cand in jobs))
    with open(OUT, "w") as f:
        for (dead, cand), rec in zip(jobs, results):
            rec["dead_id"] = dead
            rec["in_catalog"] = cand in catalog
            f.write(json.dumps(rec) + "\n")
    # summary
    from collections import Counter
    c = Counter(r["cls"] for r in results)
    print("CLASS COUNTS:", dict(c), flush=True)
    print("\nWORKS:", flush=True)
    for (dead, cand), rec in zip(jobs, results):
        if rec["ok"]:
            print(f"  {dead} -> {cand} [{rec['latency_ms']}ms] "
                  f"catalog={rec['in_catalog']} {rec['content_preview']!r}",
                  flush=True)
    print("\nSTILL NOT WORKS:", flush=True)
    for (dead, cand), rec in zip(jobs, results):
        if not rec["ok"]:
            print(f"  {dead} -> {cand} cls={rec['cls']} http={rec['http']} "
                  f"catalog={rec['in_catalog']} note={rec['note'][:60]}",
                  flush=True)


if __name__ == "__main__":
    asyncio.run(main())
