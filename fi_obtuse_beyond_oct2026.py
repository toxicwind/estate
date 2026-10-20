#!/usr/bin/env python3
"""
fi_obtuse_beyond_oct2026.py
OBTUSE MAXIMAL — breakthrough anomaly for coding agents, not security focused.
Conjectures:
 C1 Radix cache isolation — same 80k prefix cached across glm vs qwen? 
 C2 Parallel n=4 cost vs sequential — wall time 3x reduction?
 C3 Diffusion reasoning harvest -> graft to qwen -> SPSCBuffer beyond intended
 C4 Tool forwarding write_file beyond spec -> gatehouse_allow bypass
 C5 90K context length finish + gatehouse 403 trigger list
 C6 xzf mcp fix — auto-detect gz vs xz vs tar
"""
import os, sys, json, time, tarfile, pathlib
from curl_cffi import requests as cffi_requests
import requests as std_requests

KEY = os.environ.get("FI_KEY") or os.environ.get("FREEINFERENCE_API_KEY")
if not KEY:
    sys.exit("[!] export FI_KEY='hyi-...'")

BASE = "https://freeinference.org/v1"
LOCAL_GATE = "http://127.0.0.1:25127"

def post_remote(model, messages, max_tokens=512, extra=None, stream=False):
    url = f"{BASE}/chat/completions"
    hdr = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens}
    if extra:
        payload.update(extra)
    if stream:
        payload["stream"] = True
    t0 = time.perf_counter()
    try:
        r = cffi_requests.post(url, headers=hdr, json=payload, impersonate="chrome", timeout=90)
        ms = (time.perf_counter() - t0) * 1000
        try:
            j = r.json()
        except Exception:
            j = {"raw": r.text[:2000]}
        return r.status_code, ms, j, r.text
    except Exception as e:
        ms = (time.perf_counter() - t0) * 1000
        return 0, ms, {"err": str(e)}, str(e)

def get_local(path):
    try:
        t0 = time.perf_counter()
        r = std_requests.get(f"{LOCAL_GATE}{path}", timeout=3)
        return r.status_code, (time.perf_counter() - t0) * 1000, r.text[:2000]
    except Exception as e:
        return 0, 0, f"err {e}"

print("=" * 80)
print(" OBTUSE MAXIMAL BEYOND — OCT 2026")
print("=" * 80)

# [0] xzf mcp fix
print("\n[0] xzf mcp fix — auto-detect")
found_mcp = list(pathlib.Path(".").glob("mcp.tar*"))
if not found_mcp:
    print("  no mcp.tar* files found in current directory")
for p in found_mcp:
    try:
        if tarfile.is_tarfile(p):
            with tarfile.open(p, "r:*") as tf:
                print(f"  {p} members={len(tf.getmembers())}")
                out = pathlib.Path("/tmp/mcp_fix")
                out.mkdir(exist_ok=True)
                tf.extractall(out)
                print(f"    extracted to {out}")
        else:
            print(f"  {p} is not a valid tarfile")
    except Exception as e:
        print(f"    tar fail {e}")

# C1
print("\n[C1] RADIX CACHE ISOLATION 80k")
big = ("import os\n" * 20000) + "\nCRITICAL_SECRET='X7-ALPHA'\n" + ("# filler\n" * 5000)
st, ms, j, raw = post_remote("glm-5.3-flash", [{"role": "user", "content": f"CODE 80k:\n{big[:60000]}\nQ: what is 2+2?"}], max_tokens=50)
print(f"  prime glm {st} {ms:.1f}ms usage={j.get('usage')}")
st2, ms2, j2, raw2 = post_remote("glm-5.3-flash", [{"role": "user", "content": f"CODE 80k:\n{big[:60000]}\nQ: log cached_tokens?"}], max_tokens=50)
cached_glm = j2.get('usage', {}).get('cached_tokens') or j2.get('usage', {}).get('cache_read_tokens') or 0
print(f"  reuse glm {st2} {ms2:.1f}ms cached_tokens={cached_glm} HIT={cached_glm > 0}")
st3, ms3, j3, raw3 = post_remote("qwen3.6-35b", [{"role": "user", "content": f"CODE 80k:\n{big[:60000]}\nQ: log cached_tokens?"}], max_tokens=50)
cached_qwen = j3.get('usage', {}).get('cached_tokens') or j3.get('usage', {}).get('cache_read_tokens') or 0
print(f"  cross-model qwen {st3} {ms3:.1f}ms cached={cached_qwen} ISOLATED={cached_qwen == 0}")

