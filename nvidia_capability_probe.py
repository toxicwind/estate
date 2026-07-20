#!/usr/bin/env python3
"""
nvidia_capability_probe.py  (v3 — endpoint-family aware)
=========================================================
Discover and capability-test every model reachable by an NVIDIA NIM API key on
https://integrate.api.nvidia.com/v1.

WHY v2 was wrong: NVIDIA NIM is NOT only chat. The catalog mixes many endpoint
families (chat, vision, embeddings, rerank, speech, safety, biology, video,
document, translation, audio, weather). Probing only /v1/chat/completions and
calling everything else "not_deployed" was incorrect — those models ARE deployed,
just on a different endpoint. This v3 classifies each model by ENDPOINT FAMILY
(using the authoritative nim-client catalog as ground truth) and probes the
CORRECT endpoint per family.

Endpoint families (from nim-client/src/models.ts + client.ts):
  chat      -> /v1/chat/completions
  vision    -> /v1/chat/completions (multimodal; image input)
  embeddings-> /v1/embeddings
  rerank    -> /v1/ranking   (NOTE: not /rerank; often NOT on free tier)
  speech/translation/audio/biology/video/document/weather/safety -> own endpoints

STATE MACHINE (per family):
  For chat/vision: CHAT_OK / CHAT_DENIED / CHAT_NOT_DEPLOYED / CHAT_UNSUPPORTED /
                   CHAT_SERVER_ERR / CHAT_CONN_TIMEOUT / CHAT_CONN_OTHER / CHAT_WATCHDOG
  For embeddings:  EMB_OK / EMB_DENIED / EMB_NOT_DEPLOYED / EMB_UNSUPPORTED /
                   EMB_SERVER_ERR / EMB_CONN_TIMEOUT / EMB_CONN_OTHER / EMB_WATCHDOG
  For rerank:      RERANK_OK / ... (same pattern)
  (safety/pii/translation use chat with special prompts -> treated as chat)

A model is USABLE if its family's *_OK state holds. Transient states
(CONN_TIMEOUT/CONN_OTHER/SERVER_ERR/WATCHDOG) are separated from permanent
denials (DENIED / NOT_DEPLOYED / UNSUPPORTED).

Watchdog: hard per-model wall-clock cap (NVIDIA_PROBE_TIMEOUT, default 25s).
Resume: finished ids cached in nvidia_models_report.json; re-run skips them.
Purge: NVIDIA_PROBE_PURGE=1 drops transient states before re-probing.

Env: NVIDIA_API_KEY, NVIDIA_PROBE_MAX, NVIDIA_PROBE_ONLY, NVIDIA_PROBE_SKIP,
     NVIDIA_PROBE_TIMEOUT, NVIDIA_PROBE_PURGE
"""

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout

BASE = "https://integrate.api.nvidia.com/v1"
KEY = os.environ.get("NVIDIA_API_KEY") or os.environ.get("NVIDIA_NIM_API_KEY")
if not KEY:
    print("ERROR: set NVIDIA_API_KEY", file=sys.stderr)
    sys.exit(1)

MAX = int(os.environ.get("NVIDIA_PROBE_MAX", "0") or 0)
ONLY = {
    x.strip()
    for x in (os.environ.get("NVIDIA_PROBE_ONLY") or "").split(",")
    if x.strip()
}
SKIP = {
    x.strip()
    for x in (os.environ.get("NVIDIA_PROBE_SKIP") or "").split(",")
    if x.strip()
}
MODEL_TIMEOUT = int(os.environ.get("NVIDIA_PROBE_TIMEOUT", "25") or 25)
PURGE = os.environ.get("NVIDIA_PROBE_PURGE") == "1"

PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M8AAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"}
REPORT_PATH = "nvidia_models_report.json"

# Endpoint family catalog (authoritative, from nim-client/src/models.ts).
# Maps model id -> family. Anything not listed is probed as chat (best effort).
FAMILY = {}


def _add(fam, ids):
    for i in ids:
        FAMILY[i] = fam


_add(
    "chat",
    [
        "nvidia/nemotron-3-ultra-550b-a55b",
        "nvidia/llama-3.3-nemotron-super-49b-v1.5",
        "nvidia/llama-3.1-nemotron-nano-8b-v1",
        "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
        "meta/llama-3.3-70b-instruct",
        "meta/llama-3.1-70b-instruct",
        "meta/llama-3.1-8b-instruct",
        "meta/llama-3.1-405b-instruct",
        "mistralai/mistral-large-3-675b-instruct-2512",
        "mistralai/mistral-7b-instruct-v0.3",
        "mistralai/mixtral-8x7b-instruct-v0.1",
        "mistralai/mixtral-8x22b-instruct-v0.1",
        "deepseek-ai/deepseek-v4-flash",
        "qwen/qwen3-coder-480b-a35b-instruct",
        "qwen/qwen2.5-72b-instruct",
        "microsoft/phi-4-multimodal-instruct",
        "google/gemma-2-27b-it",
        "writer/palmyra-med-70b-32k",
        "writer/palmyra-fin-70b-32k",
        "mistralai/codestral-22b-instruct-v0.1",
        "bytedance/seed-oss-36b-instruct",
        "stepfun-ai/step-3.5-flash",
        "minimaxai/minimax-m2.7",
        "nvidia/nemotron-mini-4b-instruct",
        "google/gemma-3n-e4b-it",
        "google/gemma-3n-e2b-it",
        "google/gemma-2-2b-it",
        "abacusai/dracarys-llama-3.1-70b-instruct",
        "upstage/solar-10.7b-instruct",
        "mistralai/mistral-nemotron",
        "meta/llama-4-maverick-17b-128e-instruct",
        "thinkingmachines/inkling",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "z-ai/glm-5.2",
        "qwen/qwen3-next-80b-a3b-instruct",
        "sarvamai/sarvam-m",
        "poolside/laguna-xs-2.1",
        "stepfun-ai/step-3.7-flash",
        "meta/llama-3.2-3b-instruct",
        "meta/llama-3.2-1b-instruct",
        "mistralai/mistral-small-4-119b-2603",
        "mistralai/mixtral-8x7b-instruct-v0.1",
        "nvidia/llama-3.3-nemotron-super-49b-v1",
        "nvidia/nemotron-3-super-120b-a12b",
        "nvidia/nemotron-3-nano-30b-a3b",
        "nvidia/nvidia-nemotron-nano-9b-v2",
        "nvidia/nemotron-nano-12b-v2-vl",
        "nvidia/llama-3.1-nemotron-nano-vl-8b-v1",
        "nvidia/riva-translate-4b-instruct-v1.1",
    ],
)
_add(
    "vision",
    [
        "meta/llama-3.2-90b-vision-instruct",
        "meta/llama-3.2-11b-vision-instruct",
        "google/paligemma",
        "microsoft/phi-4-multimodal-instruct",
        "nvidia/llama-3.1-nemotron-nano-vl-8b-v1",
        "nvidia/cosmos-reason2-8b",
        "nvidia/ising-calibration-1-35b-a3b",
        "nvidia/nemotron-3.5-content-safety",
        "meta/llama-guard-4-12b",
        "deepseek-ai/deepseek-v4-pro",
        "google/diffusiongemma-26b-a4b-it",
        "nvidia/ai-synthetic-video-detector",
    ],
)
_add(
    "embeddings",
    [
        "nvidia/nv-embedqa-e5-v5",
        "nvidia/nv-embedqa-mistral-7b-v2",
        "nvidia/nv-embedcode-7b-v1",
        "nvidia/llama-nemotron-embed-1b-v2",
        "nvidia/llama-nemotron-embed-vl-1b-v2",
        "baai/bge-m3",
        "intfloat/multilingual-e5-large-instruct",
        "nvidia/nv-embed-v1",
        "nvidia/nemotron-3-embed-1b",
        "nvidia/nemoretriever-parse",
    ],
)
_add(
    "rerank",
    [
        "nvidia/rerank-qa-mistral-4b",
        "nvidia/nemotron-rerank-1b-v2",
    ],
)
_add(
    "safety",
    [
        "nvidia/llama-3.1-nemoguard-8b-content-safety",
        "nvidia/llama-3.1-nemoguard-8b-topic-control",
        "nvidia/nemotron-3.5-content-safety",
        "nvidia/nemotron-content-safety-reasoning-4b",
        "nvidia/gliner-pii",
        "nvidia/nemojail-jailbreak-detect",
        "nvidia/llama-3.1-aegis-defense-v1.0",
        "nvidia/llama-3.1-nemotron-safety-guard-8b-v3",
    ],
)
_add(
    "biology",
    [
        "nvidia/esmfold",
        "nvidia/esm2-650m",
        "nvidia/msa-search",
        "nvidia/genmol",
        "nvidia/molmim",
        "nvidia/rfdiffusion",
        "nvidia/Boltz-2",
    ],
)
_add(
    "video",
    [
        "nvidia/cosmos3-nano",
        "nvidia/cosmos-transfer1-7b",
        "nvidia/cosmos-predict1-5b",
        "nvidia/cosmos-transfer2.5-2b",
        "nvidia/ai-synthetic-video-detector",
    ],
)
_add(
    "document",
    [
        "nvidia/nemoretriever-parse",
        "nvidia/nemotron-ocr-v1",
        "nvidia/nemotron-table-structure-v1",
        "nvidia/nemotron-page-elements-v3",
        "nvidia/nemotron-graphic-elements-v1",
        "nvidia/paddleocr",
        "google/deplot",
    ],
)
_add(
    "speech",
    [
        "nvidia/parakeet-ctc-1.1b-asr",
        "nvidia/parakeet-tdt-1.1b-asr",
        "nvidia/canary-1b-asr",
        "nvidia/magpie-tts-zeroshot",
        "nvidia/fastpitch-hifigan-tts",
    ],
)
_add(
    "audio",
    [
        "nvidia/noise-cancellation",
        "nvidia/studio-voice",
        "nvidia/active-speaker-detection",
    ],
)
_add("weather", ["nvidia/fourcastnet"])
_add("translation", ["nvidia/riva-translate-4b-instruct-v1.1"])