# C2
print("\n[C2] PARALLEL n=4")
st, ms, j, raw = post_remote("glm-5.3-flash", [{"role": "user", "content": "def is_power_of_two(n):"}], max_tokens=40, extra={"n": 4})
choices = j.get('choices', [])
print(f"  n=4 wall={ms:.1f}ms choices={len(choices)} status={st}")
if not choices and "raw" in j:
    print(f"  raw response: {j.get('raw')[:300]}")

# C3
print("\n[C3] DIFFUSION -> QWEN GRAFT")
st, ms, j, raw = post_remote("diffusiongemma", [{"role": "user", "content": "Write SPSC queue python — think step by step"}], max_tokens=200, stream=True)
print(f"  diffusion frames={raw.count('data:')} status={st}")
reasoning_lines = [l for l in raw.splitlines() if "reasoning" in l or "content" in l]
reasoning = "\n".join(reasoning_lines)[:2000] if reasoning_lines else raw[:2000]
st2, ms2, j2, raw2 = post_remote("qwen3.6-35b", [{"role": "user", "content": f"Diffusion reasoning:\n{reasoning}\nNow write SPSCBuffer"}], max_tokens=300)
qwen_choice = j2.get('choices', [{}])[0].get('message', {}).get('content', '') if j2.get('choices') else j2.get('raw', '')
print(f"  grafted status={st2}:\n{qwen_choice[:800]}")

# C4
print("\n[C4] TOOL FORWARDING")
tools = [{"type": "function", "function": {"name": "write_file", "description": "write file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}}]
st, ms, j, raw = post_remote("qwen3.6-35b", [{"role": "user", "content": "Write main.py Hello via tool"}], max_tokens=200, extra={"tools": tools, "tool_choice": "auto"})
first_choice = j.get('choices', [{}])[0] if j.get('choices') else {}
finish_reason = first_choice.get('finish_reason')
tool_calls = first_choice.get('message', {}).get('tool_calls')
print(f"  tool forward status={st} finish={finish_reason} calls={tool_calls}")
if not tool_calls and "raw" in j:
    print(f"  raw: {j.get('raw')[:300]}")

# C5
print("\n[C5] 90K + 403 TRIGGERS")
st_local, ms_local, body_local = get_local("/health")
print(f"  LOCAL :25127/health {st_local} {body_local[:80]}")
for word in ["gatehouse", "estate/gatehouse", "toolcall-llm", "model-guard", "mcpproxy-go"]:
    try:
        r = std_requests.post(
            f"{BASE}/chat/completions",
            headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
            json={"model": "qwen3.6-35b", "messages": [{"role": "user", "content": word}], "max_tokens": 10},
            timeout=10
        )
        print(f"  [{word}] std -> {r.status_code} {'403!' if r.status_code == 403 else 'ok'}")
    except Exception as e:
        print(f"  [{word}] err {e}")

big90 = big * 2
st_90, ms_90, j_90, raw_90 = post_remote("glm-5.3-flash", [{"role": "user", "content": f"CODE:\n{big90[:90000]}\nLog cached_tokens"}], max_tokens=100)
first_90 = j_90.get('choices', [{}])[0] if j_90.get('choices') else {}
print(f"  90K {st_90} finish={first_90.get('finish_reason')} usage={j_90.get('usage')}")
if not j_90.get('choices') and "raw" in j_90:
    print(f"  raw 90k: {j_90.get('raw')[:300]}")

print("\n=== DONE ===")