# Families we can actually probe with a simple request shape:
PROBEABLE = {"chat", "vision", "embeddings", "rerank", "safety", "translation"}
# For non-probeable families (biology/video/document/speech/audio/weather) we only
# record the family + note that deep probing needs a specialized payload.

TRANSIENT_PREFIX = (
    "CHAT_CONN",
    "CHAT_SERVER",
    "CHAT_WATCHDOG",
    "EMB_CONN",
    "EMB_SERVER",
    "EMB_WATCHDOG",
    "RERANK_CONN",
    "RERANK_SERVER",
    "RERANK_WATCHDOG",
)


def post(path, payload, timeout=20, retries=2):
    data = json.dumps(payload).encode()
    last = (-1, "", "other")
    for attempt in range(retries + 1):
        req = urllib.request.Request(
            f"{BASE}{path}", data=data, headers=HEADERS, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read().decode("utf-8", "replace"), "ok"
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            last = (e.code, body, "http")
            if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(1.5**attempt)
                continue
            return e.code, body, "http"
        except urllib.error.URLError as e:
            kind = (
                "timeout"
                if "timed out" in str(e.reason).lower()
                or "timeout" in str(e.reason).lower()
                else "other"
            )
            last = (-1, str(e), kind)
            if attempt < retries:
                time.sleep(1.5**attempt)
                continue
            return -1, str(e), kind
        except Exception as e:  # noqa: BLE001
            last = (-1, str(e), "other")
            if attempt < retries:
                time.sleep(1.5**attempt)
                continue
            return -1, str(e), "other"
    return last


def classify(status, kind, prefix):
    """prefix = 'CHAT' / 'EMB' / 'RERANK'. Returns '<PREFIX>_<STATE>'."""
    if status == 200:
        return f"{prefix}_OK"
    if status in (401, 403):
        return f"{prefix}_DENIED"
    if status == 404:
        return f"{prefix}_NOT_DEPLOYED"
    if status in (400, 422):
        return f"{prefix}_UNSUPPORTED"
    if status >= 500:
        return f"{prefix}_SERVER_ERR"
    if status == -1:
        return f"{prefix}_CONN_TIMEOUT" if kind == "timeout" else f"{prefix}_CONN_OTHER"
    return f"{prefix}_ERR_{status}"


def real_tool_calls(body):
    try:
        d = json.loads(body)
    except Exception:  # noqa: BLE001
        return False
    for ch in d.get("choices", []):
        tc = ch.get("message", {}).get("tool_calls")
        if isinstance(tc, list) and tc:
            return True
        dtc = ch.get("delta", {}).get("tool_calls")
        if isinstance(dtc, list) and dtc:
            return True
    return False


def real_reasoning(body):
    try:
        d = json.loads(body)
    except Exception:  # noqa: BLE001
        return False
    for ch in d.get("choices", []):
        rc = ch.get("message", {}).get("reasoning_content")
        if isinstance(rc, str) and rc.strip():
            return True
        drc = ch.get("delta", {}).get("reasoning_content")
        if isinstance(drc, str) and drc.strip():
            return True
    return False


def probe_model(mid):
    fam = FAMILY.get(mid, "chat")
    entry = {
        "id": mid,
        "family": fam,
        "state": None,
        "tools": None,
        "vision": None,
        "streaming": None,
        "reasoning": None,
        "ms": None,
        "notes": [],
    }

    # Non-probeable families: record family, mark as needs-special-payload.
    if fam not in PROBEABLE:
        entry["state"] = (
            f"{fam.upper()}_FAMILY"  # e.g. BIOLOGY_FAMILY (deployed, special endpoint)
        )
        entry["notes"].append(
            f"family={fam}; deep probe needs specialized payload (not chat/embed/rerank)"
        )
        return entry

    # Build the right request per family.
    if fam == "embeddings":
        path, payload = (
            "/embeddings",
            {"model": mid, "input": ["hello world"], "encoding_format": "float"},
        )
        prefix = "EMB"
    elif fam == "rerank":
        path, payload = (
            "/ranking",
            {"model": mid, "query": "hello", "passages": ["a", "b"]},
        )
        prefix = "RERANK"
    else:  # chat / vision / safety / translation all use chat/completions
        if fam == "vision":
            content = [
                {"type": "text", "text": "what is in this image?"},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{PNG_B64}"},
                },
            ]
        else:
            content = "hi"
        path = "/chat/completions"
        payload = {
            "model": mid,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": 5,
            "stream": False,
        }
        prefix = "CHAT"

    t0 = time.time()
    s, b, k = post(path, payload)
    entry["ms"] = int((time.time() - t0) * 1000)
    entry["state"] = classify(s, k, prefix)

    # For chat-family models, also probe capabilities (tools/vision/stream/reasoning).
    if fam == "chat" and entry["state"] == "CHAT_OK":
        # tools
        s, b, k = post(
            "/chat/completions",
            {
                "model": mid,
                "messages": [
                    {"role": "user", "content": "call the echo tool with x=1"}
                ],
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "echo",
                            "description": "echo",
                            "parameters": {
                                "type": "object",
                                "properties": {"x": {"type": "integer"}},
                                "required": ["x"],
                            },
                        },
                    }
                ],
                "tool_choice": "auto",
                "max_tokens": 30,
                "stream": False,
            },
        )
        entry["tools"] = (
            "TOOL_OK"
            if (s == 200 and real_tool_calls(b))
            else classify(s, k, "CHAT").replace("CHAT_", "TOOL_")
        )
        # vision
        s, b, k = post(
            "/chat/completions",
            {
                "model": mid,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "what color is this pixel?"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{PNG_B64}"
                                },
                            },
                        ],
                    }
                ],
                "max_tokens": 3,
                "stream": False,
            },
        )
        entry["vision"] = (
            "VISION_OK"
            if s == 200
            else classify(s, k, "CHAT").replace("CHAT_", "VISION_")
        )
        # streaming
        s, b, k = post(
            "/chat/completions",
            {
                "model": mid,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 3,
                "stream": True,
            },
        )
        entry["streaming"] = (
            "STREAM_OK"
            if (s == 200 and "data:" in b)
            else classify(s, k, "CHAT").replace("CHAT_", "STREAM_")
        )
        # reasoning
        s, b, k = post(
            "/chat/completions",
            {
                "model": mid,
                "messages": [{"role": "user", "content": "what is 1+1?"}],
                "max_tokens": 30,
                "reasoning_effort": "low",
                "stream": False,
            },
        )
        entry["reasoning"] = (
            "REASON_OK"
            if (s == 200 and real_reasoning(b))
            else classify(s, k, "CHAT").replace("CHAT_", "REASON_")
        )
    elif fam == "vision" and entry["state"] == "VISION_OK":
        entry["vision"] = "VISION_OK"
    return entry


# ---- load prior report for resume ----
done = {}
if os.path.exists(REPORT_PATH):
    try:
        for e in json.load(open(REPORT_PATH)):
            done[e["id"]] = e
    except Exception:  # noqa: BLE001
        done = {}

if PURGE:
    before = len(done)
    done = {
        i: e
        for i, e in done.items()
        if not e.get("state", "").startswith(TRANSIENT_PREFIX)
        and e.get("state", "")
        not in ("CHAT_WATCHDOG", "EMB_WATCHDOG", "RERANK_WATCHDOG")
    }
    print(f"PURGE: dropped {before - len(done)} transient entries", file=sys.stderr)

# ---- fetch model list ----
req = urllib.request.Request(
    f"{BASE}/models", headers={"Authorization": f"Bearer {KEY}"}
)
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        models = json.loads(r.read()).get("data", [])
except Exception as e:  # noqa: BLE001
    print(f"ERROR fetching /models: {e}", file=sys.stderr)
    sys.exit(1)

ids = [m.get("id") for m in models if m.get("id")]
if ONLY:
    ids = [i for i in ids if i in ONLY]
ids = [i for i in ids if i not in SKIP]
if MAX:
    ids = ids[:MAX]

todo = [i for i in ids if i not in done]
print(f"Probing {len(todo)} models ({len(done)} cached)...", file=sys.stderr)

report = list(done.values())
with ThreadPoolExecutor(max_workers=4) as ex:
    futures = {ex.submit(probe_model, mid): mid for mid in todo}
    for fut in futures:
        mid = futures[fut]
        try:
            entry = fut.result(timeout=MODEL_TIMEOUT)
        except FuturesTimeout:
            entry = {
                "id": mid,
                "family": FAMILY.get(mid, "chat"),
                "state": "CHAT_WATCHDOG",
                "tools": "TOOL_WATCHDOG",
                "vision": "VISION_WATCHDOG",
                "streaming": "STREAM_WATCHDOG",
                "reasoning": "REASON_WATCHDOG",
                "ms": None,
                "notes": [f"watchdog: exceeded {MODEL_TIMEOUT}s"],
            }
        report.append(entry)
        json.dump(report, open(REPORT_PATH, "w"), indent=2)

# ---- summaries ----
states = Counter(e["state"] for e in report)
usable = [
    e
    for e in report
    if e["state"]
    in ("CHAT_OK", "EMB_OK", "RERANK_OK", "VISION_OK", "SAFETY_OK", "TRANSLATION_OK")
]
families = Counter(e["family"] for e in report)

print(f"\n=== SUMMARY ===")
print(f"Total seen:      {len(report)}")
print(f"USABLE (OK):     {len(usable)}")
print("State breakdown:")
for st, n in sorted(states.items()):
    print(f"  {st:22s} {n}")
print("Family breakdown:")
for fam, n in sorted(families.items()):
    print(f"  {fam:14s} {n}")

md = [
    "# NVIDIA NIM — Model Capability Matrix (endpoint-family aware)",
    "",
    f"_Generated {time.strftime('%Y-%m-%d %H:%M')} · {len(usable)} usable of {len(report)} listed_",
    "",
    "| Model | Family | State | Tools | Vision | Stream | Reasoning | ms |",
    "|-------|--------|-------|-------|--------|--------|-----------|----|",
]
for e in sorted(
    report, key=lambda x: (not x["state"].endswith("_OK"), x["family"], x["id"])
):
    md.append(
        f"| `{e['id']}` | {e['family']} | {e['state']} | {e['tools']} | {e['vision']} | {e['streaming']} | {e['reasoning']} | {e.get('ms', '')} |"
    )
with open("nvidia_models_report.md", "w") as f:
    f.write("\n".join(md) + "\n")

print("\nWrote nvidia_models_report.json and nvidia_models_report.md")
print("\nUSABLE models:")
for e in sorted(usable, key=lambda x: x["id"]):
    extra = ""
    if e["family"] == "chat":
        extra = f" T={e['tools']} V={e['vision']} S={e['streaming']} R={e['reasoning']}"
    print(f"  {e['id']:42s} [{e['family']}] {e['state']}{extra}")
